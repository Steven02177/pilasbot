# -*- coding: utf-8 -*-
"""
Procesamiento de mensajes y generación de respuestas de PilasBot.

Recibe un mensaje en lenguaje natural + el estado conversacional y devuelve
la respuesta junto con el estado actualizado y las respuestas rápidas sugeridas.

Flujo general (documento UDES):
  INICIO -> SELECCION_ESCENARIO -> PREGUNTA_ESCENARIO -> ANALISIS ->
  RECOMENDACION_PREVENTIVA | RECOMENDACION_URGENTE -> CONSULTA_OTRA_SITUACION -> FIN
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

import scenarios as sc
from conversation_manager import (
    AWAIT_CLARIFY_CLICK,
    AWAIT_COMPLIANCE,
    AWAIT_GENERIC_COMPLIANCE,
    AWAIT_GENERIC_DESCRIBE,
    AWAIT_SCENARIO_QUESTION,
    ConversationState,
    States,
    new_state,
)
from risk_analyzer import (
    CLICK_RE,
    contains_sensitive_info,
    detect_delivery,
    detect_intent,
    detect_signals,
    is_affirmative,
    is_negative,
    is_out_of_context,
    labels_for,
    normalize,
)

# ---------------------------------------------------------------------------
# Resultado del procesamiento
# ---------------------------------------------------------------------------


@dataclass
class BotReply:
    """Respuesta generada por el chatbot."""

    text: str
    state: ConversationState
    quick_replies: List[str] = field(default_factory=list)
    restart: bool = False  # True cuando el usuario pidió reiniciar


# ---------------------------------------------------------------------------
# Textos de apoyo
# ---------------------------------------------------------------------------

RESTART_REPLY = (
    "🧹 Conversación reiniciada.\n\n" + sc.GREETING + "\n\n" + sc.MENU_INTRO
)

MENU_COMMAND_REPLY = "👌 Volvamos al menú principal.\n\n" + sc.MENU_INTRO

FIN_REPLY = (
    "¡Listo! Recuerda: **no compartas claves, códigos ni números de tarjeta**, "
    "verifica siempre por canales oficiales y confirma las solicitudes de dinero "
    "con una llamada.\n\n"
    "Si más adelante surge otra situación, escribe **\"menú\"** o elige una opción "
    "para volver a empezar. ¡Pilas! 🛡️"
)

PROTECTION_REPLY = sc.PROTECTION_TIPS_INTRO + "\n\n" + "\n".join(
    f"{i}. {tip}" for i, tip in enumerate(sc.PROTECTION_TIPS, start=1)
)

PILAS_ALERT = "¡Pilas! Detecté una señal de alerta en lo que me cuentas: **{signal}**."

EXAMPLE_DESCRIPTIONS = [
    "Me piden dinero por WhatsApp",
    "Recibí un enlace sospechoso",
    "Me ofrecen un trabajo demasiado bueno",
]

# Alias local: la detección de entregas vive en risk_analyzer
_detect_delivery = detect_delivery

# Etiqueta del menú -> clave de escenario (botones de la interfaz)
MENU_LABEL_TO_KEY = {
    normalize(opt): key
    for key, opt in zip(("banco", "empleo", "familia", "otra"), sc.MENU_OPTIONS)
}


# ---------------------------------------------------------------------------
# Constructores de mensaje
# ---------------------------------------------------------------------------


def menu_text() -> str:
    lines = [f"**{i}.** {opt}" for i, opt in enumerate(sc.MENU_OPTIONS, start=1)]
    return sc.MENU_INTRO + "\n\n" + "\n".join(lines)


def menu_replies() -> List[str]:
    return list(sc.MENU_OPTIONS)


def _bullets(items: List[str], numbered: bool = False) -> str:
    out = []
    for i, item in enumerate(items, start=1):
        prefix = f"{i}. " if numbered else "• "
        out.append(f"{prefix}{item}")
    return "\n".join(out)


def build_recommendations(state: ConversationState, urgent: bool) -> str:
    """Arma el bloque de recomendación (preventiva o urgente) + señales."""
    parts: List[str] = []
    parts.append(sc.URGENT_HEADER if urgent else sc.PREVENTIVE_HEADER)

    if state.signals:
        parts.append(sc.SIGNALS_HEADER + "\n" + _bullets(labels_for(state.signals)))
    else:
        parts.append(sc.NO_SIGNALS_TEXT)

    if state.scenario == "banco":
        recs = sc.SCENARIOS["banco"]["urgent"] if urgent else sc.SCENARIOS["banco"]["preventive"]
    elif state.scenario == "empleo":
        recs = sc.SCENARIOS["empleo"]["urgent"] if urgent else sc.SCENARIOS["empleo"]["preventive"]
    elif state.scenario == "familia":
        recs = sc.SCENARIOS["familia"]["urgent"] if urgent else sc.SCENARIOS["familia"]["preventive"]
    else:
        recs = sc.GENERIC_URGENT if urgent else sc.GENERIC_PREVENTIVE

    parts.append("**Qué hacer ahora:**\n" + _bullets(recs, numbered=True))
    parts.append(sc.ORIENTATION_NOTICE)
    parts.append(sc.ASK_ANOTHER)
    return "\n\n".join(parts)


def _current_question(state: ConversationState) -> str:
    """Pregunta activa según el estado (para repetirla si hace falta)."""
    if state.status == States.PREGUNTA_ESCENARIO and state.scenario in sc.SCENARIOS:
        sdef = sc.SCENARIOS[state.scenario]
        if state.awaiting == AWAIT_CLARIFY_CLICK or state.awaiting == AWAIT_COMPLIANCE:
            return sdef["decision_question"]
        idx = min(state.question_index, len(sdef["questions"]) - 1)
        return sdef["questions"][idx]
    if state.status == States.CONSULTA_OTRA_SITUACION:
        if state.awaiting == AWAIT_GENERIC_COMPLIANCE:
            return sc.OTHER_SCENARIO["question"]
        return sc.OTHER_SCENARIO["intro"]
    return menu_text()


def current_quick_replies(state: ConversationState) -> List[str]:
    """Respuestas rápidas coherentes con el estado actual."""
    if state.status in (States.INICIO, States.SELECCION_ESCENARIO, States.FIN):
        return menu_replies()

    if state.status == States.PREGUNTA_ESCENARIO and state.scenario in sc.SCENARIOS:
        sdef = sc.SCENARIOS[state.scenario]
        if state.awaiting in (AWAIT_CLARIFY_CLICK, AWAIT_COMPLIANCE):
            return list(sdef["decision_replies"])
        idx = min(state.question_index, len(sdef["quick_replies"]) - 1)
        return list(sdef["quick_replies"][idx])

    if state.status in (States.RECOMENDACION_PREVENTIVA, States.RECOMENDACION_URGENTE):
        return list(sc.ASK_ANOTHER_REPLIES)

    if state.status == States.CONSULTA_OTRA_SITUACION:
        if state.awaiting == AWAIT_GENERIC_COMPLIANCE:
            return list(sc.OTHER_SCENARIO["replies"])
        return list(EXAMPLE_DESCRIPTIONS)

    return menu_replies()


# ---------------------------------------------------------------------------
# Arranque de escenarios
# ---------------------------------------------------------------------------


def start_scenario(
    key: str,
    state: ConversationState,
    message: str = "",
    from_button: bool = False,
) -> BotReply:
    """Inicializa un escenario y formula su primera pregunta."""
    sdef = sc.SCENARIOS[key]
    st = state.update(
        status=States.PREGUNTA_ESCENARIO,
        scenario=key,
        question_index=0,
        awaiting=AWAIT_SCENARIO_QUESTION,
        answers=[],
        generic_attempts=0,
    )
    st = st.add_signals(detect_signals(message))
    st = st.recompute_risk()

    # Si el usuario YA confirmó una entrega, se activa el modo urgente de una vez
    entrego, envio, codigo, clic = _detect_delivery(message)
    if entrego or envio or codigo:
        st = st.register_compromise(data=entrego, money=envio, code=codigo)
        st = st.recompute_risk()
        blocks = []
        if not from_button:
            blocks.append(sc.ACK_WITH_SIGNALS if st.signals else sc.ACK_NEUTRAL)
        blocks.append(sdef["intro"])
        if st.signals:
            blocks.append(sc.SIGNALS_HEADER + "\n" + _bullets(labels_for(st.signals)))
        blocks.append(build_recommendations(st, urgent=True))
        st = st.update(status=States.RECOMENDACION_URGENTE, awaiting="")
        return BotReply(
            text="\n\n".join(blocks),
            state=st,
            quick_replies=current_quick_replies(st),
        )

    blocks: List[str] = []
    if not from_button:
        blocks.append(sc.ACK_WITH_SIGNALS if st.signals else sc.ACK_NEUTRAL)
    blocks.append(sdef["intro"])
    if st.signals:
        blocks.append(sc.SIGNALS_HEADER + "\n" + _bullets(labels_for(st.signals)))
    blocks.append(sdef["questions"][0])

    return BotReply(
        text="\n\n".join(blocks),
        state=st,
        quick_replies=current_quick_replies(st),
    )


def show_menu(state: ConversationState, keep_risk: bool = True) -> ConversationState:
    """Vuelve al menú principal conservando (o no) el riesgo acumulado."""
    if keep_risk:
        return state.update(
            status=States.SELECCION_ESCENARIO,
            scenario=None,
            question_index=0,
            awaiting="",
            answers=[],
        )
    return state.update(
        status=States.SELECCION_ESCENARIO,
        scenario=None,
        question_index=0,
        awaiting="",
        answers=[],
        risk_level="RIESGO BAJO",
        signals=[],
        delivered_data=False,
        delivered_money=False,
        shared_code=False,
        clicked_link=False,
    )


# ---------------------------------------------------------------------------
# Fase: menú / inicio
# ---------------------------------------------------------------------------

_RESTART_RE = re.compile(
    r"(reiniciar|reinicia|reiniciemos|empezar de nuevo|empezar otra vez|"
    r"empezar desde cero|nueva conversacion|borrar conversacion|limpiar|"
    r"reset|start over|desde cero)"
)
_MENU_RE = re.compile(r"(^menu$|^menu principal$|volver al menu|ir al menu|opciones|el menu)")
_NUMBER_OPTION_RE = re.compile(r"^([1-4])$")


def _handle_menu_phase(raw: str, state: ConversationState) -> BotReply:
    msg = normalize(raw)

    # Opción numérica (1-4)
    num = _NUMBER_OPTION_RE.match(msg)
    if num:
        raw = sc.MENU_OPTIONS[int(num.group(1)) - 1]
        msg = normalize(raw)

    intent = detect_intent(raw)
    from_button = msg in {normalize(o) for o in sc.MENU_OPTIONS}

    # ---- Límites y alcance del bot (intenciones meta) ----
    if intent == "identidad":
        st = show_menu(state)
        return BotReply(
            text=sc.IDENTITY_REPLY + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent == "limite":
        st = show_menu(state)
        return BotReply(
            text=sc.LIMIT_REPLY + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent == "solicitud_imposible":
        st = show_menu(state)
        return BotReply(
            text=sc.IMPOSSIBLE_REQUEST_REPLY + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent in sc.SCENARIOS:
        return start_scenario(intent, state, message=raw, from_button=from_button)

    if intent == "otra":
        if from_button:
            st = state.update(
                status=States.CONSULTA_OTRA_SITUACION,
                scenario="otra",
                question_index=0,
                awaiting=AWAIT_GENERIC_DESCRIBE,
                answers=[],
                generic_attempts=0,
            )
            return BotReply(
                text=sc.OTHER_SCENARIO["intro"],
                state=st,
                quick_replies=current_quick_replies(st),
            )
        # Descripción libre desde el inicio
        return _analyze_generic(raw, state.update(scenario="otra"))

    if intent == "proteger":
        st = show_menu(state).update(status=States.SELECCION_ESCENARIO)
        return BotReply(
            text=PROTECTION_REPLY + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent == "saludo":
        st = show_menu(state)
        return BotReply(
            text=sc.GREETING + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent == "agradecer":
        st = show_menu(state)
        return BotReply(
            text="¡De nada! Para eso estoy. 🛡️\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if intent == "despedida":
        st = show_menu(state)
        return BotReply(
            text=sc.FAREWELL_REPLY,
            state=st,
            quick_replies=menu_replies(),
        )

    if is_out_of_context(raw):
        st = show_menu(state)
        return BotReply(
            text=sc.OUT_OF_CONTEXT + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    # Entrega ya confirmada sin escenario claro -> modo urgente (escenario 4)
    entrego, envio, codigo, _clic = detect_delivery(raw)
    if entrego or envio or codigo:
        return _analyze_generic(raw, state.update(scenario="otra"))

    # Sin intención reconocible
    st = show_menu(state)
    return BotReply(
        text=sc.UNKNOWN_INTENT_REPLY + "\n\n" + menu_text(),
        state=st,
        quick_replies=menu_replies(),
    )


# ---------------------------------------------------------------------------
# Fase: preguntas del escenario
# ---------------------------------------------------------------------------


def _finish_scenario(state: ConversationState, urgent: bool) -> BotReply:
    status = (
        States.RECOMENDACION_URGENTE if urgent else States.RECOMENDACION_PREVENTIVA
    )
    st = state.update(status=status, awaiting="")
    return BotReply(
        text=build_recommendations(st, urgent=urgent),
        state=st,
        quick_replies=current_quick_replies(st),
    )


def _next_question(state: ConversationState, idx: int) -> BotReply:
    sdef = sc.SCENARIOS[state.scenario]
    st = state.update(question_index=idx, awaiting=AWAIT_SCENARIO_QUESTION)
    return BotReply(
        text=sdef["questions"][idx],
        state=st,
        quick_replies=current_quick_replies(st),
    )


def _handle_scenario_phase(raw: str, state: ConversationState) -> BotReply:
    sdef = sc.SCENARIOS[state.scenario]
    msg = normalize(raw)

    # Comandos de menú / reinicio / saludo / protección se atienden primero
    if _MENU_RE.search(msg):
        st = show_menu(state)
        return BotReply(MENU_COMMAND_REPLY + "\n\n" + menu_text(), st, menu_replies())

    intent = detect_intent(raw)
    if intent == "proteger":
        return BotReply(
            text=PROTECTION_REPLY + "\n\n➡️ " + _current_question(state),
            state=state,
            quick_replies=current_quick_replies(state),
        )
    if intent == "saludo" and len(msg.split()) <= 4:
        return BotReply(
            text="¡Hola! " + _current_question(state),
            state=state,
            quick_replies=current_quick_replies(state),
        )

    # Límites y alcance: se responde sin perder la pregunta activa
    if intent in ("identidad", "limite", "solicitud_imposible"):
        text = {
            "identidad": sc.IDENTITY_REPLY,
            "limite": sc.LIMIT_REPLY,
            "solicitud_imposible": sc.IMPOSSIBLE_REQUEST_REPLY,
        }[intent]
        return BotReply(
            text=text + "\n\n➡️ " + _current_question(state),
            state=state,
            quick_replies=current_quick_replies(state),
        )

    # Compromiso confirmado en cualquier momento -> modo urgente
    entrego, envio, codigo, clic = _detect_delivery(raw)
    if entrego or envio or codigo:
        st = state.register_compromise(data=entrego, money=envio, code=codigo)
        st = st.add_signals(detect_signals(raw))
        st = st.recompute_risk()
        return _finish_scenario(st, urgent=True)

    # Respuesta a la pregunta activa
    answer = "[información sensible omitida]" if contains_sensitive_info(raw) else raw
    st = state.add_signals(detect_signals(raw))

    # ---- Sub-fase: aclaración "¿solo clic o entregaste datos?" (banco) ----
    if st.awaiting == AWAIT_CLARIFY_CLICK:
        st = st.update(answers=st.answers + [answer])
        data_words = re.search(
            r"\b(clave|claves|datos|tarjeta|contrasena|password|credenciales|cuenta)\b",
            msg,
        )
        if entrego or (data_words and not is_negative(raw)):
            st = st.register_compromise(data=True)
            return _finish_scenario(st, urgent=True)
        if CLICK_RE.search(raw) or re.search(r"\bsolo abri\b", msg):
            st = st.register_compromise(clicked=True)
            return _finish_scenario(st, urgent=True)
        if is_negative(raw):
            # Confirmó el clic pero niega haber entregado datos
            st = st.recompute_risk()
            return _finish_scenario(st, urgent=False)
        # Respuesta ambigua: se repite la aclaración
        return BotReply(
            text="Para orientarte bien necesito saberlo con claridad:\n\n"
            + sdef["decision_question"],
            state=st,
            quick_replies=list(sdef["decision_replies"]),
        )

    # ---- Sub-fase: pregunta de decisión (¿ya entregó algo?) ----
    if st.awaiting == AWAIT_COMPLIANCE:
        st = st.update(answers=st.answers + [answer])
        if is_affirmative(raw):
            st = st.register_compromise(money=envio or not codigo, code=codigo)
            return _finish_scenario(st, urgent=True)
        if is_negative(raw):
            st = st.recompute_risk()
            return _finish_scenario(st, urgent=False)
        return BotReply(
            text="No quedó claro para mí. " + sdef["decision_question"],
            state=st,
            quick_replies=list(sdef["decision_replies"]),
        )

    # ---- Pregunta normal del escenario ----
    idx = st.question_index
    st = st.update(answers=st.answers + [answer])
    new_signals = detect_signals(raw)
    pilas_line = ""
    if new_signals:
        pilas_line = PILAS_ALERT.format(signal=labels_for(new_signals)[0])

    # Refuerzos según la pregunta concreta (respuestas sí/no cortas)
    if st.scenario == "empleo" and idx == 1 and is_affirmative(raw):
        st = st.add_signal("pago_adelantado")
    elif st.scenario == "familia" and idx == 0 and is_affirmative(raw):
        st = st.add_signal("numero_nuevo")
    elif st.scenario == "familia" and idx == 1 and is_affirmative(raw):
        st = st.add_signal(
            "codigo_whatsapp" if "codigo" in msg else "emergencia_familiar"
        )
    elif st.scenario == "familia" and idx == 2 and is_negative(raw):
        st = st.add_signal("niega_llamada")
    elif st.scenario == "empleo" and idx == 2 and is_negative(raw):
        st = st.add_signal("perfil_nuevo")
    elif st.scenario == "banco" and idx == 0 and re.search(
        r"(numero|desconocido|no reconozco|no se quien)", msg
    ):
        st = st.add_signal("remitente_desconocido")

    st = st.recompute_risk()

    # Banco: la pregunta 3 es la de decisión (¿clic o datos?)
    if st.scenario == "banco" and idx == 2:
        if entrego or re.search(
            r"\b(entregu\w*|d[ií]\s+(mi|la|el)\s+clave|comparti\w*|ingres\w*\s+\w*clave|"
            r"met[ií]\s+\w*clave|ca[ií]\s+en)\b",
            msg,
        ):
            st = st.register_compromise(data=True)
            return _finish_scenario(st, urgent=True)
        if clic or is_affirmative(raw):
            # Respondió que sí: falta saber si solo abrió o entregó datos
            st = st.update(awaiting=AWAIT_CLARIFY_CLICK, clicked_link=True)
            preamble = (pilas_line + "\n\n") if pilas_line else ""
            return BotReply(
                text=preamble + sdef["decision_question"],
                state=st,
                quick_replies=list(sdef["decision_replies"]),
            )
        if is_negative(raw):
            return _finish_scenario(st, urgent=False)
        # Respuesta ambigua: se aclara antes de recomendar
        st = st.update(awaiting=AWAIT_CLARIFY_CLICK)
        return BotReply(
            text=sdef["decision_question"],
            state=st,
            quick_replies=list(sdef["decision_replies"]),
        )

    # Empleo / familia: después de la 3ª pregunta viene la pregunta de decisión
    if st.scenario in ("empleo", "familia") and idx == 2 and st.awaiting == AWAIT_SCENARIO_QUESTION:
        st = st.update(awaiting=AWAIT_COMPLIANCE)
        preamble = (pilas_line + "\n\n") if pilas_line else ""
        return BotReply(
            text=preamble + sdef["decision_question"],
            state=st,
            quick_replies=list(sdef["decision_replies"]),
        )

    # ¿Quedan preguntas?
    if idx + 1 < len(sdef["questions"]):
        nxt = _next_question(st, idx + 1)
        if pilas_line:
            nxt = BotReply(
                text=pilas_line + "\n\n" + nxt.text,
                state=nxt.state,
                quick_replies=nxt.quick_replies,
            )
        return nxt

    # No debería llegar aquí (la decisión se resuelve antes), pero por seguridad
    st = st.update(awaiting=AWAIT_COMPLIANCE)
    return BotReply(
        text=sdef["decision_question"],
        state=st,
        quick_replies=list(sdef["decision_replies"]),
    )


# ---------------------------------------------------------------------------
# Fase: recomendación mostrada (espera "otra situación")
# ---------------------------------------------------------------------------


def _handle_recommendation_phase(raw: str, state: ConversationState) -> BotReply:
    msg = normalize(raw)

    if _MENU_RE.search(msg):
        st = show_menu(state)
        return BotReply(MENU_COMMAND_REPLY + "\n\n" + menu_text(), st, menu_replies())

    intent = detect_intent(raw)

    # ---- Límites y alcance del bot (intenciones meta) ----
    if intent in ("identidad", "limite", "solicitud_imposible"):
        text = {
            "identidad": sc.IDENTITY_REPLY,
            "limite": sc.LIMIT_REPLY,
            "solicitud_imposible": sc.IMPOSSIBLE_REQUEST_REPLY,
        }[intent]
        return BotReply(
            text=text + "\n\n" + menu_text(),
            state=show_menu(state),
            quick_replies=menu_replies(),
        )

    if intent in sc.SCENARIOS:
        return start_scenario(intent, state, message=raw)

    if intent == "proteger":
        return BotReply(
            text=PROTECTION_REPLY + "\n\n" + menu_text(),
            state=show_menu(state),
            quick_replies=menu_replies(),
        )

    if intent == "despedida":
        return BotReply(
            text=sc.FAREWELL_REPLY,
            state=show_menu(state),
            quick_replies=menu_replies(),
        )

    if intent == "otra" or "otra situacion" in msg or "otra cosa" in msg:
        st = state.update(
            status=States.CONSULTA_OTRA_SITUACION,
            scenario="otra",
            question_index=0,
            awaiting=AWAIT_GENERIC_DESCRIBE,
            answers=[],
            generic_attempts=0,
        )
        return BotReply(
            text=sc.OTHER_SCENARIO["intro"],
            state=st,
            quick_replies=current_quick_replies(st),
        )

    # Respuesta a "¿Quieres consultar otra situación?"
    if re.search(r"\b(no|gracias|nada|con eso basta|ya esta)\b", msg) and not re.search(
        r"\b(si|quiero|otra)\b", msg
    ):
        st = state.update(status=States.FIN, scenario=None, awaiting="")
        return BotReply(
            text=FIN_REPLY,
            state=st,
            quick_replies=menu_replies(),
        )

    if re.search(r"\b(si|quiero|otra|siempre|vamos)\b", msg) or intent == "saludo":
        st = show_menu(state)
        if intent == "saludo":
            return BotReply(
                text=sc.GREETING + "\n\n" + menu_text(),
                state=st,
                quick_replies=menu_replies(),
            )
        return BotReply(
            text="¡Perfecto! " + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    if is_out_of_context(raw):
        st = show_menu(state)
        return BotReply(
            text=sc.OUT_OF_CONTEXT + "\n\n" + menu_text(),
            state=st,
            quick_replies=menu_replies(),
        )

    st = show_menu(state)
    return BotReply(
        text=menu_text(),
        state=st,
        quick_replies=menu_replies(),
    )


# ---------------------------------------------------------------------------
# Fase: otra situación sospechosa (escenario 4)
# ---------------------------------------------------------------------------


def _analyze_generic(raw: str, state: ConversationState) -> BotReply:
    """Analiza la descripción libre y pregunta por entregas."""
    signals = detect_signals(raw)
    st = state.add_signals(signals)
    st = st.recompute_risk()

    intent = detect_intent(raw)
    scam_context = intent is not None or bool(signals) or not is_out_of_context(raw)

    if not scam_context:
        st = st.update(generic_attempts=st.generic_attempts + 1)
        if st.generic_attempts >= 2:
            menu_st = show_menu(st)
            return BotReply(
                text=sc.OUT_OF_CONTEXT + "\n\n" + menu_text(),
                state=menu_st,
                quick_replies=menu_replies(),
            )
        return BotReply(
            text=sc.UNKNOWN_INTENT_REPLY,
            state=st,
            quick_replies=current_quick_replies(st),
        )

    # Compromiso confirmado de una vez -> urgente
    entrego, envio, codigo, clic = _detect_delivery(raw)
    if entrego or envio or codigo:
        st = st.register_compromise(data=entrego, money=envio, code=codigo)
        return _finish_scenario(st, urgent=True)

    st = st.update(status=States.CONSULTA_OTRA_SITUACION, awaiting=AWAIT_GENERIC_COMPLIANCE)
    ack = sc.ACK_WITH_SIGNALS if st.signals else sc.ACK_NEUTRAL
    blocks = [ack]
    if st.signals:
        blocks.append(sc.SIGNALS_HEADER + "\n" + _bullets(labels_for(st.signals)))
    if clic:
        blocks.append(
            "Como ya hiciste clic en el enlace, vamos a asumir que pudo quedar "
            "expuesta tu información y lo revisamos con cuidado."
        )
        st = st.register_compromise(clicked=True)
    blocks.append(sc.OTHER_SCENARIO["question"])

    return BotReply(
        text="\n\n".join(blocks),
        state=st,
        quick_replies=current_quick_replies(st),
    )


def _handle_generic_phase(raw: str, state: ConversationState) -> BotReply:
    msg = normalize(raw)

    if _MENU_RE.search(msg):
        st = show_menu(state)
        return BotReply(MENU_COMMAND_REPLY + "\n\n" + menu_text(), st, menu_replies())

    # Nota: mientras el usuario está en el escenario 4 (descripción o respuesta),
    # NO se cambia automáticamente de escenario: se analiza lo que cuenta.
    # Para cambiar de tema se usan los botones del menú o el comando "menú".

    if intent := detect_intent(raw):
        if intent == "proteger":
            return BotReply(
                text=PROTECTION_REPLY + "\n\n➡️ " + _current_question(state),
                state=state,
                quick_replies=current_quick_replies(state),
            )
        if intent == "saludo" and len(msg.split()) <= 4:
            return BotReply(
                text="¡Hola! " + _current_question(state),
                state=state,
                quick_replies=current_quick_replies(state),
            )
        if intent in ("identidad", "limite", "solicitud_imposible"):
            text = {
                "identidad": sc.IDENTITY_REPLY,
                "limite": sc.LIMIT_REPLY,
                "solicitud_imposible": sc.IMPOSSIBLE_REQUEST_REPLY,
            }[intent]
            return BotReply(
                text=text + "\n\n➡️ " + _current_question(state),
                state=state,
                quick_replies=current_quick_replies(state),
            )

    # El usuario describe algo más mientras espera la pregunta de entrega
    if state.awaiting == AWAIT_GENERIC_DESCRIBE:
        return _analyze_generic(raw, state)

    # Fase de cumplimiento: ¿entregó dinero, claves o códigos?
    entrego, envio, codigo, clic = _detect_delivery(raw)
    if entrego or envio or codigo:
        st = state.register_compromise(data=entrego, money=envio, code=codigo)
        st = st.add_signals(detect_signals(raw)).recompute_risk()
        return _finish_scenario(st, urgent=True)

    if is_affirmative(raw):
        # Afirmó sin precisar: se asume la opción más riesgosa de la pregunta
        mentions_secret = bool(
            re.search(r"\b(clave|codigo|contrasena|tarjeta|datos)\b", msg)
        )
        st = state.register_compromise(data=mentions_secret, money=not mentions_secret)
        st = st.add_signals(detect_signals(raw)).recompute_risk()
        return _finish_scenario(st, urgent=True)

    if is_negative(raw):
        st = state.add_signals(detect_signals(raw)).recompute_risk()
        return _finish_scenario(st, urgent=False)

    # Respuesta confusa: se repite la pregunta con más contexto
    return BotReply(
        text=(
            "No quedó claro para mí y no quiero inventar nada. "
            + sc.OTHER_SCENARIO["question"]
        ),
        state=state,
        quick_replies=list(sc.OTHER_SCENARIO["replies"]),
    )


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------


def process_message(message: str, state: Optional[ConversationState] = None) -> BotReply:
    """
    Procesa un mensaje del usuario contra la máquina de estados.

    Args:
        message: texto escrito por el usuario (o etiqueta de botón).
        state: estado actual; si es None se crea un estado nuevo.

    Returns:
        BotReply con la respuesta, el estado actualizado y las respuestas rápidas.
    """
    if state is None:
        state = new_state()

    raw = (message or "").strip()
    if not raw:
        return BotReply(
            text="",
            state=state,
            quick_replies=current_quick_replies(state),
        )

    msg = normalize(raw)

    # ---- Reinicio total ----
    if _RESTART_RE.search(msg):
        fresh = new_state()
        return BotReply(
            text=RESTART_REPLY,
            state=fresh,
            quick_replies=menu_replies(),
            restart=True,
        )

    # ---- Botones del menú: cambian de escenario desde cualquier estado ----
    if state.status not in (
        States.INICIO,
        States.SELECCION_ESCENARIO,
        States.FIN,
    ):
        label_key = MENU_LABEL_TO_KEY.get(msg)
        if label_key == "otra":
            st = state.update(
                status=States.CONSULTA_OTRA_SITUACION,
                scenario="otra",
                question_index=0,
                awaiting=AWAIT_GENERIC_DESCRIBE,
                answers=[],
                generic_attempts=0,
            )
            return BotReply(
                text=sc.OTHER_SCENARIO["intro"],
                state=st,
                quick_replies=current_quick_replies(st),
            )
        if label_key:
            return start_scenario(label_key, state, from_button=True)

    # ---- Volver al menú ----
    if _MENU_RE.search(msg) and state.status not in (
        States.INICIO,
        States.SELECCION_ESCENARIO,
        States.FIN,
    ):
        st = show_menu(state)
        return BotReply(MENU_COMMAND_REPLY + "\n\n" + menu_text(), st, menu_replies())

    # ---- Aviso de información sensible (siempre, sin guardar el valor) ----
    warn = ""
    if contains_sensitive_info(raw):
        warn = sc.SENSITIVE_INFO_WARNING + "\n\n"

    # ---- Despacho por estado ----
    if state.status in (States.INICIO, States.SELECCION_ESCENARIO, States.FIN):
        reply = _handle_menu_phase(raw, state)
    elif state.status == States.PREGUNTA_ESCENARIO:
        reply = _handle_scenario_phase(raw, state)
    elif state.status in (
        States.RECOMENDACION_PREVENTIVA,
        States.RECOMENDACION_URGENTE,
    ):
        reply = _handle_recommendation_phase(raw, state)
    elif state.status == States.CONSULTA_OTRA_SITUACION:
        reply = _handle_generic_phase(raw, state)
    else:
        reply = _handle_menu_phase(raw, state)

    if warn and reply.text:
        reply = BotReply(
            text=warn + reply.text,
            state=reply.state,
            quick_replies=reply.quick_replies,
            restart=reply.restart,
        )

    reply.state = reply.state.update(started=True)
    return reply
