# -*- coding: utf-8 -*-
"""
Contenido conversacional de PilasBot.

Fuente principal de verdad: documento académico
"Actividad de clase - Propuesta de Chatbot" (UDES, Ingeniería de Software, 2026B)
Autoría: Keyner Steven García Anaya - Diego Alejandro Duran Crispin.

Este módulo centraliza SALUDOS, PREGUNTAS, SEÑALES DE ALERTA y RECOMENDACIONES
para que el resto de la aplicación no duplique textos.
"""

# ---------------------------------------------------------------------------
# Textos generales
# ---------------------------------------------------------------------------

GREETING = (
    "¡Hola! Soy PilasBot. Estoy aquí para ayudarte a identificar posibles estafas "
    "antes de que te afecten. No te voy a pedir claves, números de tarjeta ni códigos. "
    "¿Qué te gustaría hacer hoy?"
)

MENU_INTRO = "Puedes elegir una opción o contarme directamente lo que te pasó:"

MENU_OPTIONS = [
    "Recibí un mensaje o enlace del banco",
    "Me ofrecieron un empleo o una compra/venta en línea",
    "Alguien dice ser un familiar y me pide dinero o un código",
    "Tengo otra situación sospechosa",
]

FOOTER = "PilasBot — Proyecto académico de Ingeniería de Software | UDES 2026B"

# Panel informativo (Estructura de la interfaz, punto E)
SAFETY_TIPS = [
    "Nunca compartas tus claves.",
    "No entregues códigos de verificación.",
    "Verifica los enlaces antes de abrirlos.",
    "Confirma las solicitudes de dinero.",
    "Desconfía de ofertas demasiado buenas.",
]

# Mensaje de bienvenida del panel lateral
WELCOME_PANEL = (
    "¡Hola! Soy PilasBot. Estoy aquí para ayudarte a identificar posibles estafas "
    "antes de que te afecten. No te voy a pedir claves, números de tarjeta ni códigos. "
    "¿Qué te gustaría hacer hoy?"
)

# Recomendaciones generales de protección (intención "protegerme")
PROTECTION_TIPS_INTRO = "¡Buenísima pregunta! Estas son las bases para protegerte de las estafas digitales:"

PROTECTION_TIPS = [
    "**Nunca compartas tus claves** ni las escribas en chats, formularios o enlaces que lleguen por mensaje.",
    "**No entregues códigos de verificación**: nadie legítimo (ni tu banco, ni WhatsApp, ni familiares) te los debe pedir.",
    "**Verifica los enlaces antes de abrirlos**: revisa la dirección completa; desconfía de los enlaces acortados o de dominios raros.",
    "**Confirma las solicitudes de dinero** llamando a la persona al número que ya tenías guardado, no al número nuevo que te escribió.",
    "**Desconfía de ofertas demasiado buenas**: ganancias altísimas con poco esfuerzo o precios muy bajos suelen ser trampa.",
    "**Activa la verificación en dos pasos** en WhatsApp y en tu correo.",
    "**Guarda evidencia**: toma capturas de pantalla antes de bloquear o eliminar mensajes sospechosos.",
]

OUT_OF_CONTEXT = (
    "Interesante, pero PilasBot está enfocado en ayudarte con **estafas digitales**: "
    "mensajes falsos del banco, ofertas de empleo o compra/venta fraudulentas y "
    "suplantación de familiares.\n\n"
    "Si quieres, cuéntame algo relacionado con eso o elige una opción del menú."
)

UNKNOWN_INTENT_REPLY = (
    "No estoy seguro de entender bien lo que me cuentas, y no quiero inventar nada. "
    "¿Podrías contarme con un poco más de detalle qué pasó? Por ejemplo: "
    "¿te llegó un mensaje, una oferta o alguien te pidiendo algo?"
)

RESTART_CONFIRMATION = (
    "Listo, reiniciamos la conversación. 👇"
)

