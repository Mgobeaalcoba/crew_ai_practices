"""Eventos: escuchar todo lo que pasa en CrewAI sin modificarlo (logs, métricas, costos, auditoría).

CrewAI emite eventos en un bus global: arranque y fin de crews, tareas, agentes, llamadas al LLM, uso de
herramientas, flows, memoria, knowledge... Un listener es una clase que se suscribe a los que le interesan.

Diferencia con los hooks (ejemplo 01): los eventos solo observan y corren en segundo plano; los hooks
pueden cambiar mensajes, respuestas o bloquear herramientas.

Uso:
    uv run main.py eventos
"""

import sys
import time

from crewai import Agent, Crew, Task
from crewai.events import BaseEventListener, crewai_event_bus
from crewai.events.types.crew_events import CrewKickoffCompletedEvent, CrewKickoffStartedEvent
from crewai.events.types.llm_events import LLMCallCompletedEvent
from crewai.events.types.task_events import TaskCompletedEvent

from comun import crear_llm, describir_llm


class Metricas(BaseEventListener):
    def __init__(self) -> None:
        self.registro: list[str] = []
        self.llamadas_llm = 0
        self.tokens = 0
        self._inicio = 0.0
        super().__init__()  # registra los handlers de setup_listeners en el bus

    def setup_listeners(self, bus) -> None:
        @bus.on(CrewKickoffStartedEvent)
        def al_iniciar(fuente, evento):
            self._inicio = time.perf_counter()
            self.registro.append(f"crew '{evento.crew_name}' iniciado")

        @bus.on(LLMCallCompletedEvent)
        def al_responder_llm(fuente, evento):
            self.llamadas_llm += 1
            self.tokens += (evento.usage or {}).get("total_tokens", 0)

        @bus.on(TaskCompletedEvent)
        def al_terminar_tarea(fuente, evento):
            self.registro.append(f"tarea terminada: {evento.output.description[:50]}...")

        @bus.on(CrewKickoffCompletedEvent)
        def al_terminar(fuente, evento):
            self.registro.append(f"crew terminado en {time.perf_counter() - self._inicio:.1f} s")


def construir_crew(llm=None) -> Crew:
    llm = llm or crear_llm(0.5)
    poeta = Agent(role="Poeta", goal="Escribir poemas breves", backstory="Ama los haikus.", llm=llm)
    critico = Agent(role="Crítico", goal="Comentar poemas en una línea", backstory="Justo y breve.", llm=llm)
    haiku = Task(description="Escribí un haiku sobre el colectivo a la mañana.", expected_output="Un haiku.", agent=poeta)
    critica = Task(description="Comentá el haiku en una oración.", expected_output="Una oración.", agent=critico)
    return Crew(agents=[poeta, critico], tasks=[haiku, critica], name="taller de poesía")


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    with crewai_event_bus.scoped_handlers():  # los handlers se quitan al salir del bloque
        metricas = Metricas()
        salida = construir_crew().kickoff()
        crewai_event_bus.flush()  # los handlers corren en segundo plano: esperar a que terminen
    print(f"\n=== Resultado ===\n{salida.raw}\n\n=== Lo que registró el listener ===")
    for linea in metricas.registro:
        print(f"  - {linea}")
    print(f"  - {metricas.llamadas_llm} llamadas al LLM, {metricas.tokens} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
