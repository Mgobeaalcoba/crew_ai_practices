"""Flow con agentes: el Flow pone la estructura (pasos, ramas) y cada agente pone el criterio.

Mesa de ayuda que clasifica un mail y lo deriva al especialista que corresponde:

    clasificar (agente) ──► router ──"facturacion"──► responder_facturacion (agente)
                                   ├─"tecnico"──────► responder_tecnico (agente)
                                   └─"otro"─────────► derivar_a_humano (sin LLM)

Ventaja sobre un Crew jerárquico: la decisión de a quién derivar es código tuyo, predecible y testeable;
el LLM solo clasifica. Los pasos son `async` y usan `kickoff_async`: dentro de un Flow, `Agent.kickoff()`
devuelve una corrutina en vez del resultado.

Uso:
    uv run main.py flow_con_agentes "Me cobraron dos veces la cuota de septiembre"
"""

import sys
from typing import Literal

from crewai import Agent
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel

from comun import crear_llm, describir_llm


class Clasificacion(BaseModel):
    categoria: Literal["facturacion", "tecnico", "otro"]
    resumen: str


class EstadoTicket(BaseModel):
    mail: str = ""
    clasificacion: Clasificacion | None = None
    respuesta: str = ""


def crear_flow(llm=None) -> Flow:
    llm = llm or crear_llm(0.2)

    def especialista(area: str) -> Agent:
        return Agent(role=f"Especialista en {area}", goal=f"Resolver consultas de {area} de un proveedor de internet",
                     backstory="Responde en 4 líneas como máximo, con pasos concretos.", llm=llm)

    class FlowMesaDeAyuda(Flow[EstadoTicket]):
        @start()
        async def clasificar(self):
            clasificador = Agent(role="Clasificador de tickets", goal="Clasificar mails de clientes",
                                 backstory="facturacion: cobros, pagos, facturas. tecnico: conexión, equipos. "
                                           "otro: todo lo demás.", llm=llm)
            salida = await clasificador.kickoff_async(self.state.mail, response_format=Clasificacion)
            self.state.clasificacion = salida.pydantic

        @router(clasificar)
        def derivar(self) -> str:
            return self.state.clasificacion.categoria

        @listen("facturacion")
        async def responder_facturacion(self):
            self.state.respuesta = (await especialista("facturación").kickoff_async(self.state.mail)).raw

        @listen("tecnico")
        async def responder_tecnico(self):
            self.state.respuesta = (await especialista("soporte técnico").kickoff_async(self.state.mail)).raw

        @listen("otro")
        def derivar_a_humano(self):
            self.state.respuesta = "Tu consulta fue derivada a una persona del equipo. Te respondemos en 24 h."

    return FlowMesaDeAyuda()


def main() -> int:
    mail = " ".join(sys.argv[1:]) or "Hola, me cobraron dos veces la cuota de septiembre. ¿Cómo lo resuelvo?"
    print(f"LLM: {describir_llm()}\n")
    flow = crear_flow()
    flow.kickoff(inputs={"mail": mail})
    print(f"\n=== Categoría: {flow.state.clasificacion.categoria} ===\n{flow.state.respuesta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
