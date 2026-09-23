"""Aprobación humana en un Flow con `@human_feedback`.

Después de que el paso decorado termina, el Flow muestra su resultado y le pide a una persona su opinión.
Con `emit=[...]`, un LLM interpreta la respuesta libre ("dale, pero bajale un poco") y la reduce a una de
esas etiquetas, que funcionan como las de un `@router`: los `@listen("etiqueta")` deciden qué sigue.

    proponer_descuento ──► [persona opina] ──"aprobado"───► publicar
                                           └─"rechazado"──► descartar

La persona responde por la terminal (ConsoleProvider). `--auto "<respuesta>"` usa un proveedor que
responde solo, para correrlo sin teclado; así también se conectaría Slack, mail o una web: implementando
`HumanFeedbackProvider.request_feedback`.

Uso:
    uv run main.py human_feedback
    uv run main.py human_feedback --auto "Me parece bien, publicalo"
"""

import sys

from crewai.flow import HumanFeedbackResult, human_feedback
from crewai.flow.async_feedback import HumanFeedbackProvider, PendingFeedbackContext
from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel

from comun import crear_llm, describir_llm


class RespuestaFija(HumanFeedbackProvider):
    """Proveedor que no pregunta: devuelve siempre la misma respuesta (para demos y tests)."""

    def __init__(self, respuesta: str) -> None:
        self.respuesta = respuesta

    def request_feedback(self, context: PendingFeedbackContext, flow: Flow) -> str:
        print(f"\n[{context.message}]\n{context.method_output}\n> {self.respuesta}")
        return self.respuesta


class EstadoPromo(BaseModel):
    producto: str = "zapatillas running"
    descuento: int = 30
    estado: str = "pendiente"


def crear_flow(proveedor: HumanFeedbackProvider | None = None, llm=None) -> Flow:
    # La clase se crea dentro de una función porque el decorador necesita el proveedor y el LLM al definirla
    class FlowPromo(Flow[EstadoPromo]):
        @start()
        @human_feedback(
            message="¿Aprobás esta promoción?",
            emit=["aprobado", "rechazado"],
            llm=llm or crear_llm(0.0),  # clasifica la respuesta libre en una de las etiquetas de emit
            default_outcome="rechazado",  # si la persona no responde nada
            provider=proveedor,  # None = ConsoleProvider (pregunta por la terminal)
        )
        def proponer_descuento(self) -> str:
            return f"Promo: {self.state.descuento}% off en {self.state.producto} durante el fin de semana."

        @listen("aprobado")
        def publicar(self, resultado: HumanFeedbackResult) -> str:
            self.state.estado = "publicada"
            return f"Publicada. Comentario de quien aprobó: {resultado.feedback!r}"

        @listen("rechazado")
        def descartar(self, resultado: HumanFeedbackResult) -> str:
            self.state.estado = "descartada"
            return f"Descartada. Motivo: {resultado.feedback!r}"

    return FlowPromo()


def main() -> int:
    proveedor = RespuestaFija(sys.argv[sys.argv.index("--auto") + 1]) if "--auto" in sys.argv else None
    print(f"LLM que clasifica la respuesta: {describir_llm()}\n")
    flow = crear_flow(proveedor)
    resultado = flow.kickoff()
    print(f"\n=== {flow.state.estado.upper()} ===\n{resultado}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
