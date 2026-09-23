"""Ejecutar el mismo Crew muchas veces: variables en los textos, `kickoff_for_each` y ejecución asíncrona.

- Los textos de agentes y tareas pueden tener `{variables}` que se completan con `kickoff(inputs={...})`.
  Así un Crew es una plantilla reutilizable.
- `kickoff_for_each(inputs=[...])` lo corre una vez por cada dict, en secuencia.
- `kickoff_async` / `akickoff` lo corren sin bloquear; con asyncio.gather, varias corridas en paralelo.

Uso:
    uv run main.py ejecucion_multiple
"""

import asyncio
import sys

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm

CIUDADES = [{"ciudad": "Salta"}, {"ciudad": "Ushuaia"}, {"ciudad": "Mendoza"}]


def construir_crew(llm=None) -> Crew:
    guia = Agent(role="Guía de turismo de {ciudad}", goal="Recomendar planes auténticos en {ciudad}",
                 backstory="Nació en {ciudad} y conoce lo que no figura en las guías.", llm=llm or crear_llm(0.5))
    plan = Task(description="Recomendá un plan de un día en {ciudad}.",
                expected_output="Mañana, tarde y noche, una línea cada una.", agent=guia)
    return Crew(agents=[guia], tasks=[plan])


async def en_paralelo(llm=None) -> list:
    # Un Crew por corrida: una misma instancia no debe ejecutarse dos veces a la vez
    return await asyncio.gather(*(construir_crew(llm).kickoff_async(inputs=i) for i in CIUDADES))


def main() -> int:
    print(f"LLM: {describir_llm()}\n")

    print("=== 1. kickoff con inputs ===")
    print(construir_crew().kickoff(inputs={"ciudad": "Córdoba"}).raw)

    print("\n=== 2. kickoff_for_each (en secuencia) ===")
    for entrada, salida in zip(CIUDADES, construir_crew().kickoff_for_each(inputs=CIUDADES)):
        print(f"\n--- {entrada['ciudad']} ---\n{salida.raw}")

    print("\n=== 3. kickoff_async + asyncio.gather (en paralelo) ===")
    for entrada, salida in zip(CIUDADES, asyncio.run(en_paralelo())):
        print(f"\n--- {entrada['ciudad']} ---\n{salida.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
