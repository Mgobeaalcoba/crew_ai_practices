"""Proyecto con YAML: agentes y tareas definidos en archivos de configuración en vez de en Python.

    08_proyecto_yaml/
    ├── config/agents.yaml   qué agentes hay (rol, objetivo, historia)
    ├── config/tasks.yaml    qué tareas hay y quién las hace
    ├── crew.py              la clase @CrewBase que los arma
    └── main.py              el punto de entrada (este archivo)

Separar textos de código permite ajustar prompts sin tocar Python, y es el formato que usa la CLI
(`crewai create crew`) y la plataforma CrewAI AMP.

Uso:
    uv run main.py proyecto_yaml "una bicicleta eléctrica plegable"
"""

import sys

from comun import describir_llm

from .crew import CrewSlogans


def main() -> int:
    producto = " ".join(sys.argv[1:])
    print(f"LLM: {describir_llm()}\n")
    salida = CrewSlogans().crew().kickoff(inputs={"producto": producto})
    print(f"\n=== Slogans ===\n{salida.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
