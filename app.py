# -*- coding: utf-8 -*-
"""
PilasBot — Aplicación web (Gradio Blocks).

Interfaz del chatbot de orientación en ciberseguridad.
Ejecutar con:  python app.py
"""

from __future__ import annotations

import base64
import pathlib
from functools import partial
from typing import List

import gradio as gr

import scenarios as sc
from chatbot import current_quick_replies, process_message
from conversation_manager import ConversationState, initial_history, new_state
from risk_analyzer import risk_css_class

# ---------------------------------------------------------------------------
# Rutas y constantes de la interfaz
# ---------------------------------------------------------------------------

BASE_DIR = pathlib.Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
CSS_PATH = ASSETS_DIR / "styles.css"
LOGO_PATH = ASSETS_DIR / "logo.png"

QUICK_BUTTON_COUNT = 5

RISK_HINTS = {
    "RIESGO BAJO": "Sin señales claras de fraude. Mantén la precaución.",
    "RIESGO MEDIO": "Señales sospechosas detectadas. Verifica antes de actuar.",
    "RIESGO CRÍTICO": "Entrega confirmada. Actúa de inmediato.",
}

# Presentación visual del medidor de riesgo
RISK_GAUGE = {
    "RIESGO BAJO": ("🛡️", 22),
    "RIESGO MEDIO": ("⚠️", 60),
    "RIESGO CRÍTICO": ("🚨", 95),
}


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------


def _load_css() -> str:
    try:
        return CSS_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""


def _logo_data_uri() -> str:
    """Logo en base64 para que funcione sin servidor de archivos."""
    try:
        data = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{data}"
    except OSError:
        return ""


def _header_html() -> str:
    logo = _logo_data_uri()
    img = f'<img src="{logo}" alt="PilasBot" class="brand-logo" />' if logo else (
        '<div class="brand-logo fallback">🛡️</div>'
    )
    return f"""
<header class="pilas-header" id="pilas-header">
  <div class="brand">
    {img}
    <div class="brand-text">
      <h1 class="brand-title">Pilas<span class="accent">Bot</span></h1>
      <p class="brand-subtitle">Tu aliado contra las estafas digitales</p>
    </div>
  </div>
  <div class="header-side">
    <div class="status-pill" title="PilasBot está listo para ayudarte">
      <span class="pulse-dot"></span> Asistente activo
    </div>
    <div class="header-chips">
      <span class="chip emerald">🔒 Nunca pido tus datos</span>
      <span class="chip">📘 Guía académica</span>
      <span class="chip">⚡ Respuesta inmediata</span>
    </div>
  </div>
</header>
"""


def _welcome_html() -> str:
    return f"""
<section class="welcome-card">
  <div class="welcome-icon">👋</div>
  <div class="welcome-text">
    <h2>Bienvenido a PilasBot</h2>
    <p>{sc.WELCOME_PANEL}</p>
    <div class="welcome-chips">
      <span class="chip">🧩 4 situaciones guiadas</span>
      <span class="chip">📊 Clasificación de riesgo</span>
      <span class="chip">🧭 Recomendaciones paso a paso</span>
    </div>
  </div>
</section>
"""


def _tips_html() -> str:
    items = "".join(f'<li><span class="tip-check">✔</span>{tip}</li>' for tip in sc.SAFETY_TIPS)
    count = len(sc.SAFETY_TIPS)
    return f"""
<section class="tips-card">
  <h3><span class="tip-shield">🛡️</span> Consejos básicos
      <span class="tips-badge">{count} reglas</span></h3>
  <ul class="tips-list">{items}</ul>
</section>
"""


def _footer_html() -> str:
    return f'<footer class="pilas-footer">{sc.FOOTER}</footer>'


