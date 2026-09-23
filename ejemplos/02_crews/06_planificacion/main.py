"""Crew con planificación: antes de empezar, un "planificador" escribe un plan paso a paso para cada tarea.

Con `planning=True`, CrewAI crea un agente AgentPlanner que lee todas las tareas y agrega a la descripción
de cada una un plan detallado. Mejora la coherencia en crews largos, a costa de una llamada más al LLM.

Es distinto de `planning_config` en un Agent (ejemplo 01/06): aquello planifica los pasos de UN agente
dentro de su tarea; esto planifica el Crew entero antes de arrancar.

Uso:
    uv run main.py 02_crews/06_planificacion
"""

import sys

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm


def construir_crew(llm=None, llm_planificador=None) -> Crew:
    llm = llm or crear_llm(0.4)
    docente = Agent(role="Docente de programación", goal="Diseñar clases prácticas para principiantes",
                    backstory="Enseña Python a adolescentes con ejemplos de videojuegos.", llm=llm)
    temario = Task(description="Armá el temario de una clase de 40 minutos sobre bucles for en Python.",
                   expected_output="Un temario con bloques y minutos.", agent=docente)
    ejercicio = Task(description="Escribí un ejercicio práctico para esa clase, con su solución.",
                     expected_output="Enunciado y solución en Python.", agent=docente)
    return Crew(agents=[docente], tasks=[temario, ejercicio], planning=True,
                planning_llm=llm_planificador or crear_llm(0.0), verbose=True)


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    crew = construir_crew()
    salida = crew.kickoff()
    print("\n=== Descripción final de la 1ª tarea (con el plan agregado) ===")
    print(crew.tasks[0].description)
    print(f"\n=== Ejercicio ===\n{salida.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
