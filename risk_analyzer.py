# -*- coding: utf-8 -*-
"""
Motor de análisis de lenguaje de PilasBot.

Implementa procesamiento de lenguaje natural basado en lógica de clasificación
de intenciones, detección de palabras clave, identificación de señales de alerta,
detección de información sensible y clasificación del nivel de riesgo.

No depende de modelos externos ni de APIs: todo funciona localmente.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Niveles de riesgo (sección 7 del documento)
# ---------------------------------------------------------------------------

RIESGO_BAJO = "RIESGO BAJO"
RIESGO_MEDIO = "RIESGO MEDIO"
RIESGO_CRITICO = "RIESGO CRÍTICO"

RISK_ORDER = {RIESGO_BAJO: 0, RIESGO_MEDIO: 1, RIESGO_CRITICO: 2}


# ---------------------------------------------------------------------------
# Normalización de texto
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Minúsculas, sin acentos ni signos ruidosos, espacios colapsados."""
    if not text:
        return ""
    text = text.lower().strip()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace("ñ", "n")
    text = re.sub(r"\s+", " ", text)
    return text


def _contains(text: str, *words: str) -> bool:
    """True si alguno de las palabras/frases aparece como token en el texto."""
    for word in words:
        if re.search(r"(?<!\w)" + re.escape(word) + r"(?!\w)", text):
            return True
    return False


def _keyword_hit(msg: str, keyword: str) -> bool:
    """Coincidencia de palabra completa (con plural tolerado)."""
    kw = normalize(keyword)
    if not kw:
        return False
    return _contains(msg, kw) or _contains(msg, kw + "s")


# ---------------------------------------------------------------------------
# Clasificación de intenciones
# ---------------------------------------------------------------------------

# Menú principal: se comparan etiquetas normalizadas
MENU_LABELS = {
    normalize("Recibí un mensaje o enlace del banco"): "banco",
    normalize("Me ofrecieron un empleo o una compra/venta en línea"): "empleo",
    normalize("Alguien dice ser un familiar y me pide dinero o un código"): "familia",
    normalize("Tengo otra situación sospechosa"): "otra",
}

INTENT_KEYWORDS: Dict[str, List[str]] = {
    "banco": [
        "banco", "bancaria", "bancario", "banca", "tarjeta",
        # "cuenta" sola es ambigua ("me robaron la cuenta de facebook"):
        # se exige contexto bancario explícito.
        "cuenta bancaria", "cuenta del banco", "mi cuenta", "cuentas bancarias",
        "debito", "credito", "ahorro", "enlace", "phishing", "bloqueo", "bloqueada",
        "bloquearan", "token", "otp", "clave bancaria", "movimiento", "transferencia",
        "app oficial", "daviplata", "nequi", "bancolombia", "davivienda", "bbva",
        "itau", "scotiabank",
    ],
    "empleo": [
        "empleo", "trabajo", "oferta", "vacante", "contratar", "contrato", "salario",
        "sueldo", "ganancia", "factura", "compra", "venta", "vendedor", "producto",
        "envio", "inscripcion", "capacitacion", "marketplace", "mercado libre",
        "mercadolibre", "olx", "independiente", "remoto", "pagar antes", "adelanto",
        "capturistas", "inversion", "oportunidad laboral",
    ],
    "familia": [
        "familiar", "mama", "papa", "mami", "papi", "hijo", "hija", "hermano",
        "hermana", "primo", "prima", "tio", "tia", "abuelo", "abuela", "nieto",
        "amigo", "amiga", "numero nuevo", "whatsapp", "codigo", "6 digitos",
        "video llamada", "videollamada", "emergencia", "urgentemente",
        "me pide dinero", "favor urgente",
    ],
    "proteger": [
        "proteger", "protegerme", "protegerse", "protejo", "protege", "proteccion",
        "precaucion", "prevencion", "consejos", "recomendaciones generales",
        "evitar estafas", "evito", "cuido", "cuidarme", "seguridad",
        "como evito", "que hago para evitar", "aprender",
    ],
    "saludo": [
        "hola", "buenas", "buenos dias", "buenas tardes", "buenas noches",
        "que tal", "hey", "saludos", "ayuda", "help",
        # El usuario no sabe por dónde empezar: se le lleva al menú
        "no se que hacer", "que hago", "que me recomiendas",
        "no se por donde empezar", "necesito orientacion",
    ],
    "agradecer": ["gracias", "genial", "perfecto", "excelente", "bueno", "ok"],
    "despedida": [
        "adios", "hasta luego", "hasta pronto", "chao", "nos vemos", "bye",
        "me voy", "buenas noches",
    ],
    # Situación genérica de estafa (escenario 4 cuando el usuario describe algo)
    "otra": [
        "estafa", "estafando", "estafaron", "estafador", "engano", "engaño",
        "robaron", "robo", "victima", "suplantan", "suplantacion", "falso",
        "fraude", "delito", "timador", "timaron", "hackearon", "hackeo",
        # Escenario 4: cualquier otra estafa (correo, clonación, enlaces raros)
        "dian", "correo", "email", "cedula", "clonar", "clonaron", "clonen",
        "clono", "link", "links", "facebook", "instagram", "suplantaron",
    ],
    # ---- Intenciones meta (no son escenarios: definen el alcance del bot) ----
    "identidad": [
        "quien eres", "quien sos", "que eres", "como te llamas", "presentate",
        "que puedes hacer", "que haces", "como funcionas", "para que sirves",
        "que tipo de ayuda", "me puedes ayudar", "puedes ayudarme",
        "eres un bot", "eres humano", "eres una ia", "eres de google",
    ],
    "limite": [
        "me garantizas", "garantizame", "garantia", "me aseguras", "estafa seguro",
        "fraude seguro", "seguro es estafa", "seguro es fraude", "certeza",
        "puedes asegurar", "es seguro que", "me confirmas que",
    ],
    "solicitud_imposible": [
        "transferirme", "enviame dinero", "enviame plata", "hazme una transferencia",
        "dime mi clave", "dame mi clave", "pasame mi clave", "cual es mi clave",
        "mi clave del banco", "mueveme el dinero", "prestame dinero",
    ],
}

