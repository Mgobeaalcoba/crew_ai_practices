"""Pasos en paralelo y condiciones combinadas: `and_` y `or_`.

- Varios `@listen` sobre el mismo paso se disparan juntos (en paralelo si son `async`).
- `@listen(and_(a, b))` espera a que terminen **todos**.
- `@listen(or_(a, b))` se dispara con **el primero** que termine.

                  ┌─► precio_proveedor_a ─┐
    pedir_precios ┤                       ├─and_─► comparar
                  └─► precio_proveedor_b ─┘
                                          └─or_──► avisar_primera_respuesta

Uso:
    uv run main.py paralelo_and_or
"""

import asyncio
import sys
import time

import comun  # noqa: F401  (carga .env y ajustes de entorno; ver comun/entorno.py)
from crewai.flow.flow import Flow, and_, listen, or_, start
from pydantic import BaseModel


class EstadoCotizacion(BaseModel):
    precios: dict[str, int] = {}
    primera_respuesta: str = ""
    eventos: list[str] = []
    inicio: float = 0.0
    duracion: float = 0.0


class FlowCotizacion(Flow[EstadoCotizacion]):
    @start()
    def pedir_precios(self):
        self.state.inicio = time.perf_counter()
        self.state.eventos.append("pedido enviado")

    @listen(pedir_precios)
    async def precio_proveedor_a(self):
        await asyncio.sleep(0.4)  # simula una API lenta
        self.state.precios["A"] = 15_000
        self.state.eventos.append("respondió A")

    @listen(pedir_precios)
    async def precio_proveedor_b(self):
        await asyncio.sleep(0.1)
        self.state.precios["B"] = 16_500
        self.state.eventos.append("respondió B")

    @listen(or_(precio_proveedor_a, precio_proveedor_b))
    def avisar_primera_respuesta(self):
        self.state.primera_respuesta = next(iter(self.state.precios))
        self.state.eventos.append(f"primera respuesta: {self.state.primera_respuesta}")

    @listen(and_(precio_proveedor_a, precio_proveedor_b))
    def comparar(self) -> str:
        proveedor = min(self.state.precios, key=self.state.precios.get)
        self.state.eventos.append("comparación hecha")
        self.state.duracion = time.perf_counter() - self.state.inicio
        return f"Conviene el proveedor {proveedor} (${self.state.precios[proveedor]:,})"


def main() -> int:
    flow = FlowCotizacion()
    resultado = flow.kickoff()
    print(f"Eventos: {' → '.join(flow.state.eventos)}")
    print(f"Resultado: {resultado}")
    # En serie serían 0,4 + 0,1 = 0,5 s; en paralelo, lo que tarda el más lento
    print(f"Duración de los pasos: {flow.state.duracion:.2f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
