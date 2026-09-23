"""Integrador, versión Flow: el mismo redactor-editor, pero con el bucle expresado como un Flow.

Compará con 01_redactor_editor: allá el bucle es un `while` en Python; acá cada etapa es un paso del Flow,
el estado (notas, borrador, ronda) vive en `self.state` y el ruteo lo decide un `@router`.

    investigar_y_redactar ──► editar ──► decidir ──"aprobado"──► guardar
                                ▲                  ├─"agotado"───► guardar
                                │                  └─"rechazado"─► reescribir ─┐
                                └──────────────── "reescrito" ─────────────────┘

Agentes, tareas y la guarda de longitud se reutilizan del ejemplo 01 (no se duplican).

Uso:
    uv run main.py redactor_editor_flow "energía solar"
"""

import importlib
import sys

from crewai import Crew
from crewai.flow.flow import Flow, listen, or_, router, start
from pydantic import BaseModel

from comun import contar, describir_llm

# "01_redactor_editor" no es un identificador válido de Python, así que no se puede usar en un `import`;
# importlib acepta el nombre como texto.
base = importlib.import_module("ejemplos.06_integrador.01_redactor_editor.main")


class EstadoRedaccion(BaseModel):
    tema: str = base.TEMA_POR_DEFECTO
    notas: str = ""
    borrador: str = ""
    correcciones: str = ""
    aprobado: bool = False
    ronda: int = 0


def crear_flow(llm=None) -> Flow:
    investigador, redactor, editor = base.construir_agentes(llm)

    class FlowRedaccion(Flow[EstadoRedaccion]):
        @start()
        async def investigar_y_redactar(self):
            investigar = base.tarea_investigar(self.state.tema, investigador)
            redactar = base.tarea_redactar([investigar], redactor)
            salida = await Crew(agents=[investigador, redactor], tasks=[investigar, redactar]).kickoff_async()
            self.state.notas, self.state.borrador = (t.raw for t in salida.tasks_output)

        # Es un router (y no un listen) para que el bucle funcione: un or_() que escucha *métodos* se dispara
        # una sola vez por ejecución; solo se vuelve a armar cuando un router emite una etiqueta nueva.
        @router("rechazado")
        async def reescribir(self) -> str:
            tarea = base.tarea_reescribir(self.state.notas, self.state.borrador, self.state.correcciones, redactor)
            self.state.borrador = (await Crew(agents=[redactor], tasks=[tarea]).kickoff_async()).raw
            return "reescrito"

        @listen(or_(investigar_y_redactar, "reescrito"))
        async def editar(self):
            self.state.ronda += 1
            tarea = base.tarea_editar([], editor, self.state.notas)
            tarea.description += f"\n\nBORRADOR A REVISAR:\n{self.state.borrador}"
            salida = await Crew(agents=[editor], tasks=[tarea]).kickoff_async()
            self.state.aprobado, self.state.correcciones = base.evaluar(base.leer_veredicto(salida.raw), self.state.borrador)

        @router(editar)
        def decidir(self) -> str:
            if self.state.aprobado:
                return "aprobado"
            if self.state.ronda >= base.MAX_RONDAS:
                return "agotado"
            print(f"\n>>> Ronda {self.state.ronda}: devuelto al redactor. Motivo: {self.state.correcciones}\n")
            return "rechazado"

        @listen(or_("aprobado", "agotado"))
        def guardar(self) -> str:
            return self.state.borrador

    return FlowRedaccion()


def main() -> int:
    tema = " ".join(sys.argv[1:]) or base.TEMA_POR_DEFECTO
    print(f"LLM: {describir_llm()}\n")
    flow = crear_flow()
    borrador = flow.kickoff(inputs={"tema": tema})
    estado = "APROBADO" if flow.state.aprobado else f"SIN APROBAR tras {base.MAX_RONDAS} rondas"
    print(f"\n=== Borrador final ({estado}, {contar(borrador)} palabras, {flow.state.ronda} ronda/s) ===\n\n{borrador}")
    return 0 if flow.state.aprobado else 1


if __name__ == "__main__":
    sys.exit(main())