# Palabras que, solas, indican que el mensaje está fuera del contexto esperado
OUT_OF_CONTEXT_HINTS = [
    "chiste", "broma", "receta", "recetame", "cocina", "futbol", "deporte", "tarea",
    "musica", "pelicula", "juego", "videojuego", "amor", "novia", "novio",
    "clima", "hora", "noticias", "politica", "deporte",
    "que tiempo", "tiempo hace", "temperatura", "pronostico", "llovera",
    "partido", "dolar", "ensename",
]


def detect_intent(text: str) -> Optional[str]:
    """
    Clasifica la intención del mensaje.

    Prioridad: etiquetas exactas del menú > saludo > protección > escenarios
    > situación genérica > None (sin intención reconocible).
    """
    msg = normalize(text)
    if not msg:
        return None

    # 1. Etiquetas del menú (botones o texto casi idéntico)
    for label, key in MENU_LABELS.items():
        if label == msg or (len(msg) > 12 and (label in msg or msg in label)):
            return key

    # 2. Intenciones con palabras clave (coincidencia por palabra completa
    #    para no confundir "cuenta" con "cuéntame", más plural)
    scores: Dict[str, int] = {}
    for intent, keywords in INTENT_KEYWORDS.items():
        hits = sum(1 for kw in keywords if _keyword_hit(msg, kw))
        if hits:
            scores[intent] = hits

    if scores:
        # Límites de seguridad: el bot se niega a pedir/dar claves o transferir
        # dinero, y a garantizar certezas que no tiene. Van primero.
        for meta in ("solicitud_imposible", "limite"):
            if meta in scores:
                return meta
        # Intenciones meta: si el usuario pide protección, tiene prioridad
        if "proteger" in scores:
            return "proteger"
        # Identidad ("¿quién eres?") solo gana si no hay ninguna otra señal
        # en juego; si el usuario además describe una estafa, manda la estafa.
        if "identidad" in scores:
            others = {
                k: v for k, v in scores.items()
                if k not in ("identidad", "saludo", "agradecer")
            }
            if not others:
                return "identidad"
            del scores["identidad"]
        # "otra" solo gana si ningún escenario específico tiene más peso
        # (evita que "me estafaron con un enlace del banco" se vaya al genérico)
        scenario_scores = {k: v for k, v in scores.items() if k in ("banco", "empleo", "familia")}
        if scenario_scores:
            best = max(scenario_scores, key=lambda k: scenario_scores[k])
            # "estafa/estafaron" no debe ganarle a un escenario con evidencia concreta
            if scores.get("otra", 0) <= scenario_scores[best]:
                return best
            # ...pero sí cuando el usuario habla de fraude en general y el
            # escenario solo coincide por palabras débiles ("cuenta", "código")
            if scenario_scores[best] >= 2:
                return best
        best_overall = max(scores, key=lambda k: scores[k])
        if best_overall == "otra" and len(scores) > 1 and scores["otra"] == 1:
            # palabra genérica aislada acompañada de intención más fuerte
            others = {k: v for k, v in scores.items() if k != "otra"}
            if others:
                return max(others, key=lambda k: others[k])
        return best_overall

    # 3. Nada reconocible
    return None


