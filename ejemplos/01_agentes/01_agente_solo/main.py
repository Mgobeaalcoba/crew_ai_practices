"""Agente solo: un Agent que responde sin Crew ni Task.

Uso:
    uv run main.py agente_solo "¿Qué es un agente de IA?"
"""

import sys

from crewai import Agent
from pydantic import BaseModel, Field

from comun import crear_llm, describir_llm


class Definicion(BaseModel):
    termino: str
    definicion: str = Field(description="Una o dos oraciones, sin tecnicismos")
    ejemplo: str = Field(description="Un ejemplo cotidiano")


def construir_agente(llm=None) -> Agent:
    return Agent(
        role="Profesor de tecnología",
        goal="Explicar conceptos técnicos a personas sin formación técnica",
        backstory="Docente de secundaria. Usa ejemplos cotidianos y evita la jerga.",
        llm=llm or crear_llm(0.3),
        inject_date=True,  # agrega la fecha de hoy al prompt: útil si la pregunta depende del momento
        verbose=True,
    )


def preguntar(agente: Agent, pregunta: str) -> str:
    return agente.kickoff(pregunta).raw


def definir(agente: Agent, termino: str) -> Definicion:
    # response_format le pide al agente una salida que cumpla el modelo Pydantic y la valida
    salida = agente.kickoff(f"Definí el término: {termino}", response_format=Definicion)
    return salida.pydantic


def main() -> int:
    pregunta = " ".join(sys.argv[1:]) or "¿Qué es un agente de IA?"
    print(f"LLM: {describir_llm()}\n")
    agente = construir_agente()

    print(f"\n=== Respuesta libre ===\n{preguntar(agente, pregunta)}\n")

    definicion = definir(agente, "agente de IA")
    print("=== Respuesta estructurada (Pydantic) ===")
    print(definicion.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
