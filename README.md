# 🛡️ PilasBot — Tu aliado contra las estafas digitales

**Proyecto académico — Universidad de Santander (UDES)**
Ingeniería de Software · Requisitos de Software · Semestre 2026B

**Autores:**
- Keyner Steven García Anaya — Código 01240371013
- Diego Alejandro Duran Crispin — Código 01240372007

---

## 1. Descripción

PilasBot es un **chatbot de orientación en ciberseguridad** que ayuda a las personas a
identificar posibles estafas digitales **antes** de ser víctimas de ellas.

En Colombia, "pilas" significa estar alerta y atento: ese es justo el propósito del
chatbot, ayudarte a estar atento ante posibles estafas digitales.

### ¿A quién ayuda?

A personas que usan WhatsApp, redes sociales y banca móvil en su día a día y que son
blanco frecuente de fraudes, en especial:

- 👴 Adultos mayores
- 🎓 Estudiantes
- 🏪 Pequeños comerciantes

### Problema concreto que resuelve

Muchas personas pierden dinero o entregan datos personales por estafas digitales
(enlaces falsos del banco, ofertas de empleo o compra y venta fraudulentas,
suplantación de familiares) porque no tienen a quién consultar en el momento.
PilasBot da una orientación inmediata: ayuda a verificar si una situación es
sospechosa y qué hacer antes de enviar dinero, códigos o claves.

---

## 2. Funcionalidades

### Escenarios principales (según el documento de la asignatura)

| # | Situación | Preguntas clave |
|---|-----------|-----------------|
| 1 | 🏦 Recibí un mensaje o enlace del banco (phishing) | Canal del mensaje · Qué te pide · ¿Ya hiciste clic o entregaste datos? |
| 2 | 💼 Me ofrecieron un empleo o una compra/venta en línea con pago adelantado | Dónde viste la oferta · ¿Piden dinero antes? · ¿Empresa/vendedor verificable? |
| 3 | 👨‍👩‍👧 Alguien dice ser un familiar y me pide dinero o un código | Número nuevo · Qué te pide · ¿Confirmaste su identidad? |
| 4 | 🔍 Tengo otra situación sospechosa | Descripción libre + análisis de palabras clave + pregunta de entrega |

### Capacidades

- ✅ Comprensión de mensajes en lenguaje natural (no solo botones).
- ✅ Máquina de estados conversacional: conserva escenario, pregunta actual,
  respuestas, nivel de riesgo y si el usuario entregó datos/dinero/códigos.
- ✅ Detección de señales de alerta (urgencia, enlaces falsos, solicitud de claves,
  pagos anticipados, números nuevos, códigos de WhatsApp, etc.).
- ✅ Clasificación de riesgo en 3 niveles: **BAJO / MEDIO / CRÍTICO**, mostrado
  visualmente en la interfaz.
- ✅ Modo urgente automático cuando el usuario confirma haber entregado datos,
  dinero o códigos.
- ✅ Respuestas rápidas (botones), menú de situaciones, botón de reinicio y
  comando de texto "menú"/"reiniciar".
- ✅ **Límites claros**: si le preguntan quién es o qué puede hacer, explica su
  alcance; si le piden garantías absolutas o que transfiera dinero/dé claves,
  se niega y explica por qué.
- ✅ **Seguridad**: nunca pide claves, códigos ni números completos de tarjeta;
  si el usuario los escribe, avisa y no los almacena.
- ✅ Funciona **100 % local**, sin APIs pagadas, sin modelos externos y sin
  conexión a servicios de IA.

---

## 3. Tecnologías utilizadas

| Tecnología | Uso |
|------------|-----|
| Python 3 | Lógica del chatbot |
| Gradio (Blocks) | Interfaz web, `gr.Chatbot`, `gr.State`, botones |
| CSS personalizado | Diseño moderno tipo dashboard (ver esmeralda / negro azulado) |
| NLP por reglas | Clasificación de intenciones, palabras clave y señales de alerta |
| pytest | Pruebas automatizadas |

---

## 4. Estructura del proyecto