def is_out_of_context(text: str) -> bool:
    """True si el mensaje parece ajeno al tema de ciberseguridad."""
    msg = normalize(text)
    if not msg:
        return False
    if detect_intent(msg) is not None:
        return False
    if _contains(msg, *OUT_OF_CONTEXT_HINTS):
        return True
    # Sin palabras relacionadas con estafas ni escenarios
    scam_terms = [
        "estafa", "banco", "tarjeta", "enlace", "clave", "codigo", "dinero",
        "trabajo", "oferta", "familiar", "whatsapp", "mensaje", "pago",
        "fraude", "robaron", "victima", "suplant", "phishing",
        "plata", "envie", "envio", "transfiri", "estafaron", "engano",
        "timaron", "premio", "verificacion", "datos", "cuenta", "usuario",
        # Temas de ciberseguridad que antes se leían como ajenos
        "cedula", "clon", "link", "correo", "dian", "facebook", "instagram",
        "miedo", "robo", "hackeo", "delito",
    ]
    return not any(t in msg for t in scam_terms)


# ---------------------------------------------------------------------------
# Respuestas sí / no
# ---------------------------------------------------------------------------

NEGATIVE_RE = re.compile(
    r"(?<!\w)(no|nunca|jamas|nadie|nada|ninguno|ninguna|todavia no|aun no|"
    r"para nada|nop|tampoco|no lo hice|no pude|no he)(?!\w)"
)

AFFIRMATIVE_RE = re.compile(
    r"(?<!\w)(si|yes|claro|obvio|exacto|correcto|afirmativo|asique|"
    r"por supuesto|desde luego|ya|ya lo hice|ya hice|ya esta)(?!\w)"
)


def is_affirmative(text: str) -> bool:
    """
    Detecta respuestas afirmativas sin confundirlas con 'no'.

    Regla: la primera parte de la respuesta (antes de la primera coma) manda.
    "No, todavía no" -> False.  "Sí, ya lo hice" -> True.
    """
    msg = normalize(text)
    if not msg:
        return False
    first = msg.split(",")[0].strip()
    if re.match(r"^(no|nunca|jamas|todavia no|aun no|para nada|nop|ya no)\b", first):
        return False
    return bool(AFFIRMATIVE_RE.search(msg))


def is_negative(text: str) -> bool:
    """Detecta respuestas negativas (si no son afirmativas)."""
    msg = normalize(text)
    if not msg or is_affirmative(text):
        return False
    return bool(NEGATIVE_RE.search(msg))


# Entrega confirmada en pasado (con acento) o con "ya" + verbo
ACCENTED_PAST_RE = re.compile(
    r"\b(envié|pague|pague|pagué|transferí|entregué|compartí|mandé|proporcioné|"
    r"deposité|metí|ingresé|escribí|cambié)\b",
    re.IGNORECASE,
)
YA_PAST_RE = re.compile(
    r"\bya\b[^.!?]{0,60}?\b(envi\w*|mand\w*|pago\w*|pagu\w*|transfer\w*|"
    r"entreg\w*|compart\w*|deposit\w*|d[ií]\b)",
    re.IGNORECASE,
)
CLICK_RE = re.compile(
    r"\b(hice clic|hice click|abri\b|abrir\b|clic\b|click\b|ingres[ée] al enlace|"
    r"met[ií] el enlace)\b",
    re.IGNORECASE,
)
CREDENTIAL_DELIVERY_RE = re.compile(
    r"\b(entregu\w*|comparti\w*|proporcion\w*|d[ií]\s+(mi|la|el|los|las)\s+"
    r"(clave|contrasena|codigo|datos|tarjeta|numero)|ingres\w*\s+\w*\s*"
    r"(clave|contrasena|datos|tarjeta)|escrib\w*\s+\w*\s*(clave|codigo))\b",
    re.IGNORECASE,
)