def _risk_panel(state: ConversationState | None) -> str:
    if state is None:
        state = new_state()
    level = state.risk_level
    css_class = risk_css_class(level)
    hint = RISK_HINTS.get(level, "")
    emoji, percent = RISK_GAUGE.get(level, ("🛡️", 10))
    if not state.started:
        hint = "Escríbeme tu caso y lo revisaremos juntos."
        emoji, percent = ("🛡️", 8)
    scenario_label = ""
    if state.scenario in sc.SCENARIOS:
        sdef = sc.SCENARIOS[state.scenario]
        scenario_label = (
            f'<div class="risk-scenario">{sdef["icon"]} {sdef["short"]}</div>'
        )
    alert_bar = '<div class="risk-alert-bar">⚠ ACTÚA DE INMEDIATO ⚠</div>'
    return f"""
<section class="risk-card {css_class}" id="risk-card">
  <div class="risk-top">
    <div class="risk-head">
      <span class="risk-lamp"></span>
      <span class="risk-caption">Nivel de riesgo</span>
    </div>
    <div class="risk-emoji" aria-hidden="true">{emoji}</div>
  </div>
  <div class="risk-level">{level}</div>
  <div class="risk-meter" role="meter" aria-valuenow="{percent}" aria-valuemin="0"
       aria-valuemax="100" aria-label="Indicador de riesgo">
    <i style="width:{percent}%"></i>
  </div>
  <div class="risk-hint">{hint}</div>
  {scenario_label}
  {alert_bar}
</section>
"""


def _quick_updates(replies: List[str]) -> list:
    """Actualiza los botones de respuesta rápida (5 ranuras)."""
    updates = []
    for i in range(QUICK_BUTTON_COUNT):
        if i < len(replies):
            updates.append(gr.update(value=replies[i], visible=True))
        else:
            updates.append(gr.update(visible=False))
    return updates


# ---------------------------------------------------------------------------
# Lógica de eventos
# ---------------------------------------------------------------------------


def _apply_message(message: str, history: list, state: ConversationState):
    """Procesa un mensaje y devuelve todas las actualizaciones de la UI."""
    history = list(history or [])
    message = (message or "").strip()

    if not message:
        return (
            history,
            state,
            _risk_panel(state),
            *_quick_updates(current_quick_replies(state)),
            gr.update(),
        )

    reply = process_message(message, state)

    if reply.restart:
        # Reinicio: se limpia el historial y se muestra el saludo nuevo
        history = [{"role": "assistant", "content": reply.text}]
    else:
        history = history + [{"role": "user", "content": message}]
        if reply.text:
            history = history + [{"role": "assistant", "content": reply.text}]

    return (
        history,
        reply.state,
        _risk_panel(reply.state),
        *_quick_updates(reply.quick_replies),
        gr.update(value=""),  # limpia el campo de texto
    )


def _reset_conversation():
    """Reinicia por completo la conversación (botón Reiniciar)."""
    greeting = sc.GREETING + "\n\n" + sc.MENU_INTRO
    state = new_state().update(started=True)
    return (
        initial_history(greeting),
        state,
        _risk_panel(state),
        *_quick_updates(current_quick_replies(state)),
        gr.update(value=""),
    )


def _menu_click(label: str, history: list, state: ConversationState):
    """Un botón del menú principal actúa como si el usuario lo escribiera."""
    return _apply_message(label, history, state)


# ---------------------------------------------------------------------------
# Construcción de la interfaz
# ---------------------------------------------------------------------------

APP_TITLE = "PilasBot — Tu aliado contra las estafas digitales"