SENSITIVE_INFO_WARNING = (
    "⚠️ **Detente:** acaba de aparecer información sensible en tu mensaje "
    "(una clave, un código o números de una tarjeta). **No la compartas en ningún chat**, "
    "ni conmigo. Yo no la guardo ni la repito. Si ya la escribiste en otro lugar, "
    "cambiala de inmediato desde un dispositivo seguro."
)

# Aviso de responsabilidad (clasificación orientativa)
ORIENTATION_NOTICE = (
    "_Recuerda: mis indicaciones son orientativas y no sustituyen la verificación "
    "ni a las autoridades. No puedo afirmar con certeza que una situación sea fraude._"
)

# ---------------------------------------------------------------------------
# Respuestas de alcance y límites del chatbot
# ---------------------------------------------------------------------------

IDENTITY_REPLY = (
    "Soy **PilasBot**, un chatbot académico de orientación en ciberseguridad "
    "(proyecto de Ingeniería de Software, UDES).\n\n"
    "**Lo que sí puedo hacer por ti:**\n"
    "1. Guiarte paso a paso en **4 situaciones**: mensajes del banco, "
    "empleo o compras/ventas en línea, familiares que piden dinero y otras estafas.\n"
    "2. **Clasificar el nivel de riesgo** (BAJO, MEDIO o CRÍTICO) según las "
    "señales que me cuentes.\n"
    "3. Darte **recomendaciones concretas** de prevención y, si ya entregaste "
    "dinero o datos, acciones urgentes.\n\n"
    "**Lo que no puedo (y no voy a intentar):**\n"
    "- No soy un banco, una entidad oficial ni una persona: no opero cuentas "
    "ni transferencias.\n"
    "- **Nunca te voy a pedir claves, códigos ni números de tarjeta**, y no los guardo.\n"
    "- **No doy certeza absoluta** sobre si algo es fraude o no: mi lectura es orientativa.\n"
)

LIMIT_REPLY = (
    "Entiendo que quieras estar **100% seguro**, pero no puedo darte esa "
    "garantía: soy un chatbot que reconoce señales y patrones de estafa "
    "conocidos, no una autoridad ni una entidad bancaria.\n\n"
    "Lo que sí hago es indicarte qué señales detecté y cómo **verificarlo por "
    "canales oficiales** antes de tomar una decisión.\n\n" + ORIENTATION_NOTICE
)

IMPOSSIBLE_REQUEST_REPLY = (
    "🚫 **No puedo hacer eso, y por principio no lo haría.**\n\n"
    "- **No transferiré ni enviaré dinero**, ni opero cuentas bancarias: no tengo "
    "ninguna conexión con bancos ni billeteras.\n"
    "- **No doy claves ni códigos** (ni los tuyos: no los tengo ni los pido).\n"
    "- Si alguien te pide claves, códigos o transferencias haciéndose pasar por "
    "mí o por una entidad, eso es **una señal de estafa**.\n\n"
    "Si es eso lo que te está pasando, cuéntamelo y lo revisamos juntos paso a paso."
)

FAREWELL_REPLY = (
    "¡Con gusto! Cuídate mucho. 🛡️\n\n"
    "Recuerda: **no compartas claves, códigos ni datos de tu tarjeta**, y verifica "
    "siempre por los canales oficiales. Si más adelante te llega algo sospechoso, "
    "aquí estaré para revisarlo contigo."
)


# ---------------------------------------------------------------------------
# Definición de los escenarios principales
# ---------------------------------------------------------------------------

def _scenario(
    key: str,
    label: str,
    short: str,
    icon: str,
    intro: str,
    questions: list,
    signals: list,
    preventive: list,
    urgent: list,
    decision_question: str,
    decision_replies: list,
    quick_replies: list,
) -> dict:
    """Construye la definición de un escenario con todos sus textos."""
    return {
        "key": key,
        "label": label,
        "short": short,
        "icon": icon,
        "intro": intro,
        "questions": questions,
        "signals": signals,
        "preventive": preventive,
        "urgent": urgent,
        "decision_question": decision_question,
        "decision_replies": decision_replies,
        "quick_replies": quick_replies,
    }


