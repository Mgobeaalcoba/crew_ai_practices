# AGENTS.md

Guía para agentes de código (Claude Code, Codex, etc.) que trabajen en este repo. Para el propósito y el uso, ver [README.md](README.md).

## Qué es

Un repositorio **educativo** de CrewAI: un catálogo de ejemplos ejecutables, uno por cada tipo de agente, Crew o Flow, con documentación didáctica y tests. El público son personas que están aprendiendo CrewAI.

- `main.py`: lanzador que lista y corre los ejemplos (`runpy`).
- `comun/`: piezas compartidas (`crear_llm`, `config_embedder`, `LLMGuionado`, herramientas, entorno).
- `ejemplos/<nn_grupo>/<nn_ejemplo>/main.py` + `README.md`: un concepto por carpeta.
- `tests/`: `unittest` con LLM falso; `test_vivo.py` usa el LLM real.
- `docs/`: conceptos, clasificación, proveedores, tests, trampas conocidas y decisiones técnicas.

## Comandos

```bash
uv sync                                          # instalar dependencias (Python 3.12)
uv run main.py                                   # listar ejemplos
uv run main.py <parte del nombre> [args]         # correr uno
uv run python -m unittest -b                     # tests offline (~20 s, sin tokens)
CREW_VIVO=1 uv run python -m unittest -b tests.test_vivo   # tests con LLM real (gasta tokens)
uv run --offline ...                             # igual, sin tocar PyPI (el entorno original no tenía acceso)
```

**Verificación:** los tests offline tienen que pasar siempre. Para cambios de comportamiento, corré además el ejemplo afectado en vivo **una vez**. La capa gratuita de Groq tiene un tope de 200.000 tokens por día: no corras ejemplos en vivo sin necesidad y no corras todos seguidos.

## Reglas para no romper cosas

Cada una arregla un fallo real. El porqué, con los mensajes de error, está en [docs/decisiones-tecnicas.md](docs/decisiones-tecnicas.md) y [docs/trampas-conocidas.md](docs/trampas-conocidas.md).

**Conexión con Groq (`comun/llm.py`):**
- **No cambies `crear_llm` al prefijo `groq/...`.** Con `crewai 1.15.20` esa ruta (litellm) manda `cache_breakpoint` y Groq responde 400. Se usa `openai/` con `base_url` y `custom_openai=True`.
- **No pongas un `openai/gpt-oss-*` como modelo por defecto.** Llaman herramientas inexistentes (`json`, `open_file`).
- **No quites el `max_tokens` por defecto de Groq (900).** Sin tope, Groq responde 429 (OTPM 1000).

**Integrador (`ejemplos/06_integrador/01_redactor_editor`):**
- **No uses `output_pydantic` en la tarea del editor** (falla con `gpt-oss`). El editor responde JSON como texto y `leer_veredicto` lo valida.
- **No quites la guarda de `evaluar`.** El editor aprobó borradores de 281, 257 y 256 palabras (máximo 250).
- **Las tareas del bucle reciben texto, no `Task`s previas.**

**CrewAI 1.15.20 en general:**
- **Knowledge solo funciona dentro de un Crew** (`Agent.kickoff()` lo ignora).
- **Servidores MCP:** comando y argumentos cortos (los nombres de herramientas se truncan a 64 caracteres), y devolver un solo texto, no listas (CrewAI lee solo el primer bloque).
- **Flows:** nunca apiles `@listen` (usá `or_`). En bucles, el paso que vuelve atrás tiene que ser un `@router` que emita una etiqueta nueva. Dentro de un Flow, usá `await ...kickoff_async()`.
- **No quites `CREWAI_DISABLE_VERSION_CHECK` de `comun/entorno.py`**: sin PyPI, los Flows se cuelgan. Todo ejemplo tiene que importar `comun`, aunque no use LLM.
- **`step_callback` necesita `executor_class=CrewAgentExecutor`.**
- Siempre pasá `embedder=` (knowledge, memoria) y `planning_llm=` (Crew con planning): sin ellos CrewAI usa OpenAI y pide `OPENAI_API_KEY`.

Si cambiás la versión de `crewai`, revisá si estas reglas siguen vigentes antes de tocarlas y actualizá la documentación con lo que encuentres.

## Convenciones

- **Español** en nombres, prompts, mensajes y docs; **voseo** en prompts y documentación.
- **Ejemplos:** un concepto por carpeta; `main.py` con docstring (qué muestra, uso) y `README.md` con esta estructura: qué vas a aprender, cómo funciona (diagrama), código clave, correrlo, qué vas a ver (**salida real**, con fecha), trampas, para experimentar, tests, ver también.
- **El LLM se inyecta:** `construir_*(..., llm=None)` con `llm or crear_llm(...)`, para poder testear con `LLMGuionado`.
- **Comentarios:** en `ejemplos/` pueden explicar conceptos (el repo es didáctico). En `comun/` y `tests/`, solo el porqué no evidente.
- **Cada ejemplo nuevo** lleva test offline en `tests/test_<grupo>.py`, fila en `ejemplos/README.md` (catálogo y estado de verificación) y, si corresponde, en `docs/clasificacion.md`.
- **Honestidad:** si un ejemplo no se pudo correr en vivo, decilo en su README y en la tabla de verificación. No pongas salidas inventadas.
- **Constantes de criterio** (límites, rondas) al inicio del `main.py` de cada ejemplo; los prompts las leen.
- **No cambies `pyproject.toml` ni `uv.lock` sin acceso a PyPI:** un lock desactualizado rompe `uv run`. Por eso los ejemplos se corren como módulos y `comun` no es un paquete instalado ([decisiones §10](docs/decisiones-tecnicas.md#10-estructura-del-repo-ejemplos-como-módulos-no-como-paquete-instalado)).

## Secretos

- Las keys viven en `.env` (ignorado por git). Nunca imprimas ni loguees sus valores, ni los copies a otros archivos. Para comprobar que existe una key, medí su longitud.
- `.env.example` es la plantilla; no le pongas valores reales.

## Notas de entorno

- Python 3.12 (`.python-version`, `requires-python = ">=3.12,<3.14"`).
- Embeddings: LM Studio en `:1234` con `text-embedding-nomic-embed-text-v1.5`. El servidor se apaga solo: `lms server start`.
- Docker para `09_ejecucion_de_codigo` (`SANDBOX_IMAGEN`).
- La búsqueda usa `ddgs` (DuckDuckGo), sin key; puede fallar por límites de tasa.
- Al terminar, puede aparecer un pánico de Rust (`pyo3`, `tokio-runtime-worker`): es `lancedb` cerrándose. Ruido inofensivo.
- Archivos generados que no se versionan: `borrador_final.md`, `.venv/`, `db/`, `__pycache__/`.
