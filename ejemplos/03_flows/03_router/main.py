"""Router: bifurcar el Flow según una condición.

Un método `@router(paso)` devuelve un texto (una "etiqueta"), y los métodos `@listen("etiqueta")` que
coinciden se ejecutan. Es el `if` de los Flows, y con él se pueden armar bucles: un listener puede volver
a disparar un paso anterior emitiendo su etiqueta.

    evaluar ──► router ──"aprobado"──► aprobar
                      ├─"revision"───► pedir_revision
                      └─"rechazado"──► rechazar

Uso:
    uv run main.py flows/03_router 720
"""

import sys

import comun  # noqa: F401  (carga .env y ajustes de entorno; ver comun/entorno.py)
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel


class EstadoCredito(BaseModel):
    puntaje: int = 0
    decision: str = ""


class FlowCredito(Flow[EstadoCredito]):
    @start()
    def evaluar(self):
        print(f"Evaluando puntaje {self.state.puntaje}")

    @router(evaluar)
    def decidir(self) -> str:
        if self.state.puntaje >= 700:
            return "aprobado"
        if self.state.puntaje >= 500:
            return "revision"
        return "rechazado"

    @listen("aprobado")
    def aprobar(self):
        self.state.decision = "Crédito aprobado automáticamente"

    @listen("revision")
    def pedir_revision(self):
        self.state.decision = "Pasa a revisión manual de un analista"

    @listen("rechazado")
    def rechazar(self):
        self.state.decision = "Crédito rechazado"


def decidir(puntaje: int) -> str:
    flow = FlowCredito()
    flow.kickoff(inputs={"puntaje": puntaje})
    return flow.state.decision


def main() -> int:
    puntajes = [int(p) for p in sys.argv[1:]] or [820, 610, 300]
    for puntaje in puntajes:
        print(f"  → {decidir(puntaje)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
