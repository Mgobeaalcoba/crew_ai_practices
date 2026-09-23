"""Flow básico: pasos encadenados por eventos, sin ningún LLM.

Un Flow es un programa de Python cuyos métodos se disparan entre sí:
- `@start()` marca por dónde arranca.
- `@listen(metodo)` se ejecuta cuando `metodo` termina y recibe lo que devolvió.

    obtener_pedido ──► calcular_total ──► emitir_ticket

Los Flows no necesitan agentes: sirven para orquestar cualquier cosa. Cuando un paso necesita "pensar",
llamás a un agente o a un Crew desde ese paso (ejemplos 07 y 08).

Uso:
    uv run main.py flows/01_basico
"""

import sys

import comun  # noqa: F401  (carga .env y ajustes de entorno; ver comun/entorno.py)
from crewai.flow.flow import Flow, listen, start

PRECIOS = {"café": 2500, "medialuna": 900, "tostado": 4200}


class FlowPedido(Flow):
    @start()
    def obtener_pedido(self) -> dict[str, int]:
        return {"café": 2, "medialuna": 3}

    @listen(obtener_pedido)
    def calcular_total(self, pedido: dict[str, int]) -> int:
        return sum(PRECIOS[producto] * cantidad for producto, cantidad in pedido.items())

    @listen(calcular_total)
    def emitir_ticket(self, total: int) -> str:
        return f"Total a pagar: ${total:,}".replace(",", ".")


def main() -> int:
    flow = FlowPedido()
    resultado = flow.kickoff()  # devuelve lo que retornó el último método ejecutado
    print(f"\n=== Resultado ===\n{resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
