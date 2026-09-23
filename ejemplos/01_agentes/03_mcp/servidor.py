"""Servidor MCP mínimo: una biblioteca con tres herramientas.

MCP (Model Context Protocol) es un estándar para exponer herramientas a cualquier cliente de IA. Este
servidor no sabe nada de CrewAI: lo mismo lo puede usar Claude Desktop, un IDE u otro framework.

Se comunica por stdio (entrada/salida estándar), así que el cliente lo lanza como subproceso:
    python ejemplos/01_agentes/03_mcp/servidor.py
"""

import json

from mcp.server.fastmcp import FastMCP

LIBROS = {
    "978-950-07-0001": {"titulo": "Rayuela", "autor": "Julio Cortázar", "anio": 1963, "disponible": True},
    "978-950-07-0002": {"titulo": "Ficciones", "autor": "Jorge Luis Borges", "anio": 1944, "disponible": False},
    "978-950-07-0003": {"titulo": "El Aleph", "autor": "Jorge Luis Borges", "anio": 1949, "disponible": True},
    "978-950-07-0004": {"titulo": "Bestiario", "autor": "Julio Cortázar", "anio": 1951, "disponible": True},
}

servidor = FastMCP("biblioteca")


@servidor.tool()
def buscar_por_autor(autor: str) -> str:
    """Lista los libros de un autor (búsqueda parcial, sin distinguir mayúsculas), con ISBN y disponibilidad."""
    libros = [{"isbn": isbn, **libro} for isbn, libro in LIBROS.items() if autor.lower() in libro["autor"].lower()]
    # Se devuelve un solo texto JSON y no una lista: FastMCP convierte cada elemento de una lista en un bloque
    # de contenido aparte, y crewai 1.15.20 solo lee el primero (el agente vería un único libro).
    return json.dumps(libros, ensure_ascii=False)


@servidor.tool()
def consultar_libro(isbn: str) -> dict:
    """Devuelve los datos de un libro por su ISBN."""
    if isbn not in LIBROS:
        raise ValueError(f"No existe el ISBN {isbn}")
    return {"isbn": isbn, **LIBROS[isbn]}


@servidor.tool()
def reservar(isbn: str) -> str:
    """Reserva un libro disponible. Falla si no existe o si ya está prestado."""
    libro = LIBROS.get(isbn)
    if libro is None or not libro["disponible"]:
        raise ValueError(f"El libro {isbn} no se puede reservar")
    libro["disponible"] = False
    return f"Reservado: {libro['titulo']}"


if __name__ == "__main__":
    servidor.run()  # transporte stdio por defecto