def detect_delivery(text: str) -> Tuple[bool, bool, bool, bool]:
    """
    Detecta un compromiso confirmado por el usuario en su mensaje.

    Returns:
        (entrego_datos, envio_dinero, compartio_codigo, hizo_clic)

    Nota: distingue "me piden que le envíe dinero" (reporte, no entrega)
    de "ya envié dinero" (entrega confirmada).
    """
    raw = (text or "").lower()
    msg = normalize(text)
    if not msg:
        return False, False, False, False

    past = bool(ACCENTED_PAST_RE.search(raw)) or bool(YA_PAST_RE.search(raw))
    cred = bool(CREDENTIAL_DELIVERY_RE.search(msg))
    codigo = bool(
        re.search(r"\b(codigo|codigos|otp|token|6 digitos|seis digitos)\b", msg)
        and (past or cred or re.search(r"\bcomparti\w*\b", msg))
    )
    money = bool(
        re.search(r"\b(dinero|plata|pago|transferencia|deposito|giro)\b", msg)
        and (past or cred)
    )
    entrego = cred or bool(
        re.search(r"\b(clave|contrasena|password|tarjeta|credenciales)\b", msg) and past
    )
    clic = bool(CLICK_RE.search(raw)) and not entrego
    return entrego, money, codigo, clic


# ---------------------------------------------------------------------------
# Detección de información sensible (seguridad)
# ---------------------------------------------------------------------------

CARD_RE = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
SECRET_RE = re.compile(
    r"(mi\s+)?(clave|contrasena|password|pin|codigo|otp|token)\s*(es|:|=)\s*[^\s]{3,}"
)
SECRET_LABELED_RE = re.compile(
    r"(clave|contrasena|password|pin|codigo|otp|token)\s*(es|:|=)\s*\d{4,10}"
)


def contains_sensitive_info(text: str) -> bool:
    """Detecta claves, códigos o números de tarjeta escritos en el chat."""
    msg = normalize(text)
    if not msg:
        return False
    if CARD_RE.search(msg):
        return True
    if SECRET_RE.search(msg) or SECRET_LABELED_RE.search(msg):
        return True
    # Pasaporte/cédula larga o números de cuenta con etiqueta
    if re.search(r"(cuenta|tarjeta|cc|cedula)\s*(es|:|=)?\s*\d{6,}", msg):
        return True
    return False


def mask_answer(text: str) -> str:
    """Reemplaza valores sensibles por un marcador para no almacenarlos."""
    if not contains_sensitive_info(text):
        return text
    return "[información sensible omitida]"


# ---------------------------------------------------------------------------
# Señales de alerta
# ---------------------------------------------------------------------------

# Banco (señales del documento)
SIGNAL_PATTERNS: List[Tuple[str, str, str]] = [
    ("urgencia", r"\b(urgente|urgentes|inmediato|inmediata|ahora mismo|hoy|24 horas|vence|vencera|bloquead\w*|suspendid\w*|suspendera|ultima alerta|actua ya)\b", "Tono de urgencia o amenaza de bloqueo de cuenta."),
    ("enlaces_falsos", r"(http://|https?://|www\.|bit\.ly|tinyurl|enlace|link|clic|click|ingresar al|abrir el|acortad|www[.-])", "Enlaces acortados o con direcciones que imitan al banco."),
    ("solicitud_claves", r"(clave|contrasena|password|token|otp|codigo de verificacion|datos de la tarjeta|numero completo|cvv|fecha de vencimiento)", "Solicitud de clave, token o datos completos de la tarjeta."),
    ("remitente_desconocido", r"(numero nuevo|desconocido|no oficial|no lo tengo|no reconozco|no se quien|otro numero|mensaje de un)", "Remitente desconocido o número no oficial."),
    # Empleo / compra-venta
    ("ganancias_altas", r"(gana|ganar|ganancia|ganancias|facil|sin esfuerzo|sin experiencia|desde casa|extra|mucho dinero|millones|rapido)", "Ganancias muy altas con poco esfuerzo."),
    ("pago_adelantado", r"(pago antes|pagar antes|adelanto|inscripcion|capacitacion|envio|matricula|deposita|depositar|transferi.*antes|cobro inicial|precio por adelantado)", "Pagos por adelantado («inscripción», «capacitación», «envío»)."),
    ("precio_bajo", r"(muy barato|baratisimo|regalo|por debajo del mercado|mitad de precio|precio increible|demasiado barato|super oferta)", "Precios muy por debajo del mercado."),
    ("presion_rapido", r"\b(rapido|rapida|ahora|ya|no lo pienses|ultimo dia|se acaba|por tiempo limitado|responde ya|no cuentes a nadie|secreto|no le digas|telegram)\b|cambia\w* (de|la) plataforma", "Presión para decidir rápido o sacar la conversación a otra plataforma."),
    ("perfil_nuevo", re.escape("perfil nuevo") + r"|" + re.escape("sin resenas") + r"|" + re.escape("sin historial") + r"|" + re.escape("sin referencias") + r"|" + re.escape("no tiene pagina"), "Perfiles nuevos, sin historial ni reseñas."),
    # Familiares
    ("numero_nuevo", r"(numero nuevo|nuevo numero|de otro numero|no es mi numero|cambio de numero|no lo tenia guardado)", "Mensaje de un «número nuevo» con historia de emergencia."),
    ("emergencia_familiar", r"(emergencia|accidente|hospital|urgente|necesito dinero ya|necesita dinero|me robaron el telefono|estoy varado|preso|apresurado)", "Historia de emergencia para pedir dinero con urgencia."),
    ("codigo_whatsapp", r"(codigo de (6|seis) digitos|codigo de whatsapp|codigo de verificacion|te llego un codigo|llego un codigo|codigo de 6)", "Petición del código de 6 dígitos de WhatsApp (así roban la cuenta)."),
    ("niega_llamada", r"(no puede hablar|no puede llamar|no contesta|no quiero llamar|no acepta llamada|no puedo hablar por llamada|mejor por aqui|no puedo videollamada)", "Se niega a hacer llamada o videollamada."),
    ("instalar_app", r"(instala|instalar|descarga|descargar|apk|aplicacion|permisos|acceso a tu telefono|teamviewer|anydesk|acceso remoto|programa especial|control remoto)", "Solicitud de instalar aplicaciones o dar acceso remoto."),
]