SCENARIOS = {
    # ------------------------------------------------------------------
    # SITUACIÓN 1: phishing bancario
    # ------------------------------------------------------------------
    "banco": _scenario(
        key="banco",
        label="Recibí un mensaje o enlace del banco",
        short="Mensaje o enlace del banco",
        icon="🏦",
        intro=(
            "Vamos a revisar ese mensaje del banco paso a paso. "
            "**No abras el enlace ni respondas mientras analizamos.**"
        ),
        questions=[
            "1/3 ¿Recibiste el mensaje por SMS, WhatsApp, correo o llamada?",
            "2/3 ¿Qué te pide el mensaje: entrar a un enlace, dar claves, confirmar datos o instalar algo?",
            "3/3 ¿Ya hiciste clic en el enlace o entregaste algún dato?",
        ],
        signals=[
            "Tono de urgencia o amenaza de bloqueo de cuenta.",
            "Enlaces acortados o con direcciones que imitan al banco.",
            "Solicitud de clave, token o datos completos de la tarjeta.",
            "Remitente desconocido o número no oficial.",
        ],
        preventive=[
            "**No abras el enlace** y **no respondas** al mensaje.",
            "Verifica directamente desde la **app oficial del banco** (descargada tú mismo).",
            "Contacta al banco usando un **canal oficial** (número que aparece en tu tarjeta o en la app).",
            "Bloquea y reporta al remitente sospechoso en tu aplicación de mensajería.",
            "Si es una llamada, cuelga y llama tú al banco por un canal oficial.",
        ],
        urgent=[
            "**Contacta a tu banco inmediatamente** por un canal oficial y reporta lo ocurrido.",
            "**Bloquea la tarjeta o la cuenta** comprometida de inmediato.",
            "**Cambia las claves comprometidas** desde un dispositivo seguro (no desde el enlace del mensaje).",
            "Solicita al banco revisar movimientos sospechosos y, si aplica, reversar operaciones.",
            "Denuncia por los **canales oficiales de delitos informáticos** de tu país (busca el canal oficial vigente; no uses números que lleguen por mensaje).",
            "Avisa a tus contactos que podrían recibir mensajes similares usando tu identidad.",
        ],
        decision_question=(
            "¿Pudiste ingresar tus claves o datos personales en ese enlace, o solo abriste el enlace?"
        ),
        decision_replies=[
            "Solo abrí el enlace",
            "Ingresé claves o datos",
        ],
        quick_replies=[
            ["Por WhatsApp", "Por SMS", "Por correo", "Fue una llamada"],
            [
                "Me pide entrar a un enlace",
                "Me pide mi clave",
                "Me pide confirmar datos",
                "Quiere que instale algo",
            ],
            ["Sí, ya hice clic", "Sí, entregué datos", "No, todavía no"],
        ],
    ),
    # ------------------------------------------------------------------
    # SITUACIÓN 2: empleo o compra/venta fraudulenta
    # ------------------------------------------------------------------
    "empleo": _scenario(
        key="empleo",
        label="Me ofrecieron un empleo o una compra/venta en línea",
        short="Empleo o compra/venta en línea",
        icon="💼",
        intro=(
            "Perfecto, revisemos esa oferta juntos. "
            "**No envíes dinero mientras la analizamos.**"
        ),
        questions=[
            "1/3 ¿Dónde viste la oferta: red social, WhatsApp o página web?",
            "2/3 ¿Te piden dinero antes de empezar a trabajar o de recibir el producto?",
            "3/3 ¿Hay una empresa o vendedor verificable mediante página web, referencias o reseñas?",
        ],
        signals=[
            "Ganancias muy altas con poco esfuerzo.",
            "Pagos por adelantado («inscripción», «capacitación», «envío»).",
            "Precios muy por debajo del mercado.",
            "Presión para decidir rápido o sacar la conversación a otra plataforma.",
            "Perfiles nuevos, sin historial ni reseñas.",
        ],
        preventive=[
            "**No envíes dinero por adelantado** a desconocidos.",
            "Busca **reseñas y referencias** y verifica la empresa o el vendedor.",
            "Prefiere pagos con **protección al comprador** o **pago contra entrega** cuando sea apropiado.",
            "Guarda **capturas de pantalla** como evidencia.",
            "Reporta el perfil sospechoso en la plataforma donde lo viste.",
        ],
        urgent=[
            "**Contacta de inmediato a tu banco o al proveedor de pago** y explica que fuiste víctima de una posible estafa.",
            "Pregunta si es posible **revertir o bloquear la operación** (actúa rápido: cuanto antes, más opciones hay).",
            "**Guarda todas las evidencias**: conversaciones, datos del perfil, cuentas y capturas de pantalla.",
            "Reporta el perfil y **denuncia por los canales oficiales** de delitos informáticos de tu país.",
            "Si te solicitaron datos de tu tarjeta o claves, **cámbialas desde un dispositivo seguro** y bloquea los productos afectados.",
        ],
        decision_question=(
            "Última pregunta: ¿ya enviaste dinero o hiciste algún pago por esta oferta?"
        ),
        decision_replies=[
            "Sí, ya envié dinero",
            "No, todavía no",
        ],
        quick_replies=[
            ["En una red social", "Por WhatsApp", "En una página web", "No recuerdo"],
            ["Sí, me piden pagar antes", "No, no piden dinero"],
            [
                "Sí, tiene página y reseñas",
                "No, no se puede verificar",
                "No estoy seguro",
            ],
        ],
    ),
    # ------------------------------------------------------------------
    # SITUACIÓN 3: suplantación de familiares
    # ------------------------------------------------------------------
    "familia": _scenario(
        key="familia",
        label="Alguien dice ser un familiar y me pide dinero o un código",
        short="Suplantación de un familiar",
        icon="👨‍👩‍👧",
        intro=(
            "Entiendo, esto puede ser muy preocupante. "
            "**No envíes dinero ni compartas códigos mientras lo revisamos.**"
        ),
        questions=[
            "1/3 ¿Te escribió desde un número nuevo diciendo que es un familiar o amigo?",
            "2/3 ¿Te pide dinero, un favor urgente o un código que te llegó por mensaje?",
            "3/3 ¿Pudiste confirmar su identidad mediante una llamada u otra persona de la familia?",
        ],
        signals=[
            "Mensaje de un «número nuevo» con historia de emergencia.",
            "Petición de transferir dinero de inmediato.",
            "Petición del código de 6 dígitos de WhatsApp (así roban la cuenta).",
            "Se niega a hacer llamada o videollamada.",
        ],
        preventive=[
            "**No envíes dinero** ni compartas códigos de verificación.",
            "Llama al familiar **al número que ya tenías guardado** para confirmar.",
            "Hazle **una pregunta que solo la persona real** sabría responder.",
            "Activa la **verificación en dos pasos de WhatsApp**.",
            "Reporta el número sospechoso en tu aplicación de mensajería.",
        ],
        urgent=[
            "Si compartiste el código de WhatsApp: **recupera el acceso a tu cuenta** siguiendo el procedimiento oficial de WhatsApp (desde la propia aplicación).",
            "**No compartas más códigos** con nadie, aunque digan ser soporte o familiares.",
            "Alerta a **familiares y contactos por otro medio** (llamada, otro número) para que no caigan en el engaño.",
            "Activa la **verificación en dos pasos** una vez recuperes el acceso.",
            "Si enviaste dinero: **contacta de inmediato a tu banco o proveedor de pago** para intentar reversar o bloquear la operación.",
            "Guarda las evidencias y **denuncia por los canales oficiales** de delitos informáticos.",
        ],
        decision_question=(
            "¿Ya enviaste dinero o compartiste algún código de verificación?"
        ),
        decision_replies=[
            "Sí, ya envié dinero",
            "Sí, compartí un código",
            "No, nada todavía",
        ],
        quick_replies=[
            ["Sí, es un número nuevo", "No, es el mismo número", "No estoy seguro"],
            ["Me pide dinero", "Me pide un código de WhatsApp", "Dice que es urgente"],
            ["Sí, lo confirmé con una llamada", "No pude confirmarlo"],
        ],
    ),
}

