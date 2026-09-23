# Trampas conocidas

Problemas reales que aparecieron al armar y correr los ejemplos de este repo. Cada uno tiene su **síntoma** (lo que ves), su **causa** (lo que pasa por detrás) y el **arreglo** que usa el repo.

Varios son silenciosos: CrewAI no tira error, simplemente hace otra cosa. Por eso vale la pena conocerlos antes de que te pasen.

**Dónde se observó:** `crewai 1.15.20`, Python 3.12, macOS, Groq con `qwen/qwen3.8-27b` (capa gratuita), LM Studio con `text-embedding-nomic-embed-text-v1.5`, entre el 21 y el 23/09/2026. Con otra versión el comportamiento puede cambiar: antes de quitar un arreglo, comprobá que el problema siga ocurriendo.

Las trampas de conexión con Groq (prefijo `groq/`, modelos `gpt-oss`, `max_tokens`) están en [decisiones-tecnicas.md](decisiones-tecnicas.md).

## Índice

| # | Trampa | Tipo | Ejemplo |
|---|---|---|---|
| 1 | `Agent.kickoff()` ignora `knowledge_sources` | silenciosa | [01_agentes/04_knowledge](../ejemplos/01_agentes/04_knowledge) |
| 2 | Herramientas MCP con nombre ilegible | silenciosa | [01_agentes/03_mcp](../ejemplos/01_agentes/03_mcp) |
| 3 | Resultado MCP truncado al primer bloque | silenciosa | [01_agentes/03_mcp](../ejemplos/01_agentes/03_mcp) |
| 4 | El modelo no usa las herramientas que tiene | comportamiento del LLM | [01_agentes/02_herramientas](../ejemplos/01_agentes/02_herramientas) |
| 5 | Apilar `@listen` pierde disparadores | silenciosa | [03_flows/08_flow_con_crews](../ejemplos/03_flows/08_flow_con_crews) |
| 6 | Un `or_()` de métodos no se vuelve a disparar en un bucle | silenciosa | [06_integrador/02_redactor_editor_flow](../ejemplos/06_integrador/02_redactor_editor_flow) |
| 7 | `Agent.kickoff()` dentro de un Flow devuelve una corrutina | error confuso | [03_flows/07_flow_con_agentes](../ejemplos/03_flows/07_flow_con_agentes) |
| 8 | `step_callback` no se llama con el ejecutor por defecto | silenciosa | [04_observabilidad/03_callbacks](../ejemplos/04_observabilidad/03_callbacks) |
| 9 | Un Flow se cuelga sin acceso a PyPI | cuelgue | todos los Flows |
| 10 | Pánico de Rust al terminar el programa | ruido | todos |
| 11 | Límites de Groq: entrada por minuto (413) y tokens por día (429) | límite externo | [02_crews/02_jerarquico](../ejemplos/02_crews/02_jerarquico) |
| 12 | El LLM se equivoca en datos del dominio | comportamiento del LLM | [02_crews/02_jerarquico](../ejemplos/02_crews/02_jerarquico) |
| 13 | Sin descripciones, la salida estructurada es más pobre | comportamiento del LLM | [01_agentes/08_salida_estructurada](../ejemplos/01_agentes/08_salida_estructurada) |
| 14 | Parámetros deprecados que todavía aparecen en tutoriales | API | [clasificacion.md](clasificacion.md#lo-que-no-se-puede-armar-o-ya-no-conviene) |
| 15 | Rutas de archivos de knowledge relativas a `./knowledge/` | API | [01_agentes/04_knowledge](../ejemplos/01_agentes/04_knowledge) |
| 16 | El servidor de LM Studio se apaga solo | entorno | knowledge y memoria |
| 17 | La planificación del agente sale en inglés | cosmético | [01_agentes/06_planificacion](../ejemplos/01_agentes/06_planificacion) |

---

## 1. `Agent.kickoff()` ignora `knowledge_sources`

**Síntoma.** Un agente con `knowledge_sources` y `embedder` configurados responde "no dispongo de esa información", aunque la respuesta esté en los documentos. No se crea ninguna base vectorial en `db/`.

**Causa.** En 1.15.20 las fuentes se indexan en `Agent.set_knowledge()`, que solo llama `crews/utils.py` al armar un Crew. Y la búsqueda (`handle_knowledge_retrieval`) solo corre en `Agent.execute_task()`, es decir, cuando el agente ejecuta una `Task`. Llamar `set_knowledge()` a mano tampoco alcanza: `kickoff()` nunca consulta.

**Arreglo.** Envolver al agente en un Crew de una sola tarea:

```python
tarea = Task(description=f"Consulta del cliente: {pregunta}", expected_output="...", agent=agente)
Crew(agents=[agente], tasks=[tarea]).kickoff()
```

**Test:** `tests/test_agentes.py::TestKnowledge` verifica que los fragmentos relevantes lleguen al prompt.

## 2. Herramientas MCP con nombre ilegible

**Síntoma.** El agente ve una herramienta llamada `users_mgobea_documents_crew_ai_practices_venv_bin_pytho_b5be08a4` en vez de `buscar_por_autor`. Con varias herramientas, todas se llaman parecido y el modelo solo puede distinguirlas por la descripción.

**Causa.** CrewAI nombra cada herramienta MCP `"<comando>_<argumentos>_<herramienta>"`, la normaliza y la trunca a 64 caracteres (el máximo de OpenAI) reemplazando el final por un hash. Con `command=sys.executable` (un camino absoluto largo), el nombre real de la herramienta es lo que se corta.

**Arreglo.** Comando y argumentos cortos:

```python
MCPServerStdio(command="python", args=[os.path.relpath(SERVIDOR)])
# → python_ejemplos_01_agentes_03_mcp_servidor_py_buscar_por_autor (62 caracteres)
```

Dentro de `uv run`, `python` es el del entorno virtual. **Test:** `TestMCP.test_los_nombres_de_herramienta_entran_en_64_caracteres`.

## 3. Resultado MCP truncado al primer bloque

**Síntoma.** La herramienta devuelve dos libros, pero el agente afirma que "solo figura *Ficciones*".

**Causa.** Cuando una herramienta de FastMCP devuelve una `list`, el protocolo la manda como un bloque de contenido por elemento. `MCPNativeTool._extract_content` de CrewAI 1.15.20 lee solo `content[0]`.

**Arreglo.** Del lado del servidor, devolver un único texto (JSON) en vez de una lista:

```python
return json.dumps(libros, ensure_ascii=False)
```

## 4. El modelo no usa las herramientas que tiene

**Síntoma.** Ante "¿cuánto salen 2 teclados enviados a Córdoba?", el agente no llamó a ninguna herramienta y respondió "en el catálogo tengo varios teclados (gaming, mecánicos...), ¿cuál querés?". Inventó un catálogo que no existe.

**Causa.** No es un bug: las herramientas se enviaron (`tool_choice="auto"`), pero el modelo decidió que le faltaba información. El LLM elige herramientas según su nombre, su docstring y el rol del agente.

**Arreglo.** Decir en la docstring qué valores acepta la herramienta y, en la historia del agente, que consulte antes de responder:

```python
"""Devuelve el precio unitario (en pesos) y el peso (en kg) de un producto del catálogo.
Los productos son genéricos, sin modelos: teclado, mouse, monitor."""
backstory="Antes de responder, consulta cada producto con consultar_producto ..."
```

Con eso, el agente calculó el presupuesto exacto ($54.480).

## 5. Apilar `@listen` pierde disparadores

**Síntoma.** Un Flow con un bucle termina sin error, pero `kickoff()` devuelve `None` y el paso final nunca se ejecuta.

```python
@listen("muy_largo")
@listen(planificar)      # ← este disparador se pierde
async def escribir(self): ...
```

**Causa.** Cada `@listen` guarda *una* condición en el método; el de arriba pisa al de abajo.

**Arreglo.** Una sola condición con `or_`:

```python
@listen(or_(planificar, "muy_largo"))
```

## 6. Un `or_()` de métodos no se vuelve a disparar en un bucle

**Síntoma.** En un bucle editar → reescribir → editar, la segunda edición nunca ocurre y el Flow termina con `None`.

```python
@listen("rechazado")
async def reescribir(self): ...

@listen(or_(investigar, reescribir))   # se dispara con investigar... y nunca más
async def editar(self): ...
```

**Causa.** Un listener `or_()` se dispara una sola vez por ejecución. Solo se vuelve a armar cuando un **router** emite una etiqueta nueva.

**Arreglo.** Hacer que el paso del bucle sea un router que emite su propia etiqueta, y escuchar esa etiqueta:

```python
@router("rechazado")
async def reescribir(self) -> str:
    ...
    return "reescrito"

@listen(or_(investigar, "reescrito"))
async def editar(self): ...
```

**Test:** `tests/test_integrador.py::TestRedactorEditorFlow` recorre una ronda de rechazo y una de aprobación.

## 7. `Agent.kickoff()` dentro de un Flow devuelve una corrutina

**Causa.** Por diseño, `kickoff()` detecta si hay un event loop corriendo (el del Flow) y en ese caso devuelve una corrutina para que el Flow la espere. Si accedés a `.raw` directamente, obtenés un error sobre `coroutine`.

**Arreglo.** Pasos `async` y `await agente.kickoff_async(...)` (lo mismo con `crew.kickoff_async()`). Así el código dice explícitamente lo que pasa.

## 8. `step_callback` no se llama con el ejecutor por defecto

**Síntoma.** `Crew(step_callback=f)` nunca llama a `f`.

**Causa.** En 1.15 el ejecutor por defecto de los agentes es `AgentExecutor` (experimental), que no invoca `step_callback`. Solo lo hace el ejecutor clásico, `CrewAgentExecutor`.

**Arreglo.** `Agent(..., executor_class=CrewAgentExecutor)` en los agentes cuyos pasos quieras observar. Para observar todo sin cambiar el ejecutor, usá eventos ([04_observabilidad/02_eventos](../ejemplos/04_observabilidad/02_eventos)).

## 9. Un Flow se cuelga sin acceso a PyPI

**Síntoma.** `flow.kickoff()` no avanza nunca, ni siquiera en un Flow sin LLM. No hay error.

**Causa.** Al iniciar un Flow, la consola de CrewAI consulta `https://pypi.org/pypi/crewai/json` para avisar si hay una versión nueva. Tiene `timeout=2`, pero ese timeout no cubre la resolución DNS: en una red donde `pypi.org` no resuelve (VPN, proxy corporativo), `getaddrinfo` queda bloqueado indefinidamente.

**Arreglo.** `CREWAI_DISABLE_VERSION_CHECK=true`, que `comun/entorno.py` fija al importar `comun`. Todos los ejemplos importan `comun`, incluso los Flows que no usan LLM.

## 10. Pánico de Rust al terminar el programa

**Síntoma.** Después de imprimir el resultado, aparece:

```
thread 'tokio-runtime-worker' panicked at .../pyo3-0.26.0/src/interpreter_lifecycle.rs:117:13:
assertion `left != right` failed: The Python interpreter is not initialized ...
```

**Causa.** CrewAI importa `lancedb` (el almacenamiento por defecto de la memoria) aunque no uses memoria. Un hilo de fondo de lancedb intenta usar Python mientras el intérprete ya se está cerrando.

**Qué hacer.** Nada: ocurre después de terminar, el código de salida es 0 y los resultados son correctos. Es ruido.

## 11. Límites de Groq: entrada por minuto (413) y tokens por día (429)

**Síntoma.** El Crew jerárquico falla a mitad de camino con:

```
Error code: 413 - Request too large for model `qwen/qwen3.8-27b` ... on input tokens per minute (ITPM):
Limit 7000, Requested 7281
```

**Causa.** En el proceso jerárquico el manager conversa con los trabajadores y el contexto crece con cada delegación. En la capa gratuita de Groq, el límite de *entrada* por minuto (7000 el 23/09/2026) es distinto del de salida (ver [decisiones-tecnicas.md §8](decisiones-tecnicas.md#8-tope-de-tokens-de-salida-max_tokens900)).

**Qué hacer.** Esperar un minuto y reintentar, usar menos tareas, o correr ese ejemplo con otro proveedor (`LLM_PROVEEDOR`). Es un límite de la cuenta, no del código.

**Límite diario.** Además, la capa gratuita tiene un tope de **200.000 tokens por día** (TPD) por modelo. Correr todos los ejemplos del repo en vivo en un mismo día lo alcanza:

```
Error code: 429 - Rate limit reached ... on tokens per day (TPD): Limit 200000, Used 199811, Requested 2153.
Please try again in 14m8.448s.
```

Por eso los tests normales usan un LLM falso ([tests.md](tests.md)) y los de LLM real se activan a mano (`CREW_VIVO=1`). Para practicar mucho, alterná con un modelo local ([proveedores-llm.md](proveedores-llm.md)).

| Límite (qwen3.8-27b, cuenta gratuita, 23/09/2026) | Valor | Error |
|---|---|---|
| Tokens de salida por minuto (OTPM) | 1000 | 429 |
| Tokens de entrada por minuto (ITPM) | 7000 | 413 |
| Tokens por día (TPD) | 200.000 | 429 |

## 12. El LLM se equivoca en datos del dominio

**Síntoma.** En el Crew jerárquico, el "contador" calculó el aguinaldo (SAC) dividiendo el mejor sueldo por 12 ($75.000) en vez de por 2 ($450.000), y agregó que el SAC no tiene aportes, lo cual es falso. En el Flow con Crews, un artículo sobre el dulce de leche atribuyó la receta a un chef inventado.

**Causa.** El rol ("Contador") no le da al modelo conocimiento que no tiene. Escribe con la misma seguridad cuando acierta que cuando inventa.

**Qué hacer.**
- Poner las reglas del dominio en el prompt (el ejemplo agrega la regla del SAC a la historia del contador) o en [knowledge](../ejemplos/01_agentes/04_knowledge).
- Verificar en código lo que se pueda medir (como la guarda de longitud del [integrador](../ejemplos/06_integrador/01_redactor_editor)).
- Para cálculos, dar una herramienta que calcule ([09_ejecucion_de_codigo](../ejemplos/01_agentes/09_ejecucion_de_codigo)).

## 13. Sin descripciones, la salida estructurada es más pobre

**Síntoma.** Con el mismo aviso, `output_pydantic` devolvió `estado: "usado"` y 3 etiquetas. El camino "JSON en texto", que solo lista las claves, devolvió `estado: "poco uso"` y 1 etiqueta.

**Causa.** Con `output_pydantic`, CrewAI le pasa al modelo el esquema completo, incluidos los `Field(description=...)` ("nuevo, usado o no especificado", "entre 2 y 4 etiquetas"). Con JSON en texto, el modelo solo ve lo que escribiste en el prompt.

**Qué hacer.** Describir cada campo, y si usás JSON en texto, copiar esas reglas al `expected_output`.

## 14. Parámetros deprecados que todavía aparecen en tutoriales

| Parámetro | Estado en 1.15.20 | Qué usar |
|---|---|---|
| `Agent(allow_code_execution=True)`, `code_execution_mode` | Deprecado. `CodeInterpreterTool` ya no existe | Un sandbox propio ([09_ejecucion_de_codigo](../ejemplos/01_agentes/09_ejecucion_de_codigo)) |
| `Agent(multimodal=True)` | Deprecado, se elimina en 2.0 | Pasar archivos con `input_files` ([11_multimodal](../ejemplos/01_agentes/11_multimodal)) |
| `Agent(reasoning=True)`, `max_reasoning_attempts` | Deprecado | `planning_config=PlanningConfig(...)` |
| `Task(max_retries=...)` | Deprecado | `guardrail_max_retries` |
| `A2AConfig` | Deprecado | `A2AClientConfig` / `A2AServerConfig` |
| `Process.consensual` | Nunca se implementó (`TODO` en `process.py`) | — |

## 15. Rutas de archivos de knowledge relativas a `./knowledge/`

`TextFileKnowledgeSource(file_paths=["politicas.md"])` busca el archivo en `./knowledge/politicas.md`, relativo al directorio **desde donde corrés**, no al archivo de Python. Pasá un `Path` absoluto (`Path(__file__).with_name("conocimiento") / "politicas.md"`) para que funcione desde cualquier lado.

## 16. El servidor de LM Studio se apaga solo

Entre dos corridas, `lms server status` pasó a "not running" sin que nadie lo apagara. Los tests que necesitan embeddings se omiten con el motivo `no hay servidor de embeddings`, y los ejemplos fallan al conectar. Encendelo con `lms server start` antes de usar knowledge o memoria.

## 17. La planificación del agente sale en inglés

Con `planning_config`, el plan que genera el agente está en inglés aunque todo lo demás esté en español: los prompts internos de CrewAI están en inglés. La respuesta final sale en español. Si te molesta, `PlanningConfig` acepta `system_prompt`, `plan_prompt` y `refine_prompt` propios.
