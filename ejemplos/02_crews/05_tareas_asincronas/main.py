"""Tareas asíncronas: varias tareas independientes corren en paralelo y una final junta los resultados.

`async_execution=True` hace que el Crew no espere a esa tarea para arrancar la siguiente. La tarea que
necesita los resultados los pide con `context=[...]`, y ahí sí se espera a que terminen.

    ventajas ─┐
              ├──► recomendación
    riesgos  ─┘

Uso:
    uv run main.py asincronas "migrar el sistema de facturación a la nube"
"""

import sys
import time

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm


def construir_crew(decision: str, llm=None) -> Crew:
    llm = llm or crear_llm(0.3)
    optimista = Agent(role="Analista optimista", goal="Encontrar beneficios concretos", backstory="Busca oportunidades.", llm=llm)
    pesimista = Agent(role="Analista de riesgos", goal="Encontrar riesgos concretos", backstory="Piensa en lo que puede salir mal.", llm=llm)
    director = Agent(role="Director", goal="Tomar decisiones equilibradas", backstory="Pesa pros y contras.", llm=llm)

    ventajas = Task(description=f"Listá 3 ventajas de: {decision}", expected_output="3 viñetas.",
                    agent=optimista, async_execution=True)
    riesgos = Task(description=f"Listá 3 riesgos de: {decision}", expected_output="3 viñetas.",
                   agent=pesimista, async_execution=True)
    recomendacion = Task(description="Con las ventajas y los riesgos, recomendá si avanzar y cómo.",
                         expected_output="Una recomendación de un párrafo.", agent=director,
                         context=[ventajas, riesgos])  # espera a las dos
    return Crew(agents=[optimista, pesimista, director], tasks=[ventajas, riesgos, recomendacion])


def main() -> int:
    decision = " ".join(sys.argv[1:]) or "migrar el sistema de facturación a la nube"
    print(f"LLM: {describir_llm()}\n")
    inicio = time.perf_counter()
    salida = construir_crew(decision).kickoff()
    for tarea in salida.tasks_output:
        print(f"\n=== {tarea.agent} ===\n{tarea.raw}")
    print(f"\nTiempo total: {time.perf_counter() - inicio:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