# Escenario 4: situación libre describida por el usuario
OTHER_SCENARIO = {
    "key": "otra",
    "label": "Tengo otra situación sospechosa",
    "short": "Otra situación sospechosa",
    "icon": "🔍",
    "intro": (
        "Cuéntame con tus palabras qué pasó. Mientras más detalle me des, mejor podré orientarte. "
        "**No compartas claves, códigos ni números de tarjeta.**"
    ),
    "question": (
        "Según lo que me cuentas, hay elementos que conviene revisar. "
        "Para darte la recomendación correcta: **¿has entregado dinero, claves o códigos "
        "a esa persona o en ese sitio?**"
    ),
    "replies": [
        "Sí, entregué dinero",
        "Sí, di claves o códigos",
        "No, nada todavía",
    ],
}


# ---------------------------------------------------------------------------
# Frases de cierre y transición
# ---------------------------------------------------------------------------

# Acuses del documento (sección "Cómo respondería si la persona cuenta algo sospechoso")
ACK_WITH_SIGNALS = (
    "Gracias por contármelo, hiciste bien en consultar antes de actuar. "
    "Por lo que me cuentas, hay señales de alerta. Por favor, no envíes dinero, "
    "no des códigos ni claves y no abras enlaces. Vamos a revisarlo paso a paso."
)

