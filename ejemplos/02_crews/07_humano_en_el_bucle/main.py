"""Humano en el bucle: la tarea se detiene y le pide a una persona que apruebe o corrija el resultado.

Con `human_input=True`, al terminar la tarea CrewAI muestra la respuesta en la terminal y espera tu
comentario. Si escribís algo, el agente rehace la respuesta teniéndolo en cuenta; con Enter vacío, la acepta.

Es interactivo: corrélo en una terminal (no en un pipe). Para flujos con aprobación más elaborada
(varias salidas posibles, ruteo según la respuesta) mirá el flow 03_flows/06_human_feedback.

Uso:
    uv run main.py humano_en_el_bucle "invitación al asado de fin de año de la oficina"
"""

import sys

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm


def construir_crew(pedido: str, llm=None) -> Crew:
    redactor = Agent(role="Redactor de comunicaciones internas", goal="Escribir mensajes claros y cálidos",
                     backstory="Escribe para Slack: breve, con emojis moderados.", llm=llm or crear_llm(0.7))
    mensaje = Task(description=f"Escribí este mensaje: {pedido}", expected_output="El mensaje listo para enviar.",
                   agent=redactor, human_input=True)
    return Crew(agents=[redactor], tasks=[mensaje])


def main() -> int:
    pedido = " ".join(sys.argv[1:]) or "invitación al asado de fin de año de la oficina, viernes 12/12 a las 20"
    print(f"LLM: {describir_llm()}\n")
    print(f"\n=== Mensaje aprobado ===\n{construir_crew(pedido).kickoff().raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
