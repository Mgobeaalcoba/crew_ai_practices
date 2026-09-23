"""Flow que orquesta Crews: cada paso grande es un equipo, y el Flow los encadena con lógica propia.

Es la arquitectura que CrewAI recomienda para aplicaciones reales: Flows para el control (estado, ramas,
reintentos) y Crews para el trabajo autónomo dentro de cada etapa.

    planificar (Crew A) ──► escribir (Crew B) ──► router ──"ok"─────────► terminar
                                 ▲                    └─"muy_largo"──┐
                                 └────────── (máx. 2 reintentos) ◄───┘

El control de largo lo hace Python, no un LLM (los LLM cuentan mal las palabras).

Uso:
    uv run main.py flow_con_crews "la historia del dulce de leche"
"""

import sys

from crewai import Agent, Crew, Task
from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel

from comun import contar, crear_llm, describir_llm

MAX_PALABRAS = 120
MAX_INTENTOS = 3


class EstadoArticulo(BaseModel):
    tema: str = ""
    esquema: str = ""
    texto: str = ""
    intentos: int = 0
    correccion: str = ""


def crew_planificador(tema: str, llm) -> Crew:
    editor = Agent(role="Editor", goal="Diseñar esquemas de artículos breves", backstory="Va al grano.", llm=llm)
    tarea = Task(description=f"Armá el esquema de un artículo de divulgación sobre: {tema}",
                 expected_output="3 puntos, uno por línea.", agent=editor)
    return Crew(agents=[editor], tasks=[tarea])


def crew_redactor(esquema: str, correccion: str, llm) -> Crew:
    redactor = Agent(role="Redactor de divulgación", goal="Escribir textos breves y amenos",
                     backstory="Escribe para un público general, sin tecnicismos.", llm=llm)
    extra = f"\nCORRECCIÓN PEDIDA: {correccion}" if correccion else ""
    tarea = Task(description=f"Escribí un artículo de menos de {MAX_PALABRAS} palabras con este esquema:\n{esquema}{extra}",
                 expected_output="Solo el texto del artículo.", agent=redactor)
    return Crew(agents=[redactor], tasks=[tarea])


def crear_flow(llm=None) -> Flow:
    llm = llm or crear_llm(0.5)

    class FlowArticulo(Flow[EstadoArticulo]):
        @start()
        async def planificar(self):
            self.state.esquema = (await crew_planificador(self.state.tema, llm).kickoff_async()).raw

        @listen(or_(planificar, "muy_largo"))  # la primera vez, tras planificar; después, en cada reintento
        async def escribir(self):
            self.state.intentos += 1
            salida = await crew_redactor(self.state.esquema, self.state.correccion, llm).kickoff_async()
            self.state.texto = salida.raw

        @router(escribir)
        def revisar(self) -> str:
            palabras = contar(self.state.texto)
            if palabras <= MAX_PALABRAS or self.state.intentos >= MAX_INTENTOS:
                return "ok"
            self.state.correccion = f"Tiene {palabras} palabras; recortalo a menos de {MAX_PALABRAS}."
            return "muy_largo"

        @listen("ok")
        def terminar(self) -> str:
            return self.state.texto

    return FlowArticulo()


def main() -> int:
    tema = " ".join(sys.argv[1:]) or "la historia del dulce de leche"
    print(f"LLM: {describir_llm()}\n")
    flow = crear_flow()
    texto = flow.kickoff(inputs={"tema": tema})
    print(f"\n=== Artículo ({contar(texto)} palabras, {flow.state.intentos} intento/s) ===\n{texto}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
