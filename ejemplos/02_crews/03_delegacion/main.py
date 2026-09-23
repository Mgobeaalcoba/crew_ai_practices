"""Delegación entre agentes: un agente con `allow_delegation=True` puede pedirle ayuda a sus compañeros.

CrewAI le da dos herramientas extra: "Delegate work to coworker" y "Ask question to coworker". El agente
decide solo cuándo usarlas. Sirve cuando una tarea mezcla saberes y no querés partirla a mano.

A diferencia del jerárquico, acá no hay manager: el proceso es secuencial y la delegación es opcional.

Uso:
    uv run main.py delegacion
"""

import sys

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm


def construir_crew(llm=None) -> Crew:
    llm = llm or crear_llm(0.3)
    responsable = Agent(
        role="Responsable de producto",
        goal="Escribir fichas de producto completas y correctas",
        backstory="No es experto en nutrición: cualquier dato nutricional se lo consulta a la nutricionista.",
        llm=llm,
        allow_delegation=True,
    )
    nutricionista = Agent(
        role="Nutricionista",
        goal="Dar información nutricional precisa y prudente",
        backstory="Responde con rangos típicos y aclara que no reemplaza una consulta médica.",
        llm=llm,
        allow_delegation=False,  # evita que se devuelvan la pelota entre ellos
    )
    ficha = Task(
        description="Escribí la ficha de venta de una granola con almendras y miel, con un apartado nutricional.",
        expected_output="Una ficha con descripción, beneficios y apartado nutricional.",
        agent=responsable,
    )
    return Crew(agents=[responsable, nutricionista], tasks=[ficha], verbose=True)


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    print(f"\n=== Ficha ===\n{construir_crew().kickoff().raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
