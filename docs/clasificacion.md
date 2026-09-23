# ¿Qué se puede armar con CrewAI? Tipos y criterios de clasificación

CrewAI no publica una taxonomía oficial de "tipos de agentes". Lo que sí tiene es un conjunto de piezas ([conceptos.md](conceptos.md)) que se combinan de muchas formas. Este documento ordena esas combinaciones con **siete criterios independientes**: cualquier sistema que armes tiene un valor en cada uno.

Por ejemplo, el [integrador redactor-editor](../ejemplos/06_integrador/01_redactor_editor) es: un Crew (1) secuencial (2) de agentes con herramientas (3), con contexto entre tareas (4), autonomía intermedia (5), ejecución batch (6), desplegado como script (7).

## Resumen

| # | Criterio | Pregunta que responde | Valores |
|---|---|---|---|
| 1 | Unidad de orquestación | ¿Qué clase de CrewAI arma el sistema? | Agente solo · Crew · Flow · Flow con Crews |
| 2 | Proceso del Crew | ¿Quién decide el orden de las tareas? | Secuencial · Jerárquico |
| 3 | Capacidades del agente | ¿Qué sabe hacer cada agente además de hablar? | Solo LLM · Herramientas · MCP · Knowledge · Memoria · Planificación · Delegación · Código · Salida estructurada · Guardrails · A2A · Multimodal |
| 4 | Control de las tareas | ¿Cómo se relacionan las tareas entre sí? | Contexto · Asíncronas · Condicionales · Con guardrail · Con humano · Con callback |
| 5 | Grado de autonomía | ¿Cuánto decide el LLM y cuánto tu código? | Determinista · Guiado · Autónomo |
| 6 | Interacción | ¿Participa una persona durante la ejecución? | Batch · Humano en el bucle · Conversacional |
| 7 | Forma de definirlo y desplegarlo | ¿Cómo se escribe y dónde corre? | Script · Proyecto YAML · CrewAI AMP |

---

## 1. Por unidad de orquestación

Es el criterio principal, porque define qué clase escribís.

| Tipo | Qué es | Cuándo | Ejemplo |
|---|---|---|---|
| **Agente solo** | `Agent(...).kickoff("pregunta")`, sin Crew ni Task | Un solo rol, una consulta directa. Lo más simple | [01_agente_solo](../ejemplos/01_agentes/01_agente_solo) |
| **Crew** | Agentes + tareas + proceso | Varias etapas o roles que colaboran en una tarea acotada | [02_crews](../ejemplos/02_crews) |
| **Flow** | Métodos de Python encadenados por eventos, con estado | Lógica de aplicación: ramas, bucles, persistencia. Puede no tener ningún LLM | [03_flows/01 a 05](../ejemplos/03_flows) |
| **Flow con agentes o Crews** | Un Flow cuyos pasos llaman a agentes o Crews | Aplicaciones reales: el Flow controla y los agentes piensan | [03_flows/07](../ejemplos/03_flows/07_flow_con_agentes), [08](../ejemplos/03_flows/08_flow_con_crews), [06_integrador/02](../ejemplos/06_integrador/02_redactor_editor_flow) |

