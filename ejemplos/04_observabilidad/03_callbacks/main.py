"""Callbacks: funciones que el Crew llama en momentos puntuales de su ejecución.

Son la forma más simple de engancharse, sin bus de eventos ni hooks globales:

- `Task(callback=f)`: al terminar esa tarea, con su TaskOutput. Ej.: guardar cada resultado.
- `Crew(task_callback=f)`: al terminar cualquier tarea del Crew.
- `Crew(step_callback=f)`: después de cada paso de razonamiento de cualquier agente. Ojo: en 1.15 solo
  funciona con `executor_class=CrewAgentExecutor`; el ejecutor por defecto lo ignora sin avisar.
- `Crew(before_kickoff_callbacks=[...])`: reciben y pueden modificar los inputs antes de arrancar.
- `Crew(after_kickoff_callbacks=[...])`: reciben y pueden modificar la salida final.

Uso:
    uv run main.py callbacks
"""

import sys

from crewai import Agent, Crew, Task
from crewai.agents.crew_agent_executor import CrewAgentExecutor

from comun import crear_llm, describir_llm


def construir_crew(bitacora: list[str], llm=None) -> Crew:
    llm = llm or crear_llm(0.4)
    chef = Agent(role="Chef", goal="Proponer recetas simples con {ingrediente}", backstory="Cocina casera.", llm=llm,
                 executor_class=CrewAgentExecutor)  # el ejecutor por defecto no llama a step_callback

    receta = Task(
        description="Proponé una receta con {ingrediente} en 5 pasos.",
        expected_output="Nombre y 5 pasos numerados.",
        agent=chef,
        callback=lambda salida: bitacora.append(f"[task.callback] receta lista ({len(salida.raw)} caracteres)"),
    )

    def normalizar_inputs(inputs: dict) -> dict:
        bitacora.append(f"[before_kickoff] inputs originales: {inputs}")
        return {**inputs, "ingrediente": inputs["ingrediente"].strip().lower()}

    def agregar_firma(salida):
        bitacora.append("[after_kickoff] se agregó la firma")
        salida.raw += "\n\n— Recetario del repo crew-practices"
        return salida

    return Crew(
        agents=[chef],
        tasks=[receta],
        before_kickoff_callbacks=[normalizar_inputs],
        after_kickoff_callbacks=[agregar_firma],
        task_callback=lambda salida: bitacora.append(f"[crew.task_callback] terminó: {salida.agent}"),
        step_callback=lambda paso: bitacora.append(f"[step_callback] {type(paso).__name__}"),
    )


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    bitacora: list[str] = []
    salida = construir_crew(bitacora).kickoff(inputs={"ingrediente": "  ZAPALLO  "})
    print(f"\n=== Receta ===\n{salida.raw}\n\n=== Bitácora de callbacks (en orden) ===")
    print("\n".join(bitacora))
    return 0


if __name__ == "__main__":
    sys.exit(main())
