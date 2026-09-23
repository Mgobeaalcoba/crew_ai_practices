"""Agente con knowledge (RAG): responde con documentos propios que el modelo nunca vio.

Qué pasa por detrás:
1. CrewAI parte cada fuente en fragmentos (chunks).
2. Calcula el embedding de cada fragmento con el embedder configurado y los guarda en una base vectorial (db/).
3. Antes de cada respuesta busca los fragmentos más parecidos a la pregunta y los agrega al prompt.

Requiere un servidor de embeddings. Por defecto, LM Studio local con `text-embedding-nomic-embed-text-v1.5`:
    lms server start

Uso:
    uv run main.py knowledge "¿Puedo devolver un taladro que ya usé?"
"""

import sys
from pathlib import Path

from crewai import Agent, Crew, Task
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.text_file_knowledge_source import TextFileKnowledgeSource

from comun import config_embedder, crear_llm, describir_llm

DOCUMENTOS = Path(__file__).with_name("conocimiento")


def fuentes() -> list:
    return [
        # Un archivo: se pasa un Path absoluto porque, con un str, CrewAI lo busca dentro de ./knowledge/
        TextFileKnowledgeSource(file_paths=[DOCUMENTOS / "politicas.md"], chunk_size=600, chunk_overlap=60),
        # Un texto en memoria: útil para datos que ya tenés en el programa
        StringKnowledgeSource(content="Teléfono de atención: 0800-555-TUERCA. Mail: ayuda@latuerca.example"),
    ]


def construir_agente(llm=None, embedder: dict | None = None) -> Agent:
    return Agent(
        role="Atención al cliente de La Tuerca",
        goal="Responder consultas de clientes citando las políticas de la tienda",
        backstory="Responde solo con lo que dicen las políticas. Si algo no figura, deriva al teléfono de atención.",
        llm=llm or crear_llm(0.0),
        knowledge_sources=fuentes(),
        embedder=embedder or config_embedder(),
        knowledge_config=KnowledgeConfig(results_limit=3, score_threshold=0.3),
        verbose=True,
    )


def responder(pregunta: str, llm=None, embedder: dict | None = None) -> str:
    # En crewai 1.15.20 el knowledge solo se consulta cuando el agente ejecuta una Task dentro de un Crew.
    # Con Agent.kickoff() directo las fuentes se ignoran en silencio: el agente contesta "no tengo esa información".
    agente = construir_agente(llm, embedder)
    tarea = Task(
        description=f"Consulta del cliente: {pregunta}",
        expected_output="Una respuesta breve y amable que cite la política aplicable.",
        agent=agente,
    )
    return Crew(agents=[agente], tasks=[tarea]).kickoff().raw


def main() -> int:
    pregunta = " ".join(sys.argv[1:]) or "Compré un taladro hace 20 días y lo usé una vez. ¿Lo puedo devolver?"
    print(f"LLM: {describir_llm()}\nEmbeddings: {config_embedder()['config']['model_name']}\n")
    print(f"\n=== Respuesta ===\n{responder(pregunta)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