ACK_NEUTRAL = (
    "Gracias por contármelo, hiciste bien en consultar antes de actuar. "
    "Vamos a revisarlo paso a paso."
)

ASK_ANOTHER = "¿Quieres consultar otra situación?"

ASK_ANOTHER_REPLIES = [
    "Sí, quiero consultar otra",
    "No, gracias",
]

# Recomendaciones genéricas para el escenario 4 (situación libre)
GENERIC_PREVENTIVE = [
    "**No envíes dinero** ni compartas claves, códigos o números de tarjeta mientras verificas.",
    "Confirma la identidad por un **canal distinto**: llama al número guardado o entra tú a la app oficial.",
    "Busca **información y reseñas** sobre quien te contactó (nombre, número, página).",
    "Guarda **capturas de pantalla** de la conversación como evidencia.",
    "Reporta el mensaje o perfil sospechoso en la **plataforma** donde apareció.",
    "Si te llega un enlace, **verifica la dirección completa** antes de abrirlo.",
]

GENERIC_URGENT = [
    "Si enviaste dinero: **contacta de inmediato a tu banco o proveedor de pago** e intenta revertir o bloquear la operación.",
    "Si entregaste claves o datos: **cambia tus contraseñas desde un dispositivo seguro** y bloquea los productos comprometidos.",
    "Si compartiste un código de WhatsApp: **recupera el acceso** siguiendo el procedimiento oficial de WhatsApp.",
    "**Guarda todas las evidencias**: conversaciones, capturas, datos del perfil y movimientos.",
    "**Reporta y denuncia** por los canales oficiales de delitos informáticos de tu país (verifica el canal oficial vigente; no uses números que lleguen por mensaje).",
    "**Avisa a tus contactos** para que no caigan en el mismo engaño con tu identidad.",
]

PREVENTIVE_HEADER = "✅ **RECOMENDACIÓN PREVENTIVA** — todavía no entregaste datos ni dinero."
URGENT_HEADER = "🚨 **ALERTA URGENTE** — actúa ya:"
SIGNALS_HEADER = "Señales de alerta detectadas en tu caso:"
NO_SIGNALS_TEXT = (
    "Con la información que me diste no identifiqué señales claras de fraude, "
    "pero mantén la precaución y verifica por canales oficiales."
)