```
chatbot/
│
├── app.py                    # Interfaz Gradio Blocks y eventos
├── chatbot.py                # Procesamiento de mensajes y respuestas
├── conversation_manager.py   # Máquina de estados conversacional
├── risk_analyzer.py          # Intenciones, señales y clasificación de riesgo
├── scenarios.py              # Preguntas, señales y recomendaciones (fuente: DOCX)
├── requirements.txt
├── README.md
├── .gitignore
├── vercel.json               # Configuración del despliegue en Vercel
│
├── assets/
│   ├── styles.css            # Diseño visual
│   └── logo.png              # Escudo de PilasBot
│
└── tests/
    └── test_chatbot.py       # 75 pruebas automatizadas (pytest)
```

### Responsabilidades

- **app.py**: interfaz Gradio (encabezado, menú, chat, panel de riesgo, consejos, pie).
- **chatbot.py**: recibe mensaje + estado → genera respuesta + estado nuevo.
- **conversation_manager.py**: estados `INICIO`, `SELECCION_ESCENARIO`,
  `PREGUNTA_ESCENARIO`, `ANALISIS`, `RECOMENDACION_PREVENTIVA`,
  `RECOMENDACION_URGENTE`, `CONSULTA_OTRA_SITUACION`, `FIN`.
- **risk_analyzer.py**: detección de intenciones, señales de alerta,
  información sensible y nivel de riesgo.
- **scenarios.py**: todo el contenido textual derivado del documento académico.

---

## 5. Instalación (Windows)

1. **Instalar Python 3.10 o superior** desde <https://www.python.org/downloads/>
   (marcar *Add Python to PATH* durante la instalación).
2. **Abrir la carpeta del proyecto** en el explorador.
3. **Abrir una terminal** en la carpeta (clic derecho → *Open in Terminal* o
   escribir `cmd` en la barra de dirección).
4. **Instalar las dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

## 6. Ejecución local

```bash
python app.py
```

5. Gradio mostrará una dirección local en la terminal, por ejemplo:

   ```
   Running on local URL:  http://127.0.0.1:7860
   ```

6. **Abrir esa dirección en el navegador** (si no se abre automáticamente).

> Para detener la aplicación: `Ctrl + C` en la terminal.

### Ejecutar las pruebas

```bash
python -m pytest tests/ -v
```

---

## 6.5 Despliegue en la nube (GitHub + Vercel)

| Recurso | URL |
|---------|-----|
| 🌐 Producción (Vercel) | <https://pilasbot.vercel.app> |
| 📦 Repositorio (GitHub) | <https://github.com/Steven02177/pilasbot> |

**Cómo funciona el despliegue:** `app.py` expone una variable ASGI `app`
(FastAPI + `gr.mount_gradio_app`) que Vercel detecta automáticamente y ejecuta
como Python Function; el resto del proyecto (CSS, lógica, pruebas) se sirve
igual que en local.

**Redesplegar tras un cambio:**

```bash
git add -A
git commit -m "Descripción del cambio"
git push                       # sube el código a GitHub
vercel deploy --prod           # publica la nueva versión en Vercel
```

> **Opcional — deploy automático en cada push:** conectar el repositorio con
> Vercel desde <https://vercel.com> → *Project → Settings → Git → Connect* e
> instalar la app de Vercel en GitHub. También puede ejecutarse
> `vercel git connect` desde la terminal.

---

## 7. Cómo usar PilasBot