> **Ojo con el agente solo.** En `crewai 1.15.20`, `Agent.kickoff()` ignora `knowledge_sources`: para usar knowledge hace falta un Crew ([trampas-conocidas.md §1](trampas-conocidas.md#1-agentkickoff-ignora-knowledge_sources)).

## 2. Por proceso del Crew

| Proceso | Quién ordena | Ventaja | Costo | Ejemplo |
|---|---|---|---|---|
| **Secuencial** (`Process.sequential`) | Vos, al listar las tareas | Predecible, barato | Rígido | [01_secuencial](../ejemplos/02_crews/01_secuencial) |
| **Jerárquico** (`Process.hierarchical`) | Un manager LLM que delega y revisa | Flexible, reasigna trabajo | Más tokens, menos predecible | [02_jerarquico](../ejemplos/02_crews/02_jerarquico) |
| ~~Consensuado~~ | — | — | **No existe**: figura como `TODO` en `crewai/process.py` | — |

El jerárquico tiene dos variantes: manager genérico (`manager_llm=`) o manager propio (`manager_agent=`).

## 3. Por capacidades del agente

Es lo que suele llamarse "tipos de agentes". No son excluyentes: un mismo agente puede tener herramientas, knowledge y memoria a la vez.

| Tipo | Cómo se activa | Qué agrega | Requiere | Ejemplo |
|---|---|---|---|---|
| **Solo LLM** | `Agent(role, goal, backstory, llm)` | Razonamiento y redacción | Un LLM | [01_agente_solo](../ejemplos/01_agentes/01_agente_solo) |
| **Con herramientas** | `tools=[...]` | Actuar: consultar, calcular, buscar | — | [02_herramientas](../ejemplos/01_agentes/02_herramientas) |
| **Con MCP** | `mcps=[MCPServerStdio(...)]` | Herramientas de otro proceso, reutilizables entre apps | Un servidor MCP | [03_mcp](../ejemplos/01_agentes/03_mcp) |
| **Con knowledge (RAG)** | `knowledge_sources=[...]`, `embedder=` | Responder con documentos propios | Modelo de embeddings | [04_knowledge](../ejemplos/01_agentes/04_knowledge) |
| **Con memoria** | `Crew(memory=Memory(...))` | Recordar entre ejecuciones | Modelo de embeddings | [05_memoria](../ejemplos/01_agentes/05_memoria) |
| **Que planifica** | `planning_config=PlanningConfig(...)` | Plan de pasos antes de actuar | — | [06_planificacion](../ejemplos/01_agentes/06_planificacion) |
| **Con guardrails** | `Task(guardrails=[...])` o `Agent(guardrail=...)` | Autocorrección ante validaciones | — | [07_guardrails](../ejemplos/01_agentes/07_guardrails) |
| **De salida estructurada** | `output_pydantic=`, `response_format=` | Devuelve datos, no texto | — | [08_salida_estructurada](../ejemplos/01_agentes/08_salida_estructurada) |
| **Que ejecuta código** | Una herramienta que corre código en un sandbox | Cálculos exactos, análisis de datos | Docker | [09_ejecucion_de_codigo](../ejemplos/01_agentes/09_ejecucion_de_codigo) |
| **Remoto (A2A)** | `a2a=A2AClientConfig(endpoint=...)` | Delegar en agentes de otros sistemas | `crewai[a2a]` y un servidor A2A | [10_a2a](../ejemplos/01_agentes/10_a2a) |
| **Delegador** | `allow_delegation=True` | Pedir ayuda a otros agentes del Crew | Un Crew | [03_delegacion](../ejemplos/02_crews/03_delegacion) |
| **Multimodal** | `input_files=` (antes `multimodal=True`) | Ver imágenes o leer PDFs | Un modelo con visión | [11_multimodal](../ejemplos/01_agentes/11_multimodal) (solo documentado) |

## 4. Por control de las tareas

| Mecanismo | Qué controla | Ejemplo |
|---|---|---|
| `context=[...]` | Qué salidas previas ve cada tarea | [01_secuencial](../ejemplos/02_crews/01_secuencial) |
| `async_execution=True` | Tareas independientes en paralelo | [05_tareas_asincronas](../ejemplos/02_crews/05_tareas_asincronas) |
| `ConditionalTask(condition=f)` | Saltear una tarea según la anterior | [04_tareas_condicionales](../ejemplos/02_crews/04_tareas_condicionales) |
| `guardrails=[...]` | Repetir la tarea hasta que cumpla | [07_guardrails](../ejemplos/01_agentes/07_guardrails) |
| `human_input=True` | Una persona aprueba o corrige | [07_humano_en_el_bucle](../ejemplos/02_crews/07_humano_en_el_bucle) |
| `callback=f` | Código propio al terminar | [03_callbacks](../ejemplos/04_observabilidad/03_callbacks) |
| `inputs={...}`, `kickoff_for_each`, `kickoff_async` | Reusar un Crew como plantilla, muchas veces o en paralelo | [09_ejecucion_multiple](../ejemplos/02_crews/09_ejecucion_multiple) |

## 5. Por grado de autonomía

Un eje continuo: cuánto del camino decide el LLM y cuánto tu código.

```
determinista ◄──────────────────────────────────────────────────────► autónomo
  Flow sin LLM      Flow que rutea       Crew secuencial     Crew jerárquico
  (01-05 flows)     con agentes (07)     con bucle Python    con delegación
                                         (integrador)        (02_jerarquico)
```

| Nivel | Quién decide qué hacer después | Ventaja | Riesgo |
|---|---|---|---|
| **Determinista** | Tu código | Predecible, testeable, barato | No se adapta |
| **Guiado** | Tu código, con decisiones puntuales del LLM (clasificar, aprobar) | Buen equilibrio | Hay que definir bien las ramas |
| **Autónomo** | El LLM (manager, delegación, planificación) | Resuelve problemas abiertos | Costoso, variable, difícil de depurar |

Regla práctica: empezá por lo más determinista que resuelva el problema y agregá autonomía solo donde haga falta.

## 6. Por interacción

| Tipo | Cómo | Ejemplo |
|---|---|---|
| **Batch** | Entrada → ejecución → salida, sin intervención | La mayoría de los ejemplos |
| **Humano en el bucle (Crew)** | `Task(human_input=True)`: revisión por consola al final de la tarea | [07_humano_en_el_bucle](../ejemplos/02_crews/07_humano_en_el_bucle) |
| **Humano en el bucle (Flow)** | `@human_feedback(emit=[...])`: la respuesta libre de la persona elige la rama; admite proveedores propios (Slack, web) | [06_human_feedback](../ejemplos/03_flows/06_human_feedback) |
| **Aprobación de herramientas** | Un hook `before_tool_call` que pregunta antes de ejecutar | [01_hooks](../ejemplos/04_observabilidad/01_hooks) (versión automática) |
| **Conversacional** | Flows conversacionales (`crewai.flow.conversation`, experimental en 1.15) y `crewai chat` | No cubierto: API experimental |

## 7. Por forma de definirlo y desplegarlo

| Forma | Qué es | Ejemplo |
|---|---|---|
| **Script** | Todo en Python, un archivo | Casi todos los ejemplos |
| **Proyecto YAML** | `config/agents.yaml` + `config/tasks.yaml` + clase `@CrewBase`. Lo genera `crewai create crew` | [08_proyecto_yaml](../ejemplos/02_crews/08_proyecto_yaml) |
| **CrewAI AMP** | La plataforma comercial de CrewAI: despliegue, trazas, integraciones (`apps=`), MCPs de catálogo | Fuera del alcance (requiere cuenta) |

---

## ¿Qué más se puede armar, además de agentes?

| Pieza | Sirve para | Ejemplo |
|---|---|---|
| **Flows sin LLM** | Orquestar cualquier proceso con estado, ramas, paralelismo y persistencia | [03_flows/01 a 05](../ejemplos/03_flows) |
| **Herramientas** | Funciones reutilizables para cualquier agente | [02_herramientas](../ejemplos/01_agentes/02_herramientas) |
| **Servidores MCP** | Herramientas que usan CrewAI y cualquier otro cliente MCP | [03_mcp/servidor.py](../ejemplos/01_agentes/03_mcp/servidor.py) |
| **Servidores A2A** | Exponer un agente para que lo usen otros sistemas | [10_a2a/servidor.py](../ejemplos/01_agentes/10_a2a/servidor.py) |
| **Bases de knowledge** | Indexar documentos para RAG | [04_knowledge](../ejemplos/01_agentes/04_knowledge) |
| **Memoria independiente** | `Memory` se usa sola, sin agentes: `remember`, `recall`, `forget` | [05_memoria](../ejemplos/01_agentes/05_memoria) |
| **Guardrails** | Validadores reutilizables de salidas | [07_guardrails](../ejemplos/01_agentes/07_guardrails) |
| **Hooks y listeners** | Observabilidad, auditoría, seguridad, costos | [04_observabilidad](../ejemplos/04_observabilidad) |
| **LLMs propios** | Una subclase de `BaseLLM` para cualquier backend (el repo tiene uno falso para tests) | [comun/llm_falso.py](../comun/llm_falso.py) |

## Lo que no se puede armar (o ya no conviene)

| Cosa | Estado en 1.15.20 | Alternativa |
|---|---|---|
| Proceso consensuado | Nunca se implementó | Un Flow con varios agentes que votan y un paso que cuenta |
| `allow_code_execution=True` | Deprecado; `CodeInterpreterTool` ya no existe | Sandbox propio ([09](../ejemplos/01_agentes/09_ejecucion_de_codigo)) |
| `multimodal=True` | Deprecado, se elimina en 2.0 | `input_files` ([11](../ejemplos/01_agentes/11_multimodal)) |
| `reasoning=True` | Deprecado | `planning_config` ([06](../ejemplos/01_agentes/06_planificacion)) |

Más detalles en [trampas-conocidas.md §14](trampas-conocidas.md#14-parámetros-deprecados-que-todavía-aparecen-en-tutoriales).

## Matriz: cada ejemplo en cada criterio

| Ejemplo | 1. Orquestación | 2. Proceso | 3. Capacidades | 4. Control | 5. Autonomía | 6. Interacción |
|---|---|---|---|---|---|---|
| 01_agentes/01_agente_solo | Agente | — | Solo LLM, salida estructurada | — | Guiado | Batch |
| 01_agentes/02_herramientas | Agente | — | Herramientas | — | Guiado | Batch |
| 01_agentes/03_mcp | Agente | — | MCP | — | Guiado | Batch |
| 01_agentes/04_knowledge | Crew (1 tarea) | Secuencial | Knowledge | — | Guiado | Batch |
| 01_agentes/05_memoria | Crew | Secuencial | Memoria | — | Guiado | Batch |
| 01_agentes/06_planificacion | Agente | — | Planificación, herramientas | — | Autónomo | Batch |
| 01_agentes/07_guardrails | Crew | Secuencial | Guardrails | Guardrail | Guiado | Batch |
| 01_agentes/08_salida_estructurada | Crew | Secuencial | Salida estructurada | — | Guiado | Batch |
| 01_agentes/09_ejecucion_de_codigo | Agente | — | Código (sandbox) | — | Guiado | Batch |
| 01_agentes/10_a2a | Crew | Secuencial | A2A | — | Autónomo | Batch |
| 02_crews/01_secuencial | Crew | Secuencial | Solo LLM | Contexto | Guiado | Batch |
| 02_crews/02_jerarquico | Crew | Jerárquico | Delegación | — | Autónomo | Batch |
| 02_crews/03_delegacion | Crew | Secuencial | Delegación | — | Autónomo | Batch |
| 02_crews/04_tareas_condicionales | Crew | Secuencial | Salida estructurada | Condicional | Guiado | Batch |
| 02_crews/05_tareas_asincronas | Crew | Secuencial | Solo LLM | Asíncronas, contexto | Guiado | Batch |
| 02_crews/06_planificacion | Crew | Secuencial | Planificación del Crew | — | Autónomo | Batch |
| 02_crews/07_humano_en_el_bucle | Crew | Secuencial | Solo LLM | Con humano | Guiado | Humano en el bucle |
| 02_crews/08_proyecto_yaml | Crew (YAML) | Secuencial | Solo LLM | Callbacks | Guiado | Batch |
| 02_crews/09_ejecucion_multiple | Crew | Secuencial | Solo LLM | Inputs, paralelo | Guiado | Batch |
| 03_flows/01 a 05 | Flow | — | — (sin LLM) | — | Determinista | Batch |
| 03_flows/06_human_feedback | Flow | — | — | Router | Guiado | Humano en el bucle |
| 03_flows/07_flow_con_agentes | Flow con agentes | — | Salida estructurada | Router | Guiado | Batch |
| 03_flows/08_flow_con_crews | Flow con Crews | Secuencial | Solo LLM | Router, bucle | Guiado | Batch |
| 04_observabilidad/* | Agente o Crew | Secuencial | Herramientas | Hooks, eventos, callbacks | Guiado | Batch |
| 06_integrador/01 | Crew + bucle Python | Secuencial | Herramientas, salida estructurada | Contexto | Guiado | Batch |
| 06_integrador/02 | Flow con Crews | Secuencial | Herramientas, salida estructurada | Router, bucle | Guiado | Batch |
