"""El mismo agente sobre distintos proveedores de LLM: nube (Groq, OpenAI, Anthropic, Gemini) y local
(LM Studio, Ollama).

Para CrewAI el proveedor es solo el objeto `LLM` que le pasás al agente: roles, tareas y herramientas no
cambian. Este ejemplo detecta qué proveedores tenés disponibles (key en .env o servidor local encendido),
les hace la misma pregunta y compara respuesta y tiempo.

Uso:
    uv run main.py comparar_proveedores
    uv run main.py comparar_proveedores groq lmstudio      # solo esos
"""

import json
import os
import sys
import time
import urllib.request

from crewai import Agent

from comun import PROVEEDORES, crear_llm
from comun.llm import resolver

PREGUNTA = "En una sola oración: ¿qué es un agente de IA?"


def modelos_locales(base_url: str) -> list[str]:
    try:
        with urllib.request.urlopen(f"{base_url.rstrip('/')}/models", timeout=2) as respuesta:
            return [m["id"] for m in json.load(respuesta)["data"]]
    except (OSError, ValueError, KeyError):
        return []


def disponibilidad(nombre: str) -> tuple[bool, str, str | None]:
    """Devuelve (disponible, motivo, modelo a usar)."""
    config = PROVEEDORES[nombre]
    if config.variable_key:
        if not os.getenv(config.variable_key):
            return False, f"falta {config.variable_key} en .env", None
        try:
            return True, "", resolver(nombre)[2]
        except ValueError as error:
            return False, str(error), None
    # Servidor local: tiene que estar encendido y ofrecer un modelo de chat (no de embeddings)
    modelos = [m for m in modelos_locales(config.base_url) if "embed" not in m]
    if not modelos:
        return False, f"sin servidor o sin modelo de chat en {config.base_url}", None
    preferido = (os.getenv("LLM_MODELO") if os.getenv("LLM_PROVEEDOR") == nombre else None) or config.modelo_por_defecto
    return True, "", preferido if preferido in modelos else modelos[0]


def preguntar(nombre: str, modelo: str, llm=None) -> tuple[str, float]:
    agente = Agent(role="Divulgador", goal="Explicar conceptos en pocas palabras", backstory="Claro y breve.",
                   llm=llm or crear_llm(0.2, proveedor=nombre, modelo=modelo))
    inicio = time.perf_counter()
    respuesta = agente.kickoff(PREGUNTA).raw
    return respuesta, time.perf_counter() - inicio


def main() -> int:
    elegidos = sys.argv[1:] or list(PROVEEDORES)
    print(f"Pregunta: {PREGUNTA}\n")
    for nombre in elegidos:
        ok, motivo, modelo = disponibilidad(nombre)
        if not ok:
            print(f"· {nombre:<10} omitido: {motivo}")
            continue
        try:
            respuesta, segundos = preguntar(nombre, modelo)
            print(f"· {nombre:<10} {modelo} ({segundos:.1f} s)\n  {respuesta.strip()}\n")
        except Exception as error:  # un proveedor caído no debe frenar la comparación
            print(f"· {nombre:<10} {modelo} ERROR: {str(error)[:200]}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
