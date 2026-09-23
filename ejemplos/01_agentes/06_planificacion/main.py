"""Agente que planifica: antes de actuar arma un plan de pasos, y después lo ejecuta.

`planning_config` reemplaza a los parámetros `reasoning` y `max_reasoning_attempts`, deprecados en 1.15.
`reasoning_effort` regula cuánto se observa y se re-planifica después de cada paso:

- "low":    ejecuta el plan sin revisar cada paso con el LLM (más rápido, menos tokens).
- "medium": revisa cada paso; si uno falla, re-planifica.
- "high":   revisa cada paso y además puede terminar antes, re-planificar o refinar el plan.

Uso:
    uv run main.py planificacion
    uv run main.py planificacion high
"""

import sys

from crewai import Agent
from crewai.agent.planning_config import PlanningConfig
from crewai.tools import tool

from comun import crear_llm, describir_llm

TEMPERATURAS = {"lunes": 18, "martes": 22, "miércoles": 25, "jueves": 19, "viernes": 15}


@tool("temperatura_maxima")
def temperatura_maxima(dia: str) -> str:
    """Devuelve la temperatura máxima pronosticada (°C) para un día hábil de esta semana (lunes a viernes)."""
    grados = TEMPERATURAS.get(dia.strip().lower())
    return f"{dia}: {grados} °C" if grados is not None else f"Sin pronóstico para '{dia}'"


def construir_agente(llm=None, esfuerzo: str = "low") -> Agent:
    return Agent(
        role="Organizador de eventos",
        goal="Elegir el mejor día para un evento al aire libre según el pronóstico",
        backstory="Metódico: consulta todos los datos antes de decidir y justifica la elección.",
        llm=llm or crear_llm(0.0),
        tools=[temperatura_maxima],
        planning_config=PlanningConfig(reasoning_effort=esfuerzo, max_steps=6),
        verbose=True,
    )


def main() -> int:
    esfuerzo = sys.argv[1] if len(sys.argv) > 1 else "low"
    print(f"LLM: {describir_llm()} · reasoning_effort={esfuerzo}\n")
    pedido = "Elegí el día hábil de esta semana con la máxima más cercana a 21 °C para un picnic, y explicá por qué."
    respuesta = construir_agente(esfuerzo=esfuerzo).kickoff(pedido)
    print(f"\n=== Decisión ===\n{respuesta.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
