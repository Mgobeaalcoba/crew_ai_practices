"""Agente que ejecuta código Python en un contenedor Docker aislado.

Hasta crewai 0.x esto se hacía con `Agent(allow_code_execution=True)`. En 1.15 ese parámetro está deprecado
y la herramienta que usaba (CodeInterpreterTool) ya no existe: CrewAI recomienda un sandbox dedicado.
Este ejemplo arma ese sandbox con una herramienta propia que lanza un contenedor descartable:

- sin red (`--network none`), con memoria, CPU y procesos limitados;
- sistema de archivos de solo lectura;
- se destruye al terminar (`--rm`) y se corta a los 20 segundos.

Nunca ejecutes código generado por un LLM directamente en tu máquina.

Requiere Docker encendido y una imagen con Python (por defecto `python:3.12-slim`, se descarga sola la
primera vez; se cambia con SANDBOX_IMAGEN en .env).

Uso:
    uv run main.py ejecucion_de_codigo "¿Cuántos números primos hay entre 1 y 10.000?"
"""

import os
import subprocess
import sys

from crewai import Agent
from crewai.tools import ToolFailure, tool

from comun import crear_llm, describir_llm

IMAGEN = os.getenv("SANDBOX_IMAGEN", "python:3.12-slim")
TIEMPO_MAXIMO = 20


def ejecutar_en_docker(codigo: str) -> tuple[int, str]:
    comando = [
        "docker", "run", "--rm", "-i",
        "--network", "none", "--memory", "256m", "--cpus", "1", "--pids-limit", "64", "--read-only",
        "--entrypoint", "python", IMAGEN, "-",  # "-": Python lee el programa de la entrada estándar
    ]
    try:
        proceso = subprocess.run(comando, input=codigo, capture_output=True, text=True, timeout=TIEMPO_MAXIMO)
    except subprocess.TimeoutExpired:
        return 124, f"Se cortó la ejecución a los {TIEMPO_MAXIMO} segundos."
    return proceso.returncode, (proceso.stdout + proceso.stderr).strip()[-3000:]


@tool("ejecutar_python")
def ejecutar_python(codigo: str) -> str | ToolFailure:
    """Ejecuta un programa de Python 3.12 (solo biblioteca estándar, sin red ni archivos) y devuelve lo que
    imprime. Usá print() para ver resultados: el valor de la última línea no se muestra solo."""
    codigo_salida, salida = ejecutar_en_docker(codigo)
    if codigo_salida != 0:
        return ToolFailure(message=f"El programa falló (código {codigo_salida}):\n{salida}")
    return salida or "(el programa no imprimió nada: usá print)"


def construir_agente(llm=None) -> Agent:
    return Agent(
        role="Analista de datos",
        goal="Responder preguntas numéricas calculando con código, nunca estimando",
        backstory="Para cualquier cálculo escribe un programa corto, lo ejecuta con ejecutar_python y reporta el resultado.",
        llm=llm or crear_llm(0.0),
        tools=[ejecutar_python],
        max_iter=5,
        verbose=True,
    )


def main() -> int:
    pregunta = " ".join(sys.argv[1:]) or "¿Cuántos números primos hay entre 1 y 10.000, y cuál es el más grande?"
    print(f"LLM: {describir_llm()} · imagen: {IMAGEN}\n")
    print(f"\n=== Respuesta ===\n{construir_agente().kickoff(pregunta).raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
