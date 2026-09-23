"""Cliente A2A: un agente de CrewAI que delega en un agente remoto.

Con `a2a=A2AClientConfig(endpoint=...)`, CrewAI lee la agent card del remoto y le da al agente local la
opción de delegarle trabajo. El remoto puede estar hecho con cualquier framework: solo tiene que hablar A2A.

NO VERIFICADO (ver README.md de esta carpeta). Requiere `uv add "crewai[a2a]"` y el servidor corriendo:
    uv run python ejemplos/01_agentes/10_a2a/servidor.py      # terminal 1
    uv run main.py a2a "Mandale al equipo de Londres: la reunión pasa al jueves"   # terminal 2
"""

import sys

from crewai import Agent, Crew, Task

from comun import crear_llm, describir_llm

ENDPOINT = "http://localhost:9999/.well-known/agent-card.json"


def a2a_disponible() -> bool:
    try:
        import a2a  # noqa: F401
    except ImportError:
        return False
    return True


def construir_crew(mensaje: str, llm=None) -> Crew:
    from crewai.a2a import A2AClientConfig  # importa a2a-sdk: solo existe con el extra instalado

    coordinador = Agent(
        role="Asistente de comunicación",
        goal="Preparar mensajes para equipos de otros países",
        backstory="Si un mensaje va a un equipo angloparlante, delega la traducción en el traductor remoto.",
        llm=llm or crear_llm(0.2),
        a2a=A2AClientConfig(endpoint=ENDPOINT, timeout=60, max_turns=3, fail_fast=True),
    )
    tarea = Task(
        description=f"Prepará este mensaje para el equipo de Londres: {mensaje}",
        expected_output="El mensaje final en inglés.",
        agent=coordinador,
    )
    return Crew(agents=[coordinador], tasks=[tarea])


def main() -> int:
    if not a2a_disponible():
        print('Falta el extra de A2A. Instalalo con: uv add "crewai[a2a]"')
        return 2
    mensaje = " ".join(sys.argv[1:]) or "la reunión del martes pasa al jueves a las 15 (hora de Londres)"
    print(f"LLM: {describir_llm()} · remoto: {ENDPOINT}\n")
    print(f"\n=== Resultado ===\n{construir_crew(mensaje).kickoff().raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