def build_app() -> gr.Blocks:
    initial_state = new_state()
    greeting = sc.GREETING + "\n\n" + sc.MENU_INTRO

    with gr.Blocks(
        title=APP_TITLE,
        elem_id="pilas-app",
    ) as demo:
        gr.HTML(_header_html())
        gr.HTML(_welcome_html())

        # ---- Menú interactivo de situaciones ----
        gr.HTML('<div class="section-label">Elige tu situación</div>')
        with gr.Row(elem_id="menu-row", elem_classes=["menu-row"]):
            menu_buttons = []
            for option in sc.MENU_OPTIONS:
                btn = gr.Button(
                    option,  # etiqueta pura; el icono y el subtítulo los pinta el CSS
                    elem_classes=["menu-btn", f"menu-btn-{len(menu_buttons)}"],
                    scale=1,
                    min_width=220,
                )
                menu_buttons.append(btn)

        # ---- Conversación + paneles laterales ----
        with gr.Row(elem_id="main-row"):
            with gr.Column(scale=3, elem_id="chat-column"):
                chatbot = gr.Chatbot(
                    value=initial_history(greeting),
                    elem_id="chatbot",
                    height=520,
                    show_label=False,
                    buttons=[],
                    avatar_images=(None, str(LOGO_PATH)) if LOGO_PATH.exists() else (None, None),
                    placeholder="<div class='chat-placeholder'>🤖 Escríbeme tu caso y lo revisamos juntos paso a paso.</div>",
                )

                with gr.Row(elem_classes=["input-row"]):
                    txt = gr.Textbox(
                        placeholder="Escribe aquí tu mensaje… (ej: «Me llegó un mensaje del banco»)",
                        show_label=False,
                        elem_id="msg-input",
                        scale=4,
                        autofocus=True,
                        max_lines=4,
                    )
                    send_btn = gr.Button("Enviar ➤", elem_classes=["send-btn"], scale=1)
                    reset_btn = gr.Button(
                        "🔄 Reiniciar", elem_classes=["reset-btn"], scale=1
                    )

                # ---- Botones de respuesta rápida (inician con el menú) ----
                with gr.Row(elem_id="quick-row", elem_classes=["quick-row"]):
                    initial_replies = current_quick_replies(initial_state)
                    quick_buttons = [
                        gr.Button(
                            value=initial_replies[i] if i < len(initial_replies) else "",
                            visible=i < len(initial_replies),
                            elem_classes=["quick-btn"],
                            scale=1,
                            min_width=120,
                        )
                        for i in range(QUICK_BUTTON_COUNT)
                    ]

            # ---- Panel lateral: riesgo + consejos ----
            with gr.Column(scale=1, elem_id="side-column"):
                risk_html = gr.HTML(_risk_panel(initial_state))
                gr.HTML(_tips_html())

        gr.HTML(_footer_html())

        # ---- Estado compartido ----
        state = gr.State(initial_state)

        # Eventos -------------------------------------------------------
        outputs = [
            chatbot,
            state,
            risk_html,
            *quick_buttons,
            txt,
        ]

        txt.submit(
            _apply_message,
            inputs=[txt, chatbot, state],
            outputs=outputs,
        )
        send_btn.click(
            _apply_message,
            inputs=[txt, chatbot, state],
            outputs=outputs,
        )
        reset_btn.click(
            _reset_conversation,
            inputs=None,
            outputs=outputs,
        )

        for btn, option in zip(menu_buttons, sc.MENU_OPTIONS):
            btn.click(
                partial(_menu_click, option),
                inputs=[chatbot, state],
                outputs=outputs,
            )

        for qbtn in quick_buttons:
            qbtn.click(
                _apply_message,
                inputs=[qbtn, chatbot, state],
                outputs=outputs,
            )

    return demo


demo = build_app()


# ---------------------------------------------------------------------------
# Punto de entrada ASGI (Vercel / uvicorn / gunicorn)
# ---------------------------------------------------------------------------
# Vercel detecta `app.py` con una variable ASGI llamada `app` y la ejecuta como
# Function. Al importar el módulo (no al ejecutarlo como script) se monta el
# Blocks de Gradio sobre FastAPI con el mismo CSS y tema del modo local.

def _build_asgi_app():
    from fastapi import FastAPI

    fastapi_app = FastAPI(title=APP_TITLE)
    return gr.mount_gradio_app(
        fastapi_app,
        demo,
        path="/",
        css=_load_css(),
        theme=gr.themes.Soft(primary_hue="emerald", neutral_hue="slate"),
        ssr_mode=False,
    )


app = _build_asgi_app() if __name__ != "__main__" else None


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        inbrowser=True,
        css=_load_css(),
        theme=gr.themes.Soft(primary_hue="emerald", neutral_hue="slate"),
    )
