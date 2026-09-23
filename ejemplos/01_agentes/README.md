# 01 · Agentes

Un agente es un LLM con un rol, un objetivo y, opcionalmente, capacidades extra. Este grupo recorre **cada capacidad por separado**, con el ejemplo más chico que la muestra funcionando.

| # | Ejemplo | Capacidad | Qué necesita además del LLM |
|---|---|---|---|
| 01 | [agente_solo](01_agente_solo) | Responder sin Crew ni Task; salida Pydantic | — |
| 02 | [herramientas](02_herramientas) | Llamar funciones propias (`@tool`, `BaseTool`, `ToolFailure`) | — |
| 03 | [mcp](03_mcp) | Usar herramientas de un servidor MCP | — (el servidor es local) |
| 04 | [knowledge](04_knowledge) | Responder con documentos propios (RAG) | Embeddings (LM Studio) |
| 05 | [memoria](05_memoria) | Recordar entre ejecuciones | Embeddings (LM Studio) |
| 06 | [planificacion](06_planificacion) | Armar un plan antes de actuar | — |
| 07 | [guardrails](07_guardrails) | Validar la salida y corregirse | — |
| 08 | [salida_estructurada](08_salida_estructurada) | Devolver objetos Pydantic | — |
| 09 | [ejecucion_de_codigo](09_ejecucion_de_codigo) | Ejecutar Python en un sandbox | Docker |
| 10 | [a2a](10_a2a) | Delegar en un agente remoto (protocolo A2A) | `crewai[a2a]` (no verificado) |
| 11 | [multimodal](11_multimodal) | Ver imágenes o PDFs | Un modelo con visión (solo documentado) |

Todas las capacidades se combinan: un agente puede tener herramientas, knowledge y memoria a la vez. La clasificación completa está en [docs/clasificacion.md](../../docs/clasificacion.md#3-por-capacidades-del-agente).

## Anatomía de un agente

```python
from crewai import Agent
from comun import crear_llm

agente = Agent(
    role="Vendedor de tienda online",            # quién es
    goal="Responder presupuestos exactos",        # qué busca
    backstory="Nunca inventa precios.",           # cómo se comporta (reglas, estilo)
    llm=crear_llm(0.0),                           # el modelo (ver docs/proveedores-llm.md)
    tools=[...],                                  # 02: herramientas
    mcps=[...],                                   # 03: servidores MCP
    knowledge_sources=[...], embedder={...},      # 04: knowledge
    planning_config=PlanningConfig(...),          # 06: planificación
    allow_delegation=False,                       # delegar en otros agentes del Crew
    max_iter=6,                                   # máximo de vueltas pensar → actuar → observar
    verbose=True,                                 # mostrar el razonamiento en la terminal
)
```

**Dos formas de ejecutarlo:**

- `agente.kickoff("pregunta")`: directo, sin Crew. Es lo más simple, pero ignora knowledge ([trampas §1](../../docs/trampas-conocidas.md#1-agentkickoff-ignora-knowledge_sources)).
- Dentro de un Crew, con una `Task` (ver [02_crews](../02_crews)).
