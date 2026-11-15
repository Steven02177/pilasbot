# -*- coding: utf-8 -*-
"""
Gestión del estado conversacional de PilasBot.

Máquina de estados que conserva:
  - Escenario seleccionado.
  - Pregunta actual.
  - Respuestas anteriores.
  - Nivel de riesgo.
  - Si el usuario entregó datos, dinero o códigos.
  - Estado general de la conversación.

Estados (sección 6 del documento):
  INICIO -> SELECCION_ESCENARIO -> PREGUNTA_ESCENARIO -> ANALISIS ->
  RECOMENDACION_PREVENTIVA | RECOMENDACION_URGENTE -> CONSULTA_OTRA_SITUACION -> FIN
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Optional

from risk_analyzer import RIESGO_BAJO, classify_risk, merge_risk


class States:
    """Estados de la máquina de estados conversacional."""

    INICIO = "INICIO"
    SELECCION_ESCENARIO = "SELECCION_ESCENARIO"
    PREGUNTA_ESCENARIO = "PREGUNTA_ESCENARIO"
    ANALISIS = "ANALISIS"
    RECOMENDACION_PREVENTIVA = "RECOMENDACION_PREVENTIVA"
    RECOMENDACION_URGENTE = "RECOMENDACION_URGENTE"
    CONSULTA_OTRA_SITUACION = "CONSULTA_OTRA_SITUACION"
    FIN = "FIN"


# Sub-fases de espera (qué espera el chatbot en este momento)
AWAIT_NONE = ""                 # sin espera activa
AWAIT_SCENARIO_QUESTION = "scenario_question"   # respuesta a la pregunta actual
AWAIT_CLARIFY_CLICK = "clarify_click"           # ¿solo clic o entregó datos?
AWAIT_COMPLIANCE = "compliance"                 # ¿ya entregó dinero/códigos?
AWAIT_GENERIC_DESCRIBE = "generic_describe"     # descripción libre
AWAIT_GENERIC_COMPLIANCE = "generic_compliance"  # ¿entregó algo en lo genérico?


@dataclass
class ConversationState:
    """Estado completo de la conversación de un usuario."""

    status: str = States.INICIO
    scenario: Optional[str] = None            # banco | empleo | familia | otra
    question_index: int = 0                   # índice de la pregunta activa
    answers: List[str] = field(default_factory=list)
    risk_level: str = RIESGO_BAJO
    delivered_data: bool = False
    delivered_money: bool = False
    shared_code: bool = False
    clicked_link: bool = False
    signals: List[str] = field(default_factory=list)
    awaiting: str = AWAIT_NONE
    generic_attempts: int = 0                 # intentos de comprender lo genérico
    started: bool = False                     # si ya recibió el saludo

    # ------------------------------------------------------------------
    def update(self, **kwargs) -> "ConversationState":
        """Devuelve una copia actualizada del estado (inmutable para la UI)."""
        return replace(self, **kwargs)

    # ------------------------------------------------------------------
    def add_signal(self, signal_id: str) -> "ConversationState":
        """Agrega una señal de alerta si aún no estaba registrada."""
        if signal_id in self.signals:
            return self
        return self.update(signals=self.signals + [signal_id])

    # ------------------------------------------------------------------
    def add_signals(self, signal_ids: List[str]) -> "ConversationState":
        """Agrega varias señales descartando duplicadas."""
        state = self
        for sig in signal_ids:
            state = state.add_signal(sig)
        return state

    # ------------------------------------------------------------------
    def register_compromise(
        self,
        data: bool = False,
        money: bool = False,
        code: bool = False,
        clicked: bool = False,
    ) -> "ConversationState":
        """Marca entregas confirmadas y recalcula el nivel de riesgo."""
        state = self.update(
            delivered_data=self.delivered_data or data,
            delivered_money=self.delivered_money or money,
            shared_code=self.shared_code or code,
            clicked_link=self.clicked_link or clicked,
        )
        return state.recompute_risk()

    # ------------------------------------------------------------------
    def recompute_risk(self) -> "ConversationState":
        """Recalcula el riesgo conservando siempre el nivel más alto."""
        new_risk = classify_risk(
            delivered_data=self.delivered_data,
            delivered_money=self.delivered_money,
            shared_code=self.shared_code,
            clicked_link=self.clicked_link,
            signals=self.signals,
        )
        return self.update(risk_level=merge_risk(self.risk_level, new_risk))

    # ------------------------------------------------------------------
    @property
    def is_critical(self) -> bool:
        return self.delivered_data or self.delivered_money or self.shared_code

    # ------------------------------------------------------------------
    def reset(self) -> "ConversationState":
        """Vuelve al estado inicial (reiniciar conversación)."""
        return new_state()


def new_state() -> ConversationState:
    """Crea un estado nuevo (INICIO)."""
    return ConversationState()


def initial_history(greeting: str) -> List[dict]:
    """Historial inicial de Gradio (formato mensajes)."""
    return [{"role": "assistant", "content": greeting}]
