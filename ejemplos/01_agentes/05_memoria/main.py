"""Memoria: lo que un agente aprende en una ejecución queda disponible en las siguientes.

Knowledge (ejemplo 04) es información que vos cargás de antemano. Memoria es información que el propio
sistema guarda mientras trabaja: el LLM decide qué recordar, con qué importancia y en qué "scope" (carpeta).

Dos partes:
1. La API directa de `Memory`: `remember()` y `recall()`, sin agentes.
2. Un Crew con `memory=`: dos ejecuciones separadas donde la segunda usa lo que se dijo en la primera.

Requiere embeddings (LM Studio por defecto, ver ejemplo 04). Los datos quedan en db/ y persisten entre
corridas; `--limpiar` los borra antes de empezar.

Uso:
    uv run main.py memoria
    uv run main.py memoria --limpiar
"""

import sys

from crewai import Agent, Crew, Task
from crewai.memory.unified_memory import Memory

from comun import config_embedder, crear_llm, describir_llm


def crear_memoria(llm=None, embedder: dict | None = None) -> Memory:
    return Memory(
        llm=llm or crear_llm(0.0),  # analiza cada recuerdo: scope, categorías, importancia
        embedder=embedder or config_embedder(),  # por defecto sería OpenAI y pediría OPENAI_API_KEY
        root_scope="/ejemplos/memoria",
    )


def demo_api(memoria: Memory) -> None:
    print("\n=== 1. API directa ===")
    memoria.remember("El cliente Juan Pérez prefiere que lo contacten por WhatsApp, nunca por teléfono.")
    memoria.remember("Juan Pérez compró una amoladora en marzo y reclamó por el envío tardío.", importance=0.9)
    memoria.remember("El depósito cierra por inventario la última semana de diciembre.")

    for consulta in ("¿Cómo contacto a Juan?", "¿Hay problemas previos con Juan?"):
        # shallow: una sola búsqueda vectorial. deep (por defecto): el LLM reformula y explora más
        resultados = memoria.recall(consulta, limit=2, depth="shallow")
        print(f"\n> {consulta}")
        for r in resultados:
            print(f"  [{r.score:.2f}] {r.record.content}  (scope: {r.record.scope})")


def construir_crew(memoria: Memory, pedido: str, llm=None) -> Crew:
    asistente = Agent(
        role="Asistente personal",
        goal="Ayudar al usuario teniendo en cuenta lo que ya sabés de él",
        backstory="Recuerda preferencias y restricciones del usuario y las respeta sin que se las repita.",
        llm=llm or crear_llm(0.3),
    )
    tarea = Task(
        description=f"Pedido del usuario: {pedido}",
        expected_output="Una respuesta breve y personalizada.",
        agent=asistente,
    )
    return Crew(agents=[asistente], tasks=[tarea], memory=memoria)


def demo_crew(memoria: Memory) -> None:
    print("\n=== 2. Crew con memoria: dos ejecuciones independientes ===")
    primera = construir_crew(memoria, "Hola, soy Ana. Soy vegetariana y alérgica al maní.").kickoff()
    print(f"\n[1ª ejecución] {primera.raw}")
    # Es un Crew nuevo: lo único que comparte con el anterior es la memoria
    segunda = construir_crew(memoria, "Soy Ana. Proponeme una cena para esta noche.").kickoff()
    print(f"\n[2ª ejecución] {segunda.raw}")


def main() -> int:
    print(f"LLM: {describir_llm()}\nEmbeddings: {config_embedder()['config']['model_name']}")
    memoria = crear_memoria()
    if "--limpiar" in sys.argv:
        memoria.reset()
        print("Memoria borrada.")
    demo_api(memoria)
    demo_crew(memoria)
    return 0


if __name__ == "__main__":
    sys.exit(main())