def detect_signals(*texts: str) -> List[str]:
    """
    Detecta señales de alerta en uno o varios textos.

    Returns:
        Lista de identificadores canónicos de señal detectadas.
    """
    joined = normalize(" ".join(t for t in texts if t))
    found: List[str] = []
    if not joined:
        return found
    for signal_id, pattern, _label in SIGNAL_PATTERNS:
        if signal_id in found:
            continue
        if re.search(pattern, joined):
            found.append(signal_id)
    return found


def signal_label(signal_id: str) -> str:
    """Etiqueta legible de una señal."""
    for sid, _pattern, label in SIGNAL_PATTERNS:
        if sid == signal_id:
            return label
    return signal_id


def labels_for(signals: List[str]) -> List[str]:
    """Convierte identificadores de señales en etiquetas legibles."""
    return [signal_label(s) for s in signals]


# Señales que el chatbot fuerza según la respuesta a una pregunta concreta
# (mapeo escenario -> indice de pregunta -> señal que implica la respuesta)
QUESTION_SIGNAL_HINTS: Dict[Tuple[str, int], str] = {
    ("banco", 1): "solicitud_claves",
    ("empleo", 1): "pago_adelantado",
    ("familia", 1): "codigo_whatsapp",
}


# ---------------------------------------------------------------------------
# Clasificación del nivel de riesgo
# ---------------------------------------------------------------------------

def classify_risk(
    delivered_data: bool = False,
    delivered_money: bool = False,
    shared_code: bool = False,
    clicked_link: bool = False,
    signals: Optional[List[str]] = None,
) -> str:
    """
    Clasifica el nivel de riesgo (orientativo, no es un diagnóstico).

    - CRÍTICO: entrega de claves/códigos, dinero enviado o cuentas comprometidas.
    - MEDIO:  señales sospechosas sin entrega confirmada (o solo clic en enlace).
    - BAJO:   sin señales claras.
    """
    signals = signals or []
    if delivered_data or delivered_money or shared_code:
        return RIESGO_CRITICO
    if signals or clicked_link:
        return RIESGO_MEDIO
    return RIESGO_BAJO


def risk_css_class(risk: str) -> str:
    """Clase CSS asociada al nivel de riesgo."""
    if risk == RIESGO_CRITICO:
        return "risk-critical"
    if risk == RIESGO_MEDIO:
        return "risk-medium"
    return "risk-low"


def merge_risk(current: str, new: str) -> str:
    """Conserva el nivel más alto alcanzado durante la conversación."""
    if RISK_ORDER.get(new, 0) > RISK_ORDER.get(current, 0):
        return new
    return current
