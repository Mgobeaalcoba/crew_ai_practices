"""Hooks: código propio que corre antes y después de cada llamada al LLM o a una herramienta.

Los hooks pueden *modificar* la ejecución (a diferencia de los eventos, que solo observan):

- `@before_llm_call`: ver o editar los mensajes antes de mandarlos. Devolver False cancela la llamada.
- `@after_llm_call`: ver o reemplazar la respuesta (devolviendo un string).
- `@before_tool_call`: validar argumentos o bloquear la herramienta (devolviendo False).
- `@after_tool_call`: ver o reemplazar el resultado de la herramienta.

Se registran en forma global (afectan a todos los agentes), y se pueden filtrar por agente o herramienta.
Este ejemplo usa tres casos típicos: contar llamadas, bloquear una herramienta peligrosa y enmascarar datos.

Uso:
    uv run main.py hooks
"""

import re
import sys

from crewai import Agent
from crewai.hooks import (
    after_tool_call,
    before_llm_call,
    before_tool_call,
    clear_all_global_hooks,
)
from crewai.tools import tool

from comun import crear_llm, describir_llm

CLIENTES = {"123": "Laura Gómez, DNI 30.456.789, tel. 11-5555-1234", "456": "Pedro Ruiz, DNI 25.111.222"}
estadisticas = {"llamadas_llm": 0, "herramientas_bloqueadas": 0}


@tool("buscar_cliente")
def buscar_cliente(numero: str) -> str:
    """Devuelve los datos de un cliente a partir de su número de cliente."""
    return CLIENTES.get(numero, "No existe ese cliente")


@tool("borrar_cliente")
def borrar_cliente(numero: str) -> str:
    """Borra un cliente de la base de datos. Irreversible."""
    CLIENTES.pop(numero, None)
    return f"Cliente {numero} borrado"


def registrar_hooks() -> None:
    @before_llm_call
    def contar_llamadas(contexto):
        estadisticas["llamadas_llm"] += 1
        print(f"[hook] llamada #{estadisticas['llamadas_llm']} al LLM de '{contexto.agent.role}'")

    @before_tool_call(tools=["borrar_cliente"])
    def bloquear_borrados(contexto):
        estadisticas["herramientas_bloqueadas"] += 1
        print(f"[hook] BLOQUEADO: {contexto.tool_name}({contexto.tool_input})")
        return False  # la herramienta no se ejecuta; el agente recibe un aviso de que fue bloqueada

    @after_tool_call(tools=["buscar_cliente"])
    def enmascarar_dni(contexto):
        # el LLM nunca ve el DNI completo: se reemplaza antes de que el resultado vuelva al agente
        return re.sub(r"DNI [\d.]+", "DNI ***", contexto.tool_result or "")


def construir_agente(llm=None) -> Agent:
    return Agent(
        role="Operador de CRM",
        goal="Gestionar pedidos sobre clientes usando las herramientas",
        backstory="Ejecuta lo que se le pide con las herramientas y reporta el resultado tal cual.",
        llm=llm or crear_llm(0.0),
        tools=[buscar_cliente, borrar_cliente],
        max_iter=5,
    )


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    registrar_hooks()
    try:
        respuesta = construir_agente().kickoff("Buscá los datos del cliente 123 y después borrá al cliente 456.")
    finally:
        clear_all_global_hooks()  # los hooks son globales: limpiarlos evita que afecten a otro código
    print(f"\n=== Respuesta ===\n{respuesta.raw}")
    print(f"\nEstadísticas: {estadisticas}\nClientes que siguen en la base: {list(CLIENTES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
