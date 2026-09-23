"""Crew secuencial: cada tarea se ejecuta en orden y recibe las salidas anteriores como contexto.

Es el proceso por defecto (`Process.sequential`). El flujo lo decidís vos al ordenar las tareas.

    idea ──► guion ──► título

Uso:
    uv run main.py secuencial "cómo ahorrar agua en casa"
"""

import sys

from crewai import Agent, Crew, Process, Task

from comun import crear_llm, describir_llm


def construir_crew(tema: str, llm=None) -> Crew:
    llm = llm or crear_llm(0.6)
    creativo = Agent(role="Creativo", goal="Proponer enfoques originales para videos cortos",
                     backstory="Piensa en lo que engancha en los primeros 3 segundos.", llm=llm)
    guionista = Agent(role="Guionista", goal="Convertir una idea en un guion de 30 segundos",
                      backstory="Escribe frases cortas, habladas, con una sola idea por escena.", llm=llm)
    editor = Agent(role="Editor de títulos", goal="Escribir títulos breves que den ganas de ver el video",
                   backstory="Nunca usa clickbait engañoso.", llm=llm)

    idea = Task(description=f"Proponé UNA idea para un video corto sobre: {tema}.",
                expected_output="La idea en dos oraciones.", agent=creativo)
    guion = Task(description="Escribí el guion del video a partir de la idea.",
                 expected_output="Un guion de 4 a 6 escenas numeradas.", agent=guionista)
    # context explícito: el título mira la idea y el guion. Sin `context`, en un proceso secuencial cada tarea
    # recibe automáticamente la salida de la anterior.
    titulo = Task(description="Escribí 3 títulos posibles para el video.",
                  expected_output="Una lista de 3 títulos de menos de 60 caracteres.",
                  agent=editor, context=[idea, guion])

    return Crew(agents=[creativo, guionista, editor], tasks=[idea, guion, titulo],
                process=Process.sequential, verbose=True)


def main() -> int:
    tema = " ".join(sys.argv[1:]) or "cómo ahorrar agua en casa"
    print(f"LLM: {describir_llm()}\n")
    salida = construir_crew(tema).kickoff()
    for tarea in salida.tasks_output:
        print(f"\n=== {tarea.agent} ===\n{tarea.raw}")
    print(f"\nTokens usados: {salida.token_usage.total_tokens}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
