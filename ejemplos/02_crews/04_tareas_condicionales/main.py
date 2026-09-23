"""Tareas condicionales: una tarea que solo se ejecuta si la anterior cumple una condición.

`ConditionalTask(condition=funcion)` recibe la salida de la tarea previa y decide si correr. Si no corre,
queda una salida vacía en su lugar. No puede ser la primera tarea del Crew.

    clasificar reclamo ──► ¿es urgente? ──sí──► redactar escalamiento
                                        └─no──► (se saltea)

Uso:
    uv run main.py condicionales "Se me cortó la luz y tengo un respirador en casa"
    uv run main.py condicionales "Quiero cambiar la fecha de vencimiento de mi factura"
"""

import sys

from crewai import Agent, Crew, Task
from crewai.tasks.conditional_task import ConditionalTask
from crewai.tasks.task_output import TaskOutput
from pydantic import BaseModel

from comun import crear_llm, describir_llm


class Clasificacion(BaseModel):
    categoria: str
    urgente: bool
    motivo: str


def es_urgente(salida: TaskOutput) -> bool:
    return bool(salida.pydantic and salida.pydantic.urgente)


def construir_crew(reclamo: str, llm=None) -> Crew:
    llm = llm or crear_llm(0.0)
    operador = Agent(role="Operador de atención", goal="Clasificar reclamos de una distribuidora eléctrica",
                     backstory="Urgente = riesgo para la vida, la salud o la seguridad. Todo lo demás no lo es.",
                     llm=llm)
    supervisor = Agent(role="Supervisor de guardia", goal="Escalar casos urgentes a la cuadrilla",
                       backstory="Escribe órdenes claras y accionables.", llm=llm)

    clasificar = Task(description=f"Clasificá este reclamo: {reclamo}", expected_output="La clasificación.",
                      agent=operador, output_pydantic=Clasificacion)
    escalar = ConditionalTask(
        description="Redactá la orden de escalamiento para la cuadrilla de guardia.",
        expected_output="Una orden de 3 líneas: prioridad, situación y acción.",
        agent=supervisor,
        condition=es_urgente,
    )
    return Crew(agents=[operador, supervisor], tasks=[clasificar, escalar], verbose=True)


def main() -> int:
    reclamo = " ".join(sys.argv[1:]) or "Se me cortó la luz y tengo un respirador artificial en casa"
    print(f"LLM: {describir_llm()}\n")
    salida = construir_crew(reclamo).kickoff()
    clasificacion, escalamiento = salida.tasks_output
    print(f"\n=== Clasificación ===\n{clasificacion.pydantic}")
    print(f"\n=== Escalamiento ===\n{escalamiento.raw or '(no se ejecutó: no es urgente)'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