1. Escribe tu caso con tus palabras (ej: *"Me llegó un mensaje del banco diciendo
   que mi cuenta será bloqueada"*) **o** elige uno de los 4 botones del menú.
2. PilasBot hará preguntas de verificación paso a paso.
3. Responde con las respuestas rápidas o escribe libremente.
4. Al final recibirás **recomendaciones preventivas** o, si ya entregaste datos
   o dinero, **instrucciones urgentes** con el nivel de riesgo resaltado.
5. Puedes volver al menú escribiendo **"menú"** o reiniciar con el botón 🔄.

---

## 8. Cumplimiento de la rúbrica del examen (30 % · 30 % · 40 %)

### 8.1 Interfaz — 30 %

| Criterio | Cómo se cumple |
|----------|----------------|
| Diseño visual (colores, tipografía, organización) | Paleta esmeralda / negro azulado / blanco / gris / rojo / ámbar; tipografía Segoe UI/Inter; layout tipo dashboard (cabecera, bienvenida, menú de 4 tarjetas, chat + panel lateral, pie). Glassmorphism, medidor de riesgo y cinta de alerta en modo CRÍTICO. |
| Usabilidad (fácil de usar e intuitiva) | Las 4 situaciones se eligen con un clic; respuestas rápidas contextuales en cada pregunta; Enter para enviar; botón **Reiniciar**; comando "menú"; el chat conserva el historial. |
| Accesibilidad (legibilidad y contraste) | Texto claro sobre fondo oscuro (contraste alto), tamaños ≥ 13 px, jerarquía de títulos, `role="meter"` con `aria-label` en el medidor, emojis con `aria-hidden`, foco visible y soporte de `prefers-reduced-motion`. |

### 8.2 Modelo — 30 %

| Criterio | Cómo se cumple |
|----------|----------------|
| Datos y entrenamiento (calidad y variedad) | Base de conocimiento tomada del DOCX: 4 escenarios con preguntas, señales y recomendaciones. Clasificador con ~180 palabras clave en 8 intenciones + 3 intenciones meta, normalización Unicode (tildes/ñ), tolerancia a plurales y desambiguación por puntaje. |
| Lógica y código (estructura y funcionamiento) | 5 módulos con responsabilidades separadas (`app`, `chatbot`, `conversation_manager`, `risk_analyzer`, `scenarios`), máquina de estados explícita (8 estados), sin APIs ni modelos externos. |
| Funcionamiento técnico (ejecución y estabilidad) | `python app.py` abre la app sin configuración extra; **75 pruebas pytest** en verde; flujos probados de los 4 escenarios, reinicio y mensajes inválidos; sin errores de consola. |

### 8.3 Respuestas — 40 %

| Criterio | Cómo se cumple |
|----------|----------------|
| Comprensión (interpreta la pregunta) | Entiende variaciones naturales ("me robaron la cuenta de facebook" → escenario libre, no banco; "qué tiempo hace" → fuera de contexto), saludos, despedidas y peticiones de ayuda. |
| Precisión y coherencia | Respuestas basadas en el DOCX, riesgo coherente con lo respondido, recomendaciones de prevención vs. urgentes, sin inventar canales oficiales ni pedir datos sensibles. |
| Preguntas desconocidas (reconoce límites) | `OUT_OF_CONTEXT` para temas ajenos, `UNKNOWN_INTENT_REPLY` para mensajes ambiguos, `IDENTITY_REPLY` (qué puede y qué no), `LIMIT_REPLY` (no garantiza si es fraude) e `IMPOSSIBLE_REQUEST_REPLY` (no transfiere dinero ni da claves). |

---

## 9. Cómo presentar el proyecto al profesor

1. Ejecutar `python app.py` antes de la exposición y dejar la pestaña abierta.
2. Explicar en orden:
   - **La idea**: nombre, público objetivo y problema que resuelve.
   - **Los 3 escenarios** + escenario libre, mostrando un recorrido completo por
     pantalla (ej: phishing con entrega de clave → riesgo CRÍTICO).
   - **La arquitectura**: 5 módulos con responsabilidades separadas.
   - **La máquina de estados** y el clasificador de riesgo (mostrar `chatbot.py`
     y `risk_analyzer.py`).
   - **Seguridad y responsabilidad**: no pide datos sensibles, no inventa
     canales oficiales, las recomendaciones son orientativas.
3. Ejecutar las pruebas en vivo: `python -m pytest tests/ -v` (75 pruebas).
4. Cerrar con el pie: *"PilasBot — Proyecto académico de Ingeniería de Software | UDES 2026B"*.

---

## 10. Notas de diseño

- La clasificación de riesgo es **orientativa**: no afirma que una situación sea
  definitivamente fraudulenta sin suficientes datos.
- PilasBot **no inventa teléfonos, direcciones ni enlaces de denuncia**: recomienda
  buscar siempre los canales oficiales del banco o de las autoridades colombianas.
- No se almacena ningún dato financiero personal; los valores sensibles que el
  usuario escriba por error se reemplazan por un marcador y se avisa al instante.

---

*PilasBot — Proyecto académico de Ingeniería de Software | UDES 2026B*
