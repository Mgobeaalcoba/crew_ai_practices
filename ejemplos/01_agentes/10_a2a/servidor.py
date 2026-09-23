"""Servidor A2A: expone un agente de CrewAI por el protocolo Agent-to-Agent (A2A).

A2A es un protocolo abierto para que agentes de distintos frameworks, procesos o empresas se deleguen
tareas. El servidor publica una "agent card" (quién es, qué sabe hacer) en /.well-known/agent-card.json
y recibe mensajes por JSON-RPC.

CrewAI 1.15 trae el *cliente* A2A (`Agent(a2a=...)`), pero no un servidor fuera de su plataforma AMP, así que
este archivo lo arma con `a2a-sdk` directamente.

NO VERIFICADO: escrito contra la API de a2a-sdk 0.3 sin poder instalarlo (ver README.md de esta carpeta).

Requiere: uv add "crewai[a2a]"
Uso:      uv run python ejemplos/01_agentes/10_a2a/servidor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # para importar `comun` al correrlo como script

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from a2a.utils import new_agent_text_message
from crewai import Agent

from comun import crear_llm

PUERTO = 9999


class TraductorExecutor(AgentExecutor):
    def __init__(self) -> None:
        self.agente = Agent(
            role="Traductor",
            goal="Traducir textos al inglés conservando el tono",
            backstory="Traductor profesional. Devuelve solo la traducción.",
            llm=crear_llm(0.2),
        )

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        resultado = await self.agente.kickoff_async(context.get_user_input())
        await event_queue.enqueue_event(new_agent_text_message(resultado.raw))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Este agente no admite cancelación")


def tarjeta() -> AgentCard:
    return AgentCard(
        name="Traductor al inglés",
        description="Traduce textos del español al inglés",
        url=f"http://localhost:{PUERTO}/",
        version="1.0.0",
        default_input_modes=["text"],
        default_output_modes=["text"],
        capabilities=AgentCapabilities(streaming=False),
        skills=[AgentSkill(id="traducir", name="Traducir", description="Traduce al inglés",
                           tags=["traducción"], examples=["Traducí: buen día"])],
    )


if __name__ == "__main__":
    manejador = DefaultRequestHandler(agent_executor=TraductorExecutor(), task_store=InMemoryTaskStore())
    app = A2AStarletteApplication(agent_card=tarjeta(), http_handler=manejador)
    uvicorn.run(app.build(), host="127.0.0.1", port=PUERTO)
