"""Estado de un Flow: datos compartidos entre todos los pasos.

Además de pasarse valores de retorno, los pasos leen y escriben `self.state`. Hay dos formas:

- **No estructurado**: `Flow` a secas; `self.state` es un dict (más un `id` automático).
- **Estructurado**: `Flow[MiEstado]` con un modelo Pydantic; tenés tipos, valores por defecto, validación
  y autocompletado. Es lo recomendado para cualquier cosa no trivial.

Los `inputs` de `kickoff(inputs={...})` se cargan en el estado antes del primer paso.

Uso:
    uv run main.py flows/02_estado
"""

import sys

import comun  # noqa: F401  (carga .env y ajustes de entorno; ver comun/entorno.py)
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel


class FlowContadorLibre(Flow):
    @start()
    def iniciar(self):
        self.state["visitas"] = 0

    @listen(iniciar)
    def visitar(self):
        self.state["visitas"] += 3
        return self.state["visitas"]


class EstadoCarrito(BaseModel):
    cliente: str = "anónimo"
    items: list[str] = []
    total: float = 0.0
    descuento_aplicado: bool = False


class FlowCarrito(Flow[EstadoCarrito]):
    @start()
    def agregar(self):
        self.state.items += ["yerba", "azúcar", "galletitas"]
        self.state.total = 12_300

    @listen(agregar)
    def aplicar_descuento(self):
        if len(self.state.items) >= 3:
            self.state.total *= 0.9
            self.state.descuento_aplicado = True

    @listen(aplicar_descuento)
    def resumen(self) -> str:
        return f"{self.state.cliente}: {len(self.state.items)} ítems, total ${self.state.total:,.0f}"


def main() -> int:
    print(f"No estructurado → visitas = {FlowContadorLibre().kickoff()}")

    flow = FlowCarrito()
    print(f"Estructurado    → {flow.kickoff(inputs={'cliente': 'Marta'})}")
    print(f"Estado final    → {flow.state.model_dump()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
