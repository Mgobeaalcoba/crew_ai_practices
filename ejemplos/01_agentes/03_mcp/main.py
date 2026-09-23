"""Agente con herramientas MCP: las herramientas viven en otro proceso (servidor.py).

CrewAI lanza el servidor, le pide la lista de herramientas y se las da al agente como si fueran propias.
El filtro deja afuera `reservar`: el agente solo puede consultar, no modificar.

Uso:
    uv run main.py mcp "¿Qué libros de Borges hay disponibles?"
"""

import os
import sys
from pathlib import Path

from crewai import Agent
from crewai.mcp import MCPServerStdio
from crewai.mcp.filters import create_static_tool_filter

from comun import crear_llm, describir_llm

SERVIDOR = Path(__file__).with_name("servidor.py")


def configurar_servidor(permitir_reservas: bool = False) -> MCPServerStdio:
    permitidas = ["buscar_por_autor", "consultar_libro"] + (["reservar"] if permitir_reservas else [])
    return MCPServerStdio(
        # CrewAI nombra cada herramienta "<comando>_<args>_<herramienta>" y trunca a 64 caracteres con un hash.
        # Con un camino absoluto el nombre real se pierde, así que se usan "python" (dentro de `uv run` es el del
        # entorno virtual, que tiene el paquete `mcp`) y un camino relativo.
        command="python",
        args=[os.path.relpath(SERVIDOR)],
        tool_filter=create_static_tool_filter(allowed_tool_names=permitidas),
        cache_tools_list=True,
    )


def construir_agente(llm=None, permitir_reservas: bool = False) -> Agent:
    return Agent(
        role="Bibliotecario",
        goal="Responder consultas sobre el catálogo usando solo las herramientas de la biblioteca",
        backstory="Antes de responder busca en el catálogo. Si un libro no figura, lo dice.",
        llm=llm or crear_llm(0.0),
        mcps=[configurar_servidor(permitir_reservas)],
        verbose=True,
    )


def main() -> int:
    pregunta = " ".join(sys.argv[1:]) or "¿Qué libros de Borges hay disponibles para llevar?"
    print(f"LLM: {describir_llm()}\n")
    respuesta = construir_agente().kickoff(pregunta)
    print(f"\n=== Respuesta ===\n{respuesta.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
