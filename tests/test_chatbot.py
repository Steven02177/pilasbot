# -*- coding: utf-8 -*-
"""
Pruebas funcionales de PilasBot.

Cubre los 10 casos de prueba obligatorios del documento del proyecto
más pruebas unitarias de intenciones, riesgo y seguridad.

Ejecutar desde la raíz del proyecto:
    python -m pytest tests/ -v
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from chatbot import process_message, current_quick_replies  # noqa: E402
from conversation_manager import States, new_state  # noqa: E402
from risk_analyzer import (  # noqa: E402
    RIESGO_BAJO,
    RIESGO_CRITICO,
    RIESGO_MEDIO,
    classify_risk,
    contains_sensitive_info,
    detect_delivery,
    detect_intent,
    is_affirmative,
    is_negative,
    is_out_of_context,
)


def converse(messages, state=None):
    """Ejecuta una secuencia de mensajes y devuelve (estado_final, respuestas)."""
    if state is None:
        state = new_state()
    replies = []
    for msg in messages:
        reply = process_message(msg, state)
        state = reply.state
        replies.append(reply)
    return state, replies


# ===========================================================================
# CASO 1: enlace bancario sospechoso SIN clic
# ===========================================================================

class TestCaso1EnlaceBancarioSinClic:
    def flujo(self):
        return converse(
            [
                "Me llegó un mensaje del banco diciendo que mi cuenta será bloqueada",
                "Por WhatsApp",
                "Me pide entrar a un enlace",
                "No, todavía no",
            ]
        )

    def test_inicia_escenario_banco(self):
        state, replies = converse(
            ["Me llegó un mensaje del banco diciendo que mi cuenta será bloqueada"]
        )
        assert state.status == States.PREGUNTA_ESCENARIO
        assert state.scenario == "banco"
        assert state.question_index == 0
        assert "1/3" in replies[0].text

    def test_realiza_las_tres_preguntas(self):
        _state, replies = self.flujo()
        assert "2/3" in replies[1].text
        assert "3/3" in replies[2].text

    def test_recomendacion_preventiva(self):
        state, replies = self.flujo()
        assert state.status == States.RECOMENDACION_PREVENTIVA
        assert "RECOMENDACIÓN PREVENTIVA" in replies[-1].text
        assert "No abras el enlace" in replies[-1].text
        assert "app oficial" in replies[-1].text

    def test_no_modo_urgente_ni_critico(self):
        state, _replies = self.flujo()
        assert not state.is_critical
        assert state.risk_level != RIESGO_CRITICO
        assert state.risk_level in (RIESGO_MEDIO, RIESGO_BAJO)

    def test_respuestas_rapidas_disponibles(self):
        state, replies = self.flujo()
        assert replies[-1].quick_replies  # siempre hay opciones
        assert current_quick_replies(state)


# ===========================================================================
# CASO 2: usuario que ya entregó su clave bancaria
# ===========================================================================

class TestCaso2ClaveBancariaEntregada:
    def flujo(self):
        return converse(
            [
                "Me llegó un enlace del banco por SMS",
                "Por SMS",
                "Me pide mi clave",
                "Sí, ya la entregué",
            ]
        )

    def test_modo_urgente(self):
        state, replies = self.flujo()
        assert state.status == States.RECOMENDACION_URGENTE
        assert "ALERTA URGENTE" in replies[-1].text

    def test_riesgo_critico(self):
        state, _replies = self.flujo()
        assert state.delivered_data is True
        assert state.risk_level == RIESGO_CRITICO

    def test_recomendaciones_urgentes_del_documento(self):
        _state, replies = self.flujo()
        text = replies[-1].text
        assert "Contacta a tu banco inmediatamente" in text
        assert "Bloquea la tarjeta" in text
        assert "Cambia las claves" in text

    def test_solo_clic_no_es_critico(self):
        """Hacer clic sin entregar datos queda en riesgo medio."""
        state, replies = converse(
            [
                "Me llegó un enlace del banco",
                "Por correo",
                "Me pide entrar a un enlace",
                "Sí, ya hice clic",
                "Solo abrí el enlace",
            ]
        )
        assert state.status == States.RECOMENDACION_URGENTE
        assert state.risk_level == RIESGO_MEDIO
        assert state.delivered_data is False


# ===========================================================================
# CASO 3: oferta de empleo con pago anticipado
# ===========================================================================

class TestCaso3OfertaEmpleoPagoAdelantado:
    def flujo(self):
        return converse(
            [
                "Me ofrecieron un trabajo y me piden pagar una inscripción",
                "Por WhatsApp",
                "Sí, me piden pagar antes",
                "No, no se puede verificar",
                "No, todavía no",
            ]
        )

    def test_inicia_escenario_empleo(self):
        state, _replies = converse(
            ["Me ofrecieron un trabajo y me piden pagar una inscripción"]
        )
        assert state.scenario == "empleo"
        assert state.status == States.PREGUNTA_ESCENARIO

    def test_recomendacion_preventiva(self):
        state, replies = self.flujo()
        assert state.status == States.RECOMENDACION_PREVENTIVA
        assert "RECOMENDACIÓN PREVENTIVA" in replies[-1].text
        assert "No envíes dinero por adelantado" in replies[-1].text

    def test_detecta_senales(self):
        state, _replies = self.flujo()
        assert "pago_adelantado" in state.signals
        assert "perfil_nuevo" in state.signals
        assert state.risk_level == RIESGO_MEDIO

    def test_se_hacen_las_tres_preguntas_mas_decision(self):
        _state, replies = self.flujo()
        joined = " ".join(r.text for r in replies)
        assert "1/3" in joined
        assert "2/3" in joined
        assert "3/3" in joined
        assert "¿ya enviaste dinero" in joined.lower()


# ===========================================================================
# CASO 4: usuario que ya envió dinero a un vendedor sospechoso
# ===========================================================================

class TestCaso4EnvioDinero:
    def test_modo_urgente_inmediato(self):
        state, replies = converse(["Ya envié dinero a un vendedor sospechoso"])
        assert state.status == States.RECOMENDACION_URGENTE
        assert state.risk_level == RIESGO_CRITICO
        assert state.delivered_money is True
        assert "ALERTA URGENTE" in replies[-1].text

    def test_recomendaciones_de_pago(self):
        _state, replies = converse(["Ya envié dinero a un vendedor sospechoso"])
        text = replies[-1].text
        assert "banco" in text.lower()
        assert "evidencias" in text.lower()

    def test_durante_el_flujo(self):
        state, _replies = converse(
            [
                "Me ofrecen un trabajo independiente",
                "En una red social",
                "Sí, me piden pagar antes",
                "No, no se puede verificar",
                "Sí, ya envié dinero",
            ]
        )
        assert state.status == States.RECOMENDACION_URGENTE
        assert state.risk_level == RIESGO_CRITICO


# ===========================================================================
# CASO 5: familiar desde un número nuevo
# ===========================================================================

class TestCaso5FamiliarNumeroNuevo:
    def flujo(self):
        return converse(
            [
                "Mi mamá me escribió de otro número y necesita dinero",
                "Sí, es un número nuevo",
                "Me pide dinero",
                "No pude confirmarlo",
                "No, nada todavía",
            ]
        )

    def test_inicia_escenario_familia(self):
        state, replies = converse(["Mi mamá me escribió de otro número y necesita dinero"])
        assert state.scenario == "familia"
        assert state.status == States.PREGUNTA_ESCENARIO
        assert "1/3" in replies[0].text

    def test_recomendacion_preventiva(self):
        state, replies = self.flujo()
        assert state.status == States.RECOMENDACION_PREVENTIVA
        text = replies[-1].text
        assert "No envíes dinero" in text
        assert "número que ya tenías guardado" in text
        assert "verificación en dos pasos" in text

    def test_senales_detectadas(self):
        state, _replies = self.flujo()
        assert "numero_nuevo" in state.signals
        assert "niega_llamada" in state.signals
        assert state.risk_level == RIESGO_MEDIO


# ===========================================================================
# CASO 6: usuario que comparte un código de WhatsApp
# ===========================================================================

class TestCaso6CodigoWhatsApp:
    def test_detecta_codigo_en_el_mensaje_inicial(self):
        state, replies = converse(
            ["Me llegó un código de WhatsApp y alguien me lo está pidiendo"]
        )
        assert state.scenario == "familia"
        assert "codigo_whatsapp" in state.signals
        assert "3/3" in " ".join(r.text for r in replies) or state.question_index == 0

    def test_modo_urgente_al_compartir_codigo(self):
        state, replies = converse(
            [
                "Me llegó un código de WhatsApp y alguien me lo está pidiendo",
                "Sí, es un número nuevo",
                "Me pide un código de WhatsApp",
                "No pude confirmarlo",
                "Sí, compartí un código",
            ]
        )
        assert state.status == States.RECOMENDACION_URGENTE
        assert state.shared_code is True
        assert state.risk_level == RIESGO_CRITICO
        assert "ALERTA URGENTE" in replies[-1].text
        assert "procedimiento oficial de WhatsApp" in replies[-1].text


# ===========================================================================
# CASO 7: situación desconocida (escenario 4)
# ===========================================================================

class TestCaso7SituacionDesconocida:
    def test_boton_otra_situacion(self):
        state, replies = converse(["Tengo otra situación sospechosa"])
        assert state.status == States.CONSULTA_OTRA_SITUACION
        assert "Cuéntame" in replies[0].text

    def test_analiza_y_pregunta_por_entregas(self):
        state, replies = converse(
            [
                "Tengo otra situación sospechosa",
                "Un desconocido me escribió por mensaje diciendo que gané un premio",
            ]
        )
        assert state.awaiting == "generic_compliance"
        text = replies[-1].text
        assert "dinero, claves o códigos" in text

    def test_recomendacion_preventiva_generica(self):
        state, replies = converse(
            [
                "Tengo otra situación sospechosa",
                "Un desconocido me escribió por mensaje diciendo que gané un premio",
                "No, nada todavía",
            ]
        )
        assert state.status == States.RECOMENDACION_PREVENTIVA
        assert "RECOMENDACIÓN PREVENTIVA" in replies[-1].text

    def test_situacion_critica_generica(self):
        state, replies = converse(
            [
                "Tengo otra situación sospechosa",
                "Me piden hacer una transferencia urgente",
                "Sí, ya envié dinero",
            ]
        )
        assert state.status == States.RECOMENDACION_URGENTE
        assert state.risk_level == RIESGO_CRITICO

    def test_no_inventar_si_no_ent(self):
        _state, replies = converse(
            ["Tengo otra situación sospechosa", "Buenos días, ¿cómo están?"]
        )
        assert "no estoy seguro" in replies[-1].text.lower() or "más detalle" in replies[-1].text.lower()


# ===========================================================================
# CASO 8: cómo protegerse de estafas
# ===========================================================================

class TestCaso8Protegerse:
    def test_consejos_generales(self):
        state, replies = converse(["¿Qué puedo hacer para protegerme?"])
        text = replies[0].text
        assert "Nunca compartas tus claves" in text
        assert "códigos de verificación" in text
        assert "enlaces" in text
        assert "demasiado buenas" in text

    def test_funciona_en_cualquier_estado(self):
        state, _ = converse(
            [
                "Me llegó un mensaje del banco",
                "Por WhatsApp",
            ]
        )
        reply = process_message("¿Cómo me protejo de las estafas?", state)
        assert "Nunca compartas tus claves" in reply.text
        # conserva el escenario: se vuelve a la pregunta actual
        assert reply.state.scenario == "banco"
        assert "2/3" in reply.text


# ===========================================================================
# CASO 9: mensajes fuera del contexto de ciberseguridad
# ===========================================================================

class TestCaso9FueraDeContexto:
    def test_respuesta_de_vuelta_al_tema(self):
        state, replies = converse(["Cuéntame un chiste sobre programación"])
        assert "estafas digitales" in replies[0].text
        assert state.status in (States.SELECCION_ESCENARIO, States.INICIO)

    def test_no_inventa_informacion(self):
        _state, replies = converse(["¿Cuál es la capital de Francia?"])
        assert "PilasBot está enfocado" in replies[0].text

    def test_sigue_el_flujo_si_es_tema_sospechoso(self):
        state, _replies = converse(["Creo que me están estafando"])
        assert state.status in (
            States.PREGUNTA_ESCENARIO,
            States.CONSULTA_OTRA_SITUACION,
        )


# ===========================================================================
# CASO 10: reiniciar la conversación
# ===========================================================================

class TestCaso10Reiniciar:
    def test_reiniciar_borra_estado(self):
        state, _replies = converse(
            [
                "Me llegó un enlace del banco",
                "Por SMS",
                "Me pide mi clave",
                "Sí, ya la entregué",
            ]
        )
        assert state.risk_level == RIESGO_CRITICO

        reply = process_message("reiniciar", state)
        assert reply.restart is True
        assert reply.state.status == States.INICIO
        assert reply.state.risk_level == RIESGO_BAJO
        assert reply.state.scenario is None
        assert reply.state.is_critical is False
        assert "PilasBot" in reply.text

    def test_volver_al_menu_sin_borrar_riesgo(self):
        state, _replies = converse(
            [
                "Me llegó un enlace del banco",
                "Por SMS",
                "Me pide mi clave",
                "Sí, ya la entregué",
            ]
        )
        reply = process_message("menú", state)
        assert reply.state.status == States.SELECCION_ESCENARIO
        assert reply.state.risk_level == RIESGO_CRITICO  # se conserva

    def test_botones_de_menu_reinician_escenario(self):
        state, _replies = converse(["Me llegó un enlace del banco"])
        reply = process_message("Me ofrecieron un empleo o una compra/venta en línea", state)
        assert reply.state.scenario == "empleo"
        assert reply.state.question_index == 0


# ===========================================================================
# Intenciones y utilidades
# ===========================================================================

class TestIntenciones:
    def test_mensajes_de_ejemplo_del_documento(self):
        casos = {
            "Me llegó un mensaje del banco": "banco",
            "Creo que me están estafando": "otra",
            "Me ofrecen trabajo y me piden pagar una inscripción": "empleo",
            "Mi mamá me escribió de otro número y necesita dinero": "familia",
            "Me llegó un código de WhatsApp y alguien me lo está pidiendo": "familia",
            "¿Qué puedo hacer para protegerme?": "proteger",
        }
        for texto, esperado in casos.items():
            assert detect_intent(texto) == esperado, texto

    def test_etiquetas_del_menu(self):
        from scenarios import MENU_OPTIONS

        esperados = ["banco", "empleo", "familia", "otra"]
        for etiqueta, esperado in zip(MENU_OPTIONS, esperados):
            assert detect_intent(etiqueta) == esperado

    def test_fuera_de_contexto(self):
        assert is_out_of_context("Cuéntame un chiste")
        assert not is_out_of_context("Me llegó un enlace raro del banco")

    def test_afirmativas_y_negativas(self):
        assert is_affirmative("Sí, ya la entregué")
        assert is_affirmative("Sí, me piden pagar antes")
        assert is_negative("No, todavía no")
        assert is_negative("No pude confirmarlo")
        assert not is_affirmative("No, todavía no")
        assert not is_negative("Sí, lo confirmé")


class TestRiesgo:
    def test_bajo(self):
        assert classify_risk() == RIESGO_BAJO

    def test_medio_por_senales(self):
        assert classify_risk(signals=["urgencia"]) == RIESGO_MEDIO

    def test_medio_por_clic(self):
        assert classify_risk(clicked_link=True) == RIESGO_MEDIO

    def test_critico_por_datos(self):
        assert classify_risk(delivered_data=True) == RIESGO_CRITICO

    def test_critico_por_dinero(self):
        assert classify_risk(delivered_money=True) == RIESGO_CRITICO

    def test_critico_por_codigo(self):
        assert classify_risk(shared_code=True) == RIESGO_CRITICO


class TestSeguridad:
    def test_detecta_tarjeta(self):
        assert contains_sensitive_info("mi tarjeta es 4111 1111 1111 1111")
        assert contains_sensitive_info("4111111111111111")

    def test_detecta_clave(self):
        assert contains_sensitive_info("mi clave es SuperSegura123")
        assert contains_sensitive_info("contraseña: hola123")

    def test_detecta_codigo(self):
        assert contains_sensitive_info("mi código es 123456")

    def test_no_falsa_con_texto_normal(self):
        assert not contains_sensitive_info("Me llegó un mensaje del banco")
        assert not contains_sensitive_info("Mi número es 3001234567")

    def test_no_almacena_lo_sensible(self):
        state, replies = converse(
            [
                "Me llegó un enlace del banco",
                "Por SMS",
                "mi clave es SuperSegura123",
            ]
        )
        assert "SuperSegura123" not in " ".join(state.answers)
        assert "detente" in replies[-1].text.lower() or "sensible" in replies[-1].text.lower()


class TestDeteccionEntrega:
    def test_no_confunde_reporte_con_entrega(self):
        entrego, envio, codigo, _clic = detect_delivery(
            "Me pide que le envíe dinero a una cuenta"
        )
        assert not (entrego or envio or codigo)

    def test_detecta_envio_confirmado(self):
        _entrego, envio, _codigo, _clic = detect_delivery("Sí, ya envié dinero")
        assert envio

    def test_detecta_clave_entregada(self):
        entrego, _e, _c, _k = detect_delivery("Sí, ya la entregué")
        assert entrego

    def test_detecta_codigo_compartido(self):
        _e, _m, codigo, _k = detect_delivery("Sí, compartí un código")
        assert codigo

    def test_entrega_confirmada_sin_escenario_activa_urgente(self):
        # Caso 4: el usuario confiesa una entrega sin haber elegido menú.
        reply = process_message("Ya envié plata a una cuenta que no conozco", None)
        assert reply.state.risk_level == RIESGO_CRITICO
        assert "urgente" in reply.text.lower() or "alerta" in reply.text.lower()

    def test_fuera_de_contexto_acepta_terminos_de_estafa(self):
        # "plata" y "envié" no deben leerse como mensaje ajeno al tema.
        assert not is_out_of_context("Ya envié plata y me estafaron")


class TestRobustez:
    def test_mensaje_vacio(self):
        reply = process_message("", None)
        assert reply.text == ""
        assert reply.state.status == States.INICIO

    def test_no_cr_con_mensajes_varios(self):
        mensajes = [
            "hola",
            "1",
            "gracias",
            "asdfghjkl",
            "???",
            "banco",
            "ok",
            "reiniciar",
        ]
        state = new_state()
        for m in mensajes:
            reply = process_message(m, state)
            assert isinstance(reply.text, str)
            state = reply.state

    def test_menu_numerado(self):
        state, replies = converse(["2"])
        assert state.scenario == "empleo"

    def test_volver_al_menu_desde_flujo(self):
        state, _ = converse(["Me llegó un enlace del banco", "Por SMS"])
        reply = process_message("volver al menú", state)
        assert reply.state.status == States.SELECCION_ESCENARIO

    def test_respuestas_rapidas_siempre_no_vacias(self):
        state = new_state()
        flujo = [
            "Me llegó un mensaje del banco",
            "Por WhatsApp",
            "Me pide mi clave",
            "No, todavía no",
            "Sí, quiero consultar otra",
        ]
        for m in flujo:
            reply = process_message(m, state)
            assert reply.quick_replies, f"sin quick replies para: {m}"
            state = reply.state


class TestComprensionYLimites:
    """Auditoría de respuestas: comprensión, precisión y límites del bot."""

    # ---- Identidad y alcance ----
    def test_quien_eres(self):
        reply = process_message("¿quién eres?", None)
        assert "PilasBot" in reply.text
        assert "no" in reply.text.lower()

    def test_que_puedes_hacer(self):
        reply = process_message("¿qué puedes hacer?", None)
        assert "4 situaciones" in reply.text
        assert "Nunca te voy a pedir claves" in reply.text

    def test_me_puedes_ayudar(self):
        reply = process_message("¿me puedes ayudar?", None)
        assert "PilasBot" in reply.text

    def test_no_se_que_hacer_ofrece_menu(self):
        reply = process_message("no sé qué hacer", None)
        assert "Soy PilasBot" in reply.text
        assert reply.state.status == States.SELECCION_ESCENARIO

    def test_despedida(self):
        reply = process_message("adiós", None)
        assert "Cuídate" in reply.text

    # ---- Falsos positivos corregidos ----
    def test_cuenta_de_facebook_no_es_escenario_banco(self):
        reply = process_message("me robaron la cuenta de facebook", None)
        assert reply.state.scenario == "otra"

    def test_clima_no_entra_al_escenario_banco(self):
        reply = process_message("qué tiempo hace en Bogotá", None)
        assert "estafas digitales" in reply.text
        assert reply.state.scenario is None

    def test_correo_del_dian_se_analiza_como_estafa(self):
        reply = process_message("me llegó un correo del dian pidiendo datos", None)
        assert reply.state.status == States.CONSULTA_OTRA_SITUACION

    def test_clonacion_de_cedula_no_es_fuera_de_contexto(self):
        msg = "tengo miedo de que me clonen la cédula"
        assert not is_out_of_context(msg)
        assert process_message(msg, None).state.scenario == "otra"

    def test_link_raro_no_es_fuera_de_contexto(self):
        msg = "me llegó un link raro"
        assert not is_out_of_context(msg)
        assert process_message(msg, None).state.scenario == "otra"

    # ---- Límites de seguridad y certeza ----
    def test_rechaza_transferir_dinero(self):
        reply = process_message("¿puedes transferirme dinero?", None)
        assert "No puedo hacer eso" in reply.text
        assert reply.state.scenario is None

    def test_rechaza_dar_claves(self):
        reply = process_message("dime mi clave del banco", None)
        assert "No doy claves" in reply.text or "No puedo hacer eso" in reply.text
        assert reply.state.scenario is None

    def test_reconoce_limite_de_certeza(self):
        reply = process_message("¿esto es una estafa seguro?", None)
        assert "no puedo darte esa garantía" in reply.text.lower()

    def test_no_garantiza_que_no_sea_fraude(self):
        reply = process_message("¿me garantizas que no es fraude?", None)
        assert "certeza" in reply.text.lower()

    # ---- Coherencia de los flujos existentes ----
    def test_identidad_durante_escenario_conserva_pregunta(self):
        state, _ = converse(["Me llegó un enlace del banco"])
        reply = process_message("¿quién eres?", state)
        assert "PilasBot" in reply.text
        assert reply.state.status == state.status


if __name__ == "__main__":
    import pytest

    raise SystemExit(pytest.main([__file__, "-v"]))
