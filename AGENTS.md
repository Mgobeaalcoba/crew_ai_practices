# AGENTS.md

Guía para agentes de código (Claude Code, Codex, etc.) que trabajen en este repo. Para el propósito y el uso, ver [README.md](README.md).

## Qué es

Un Crew de CrewAI con tres agentes (investigador → redactor → editor) sobre Groq, con un bucle de revisión escrito en Python. Todo el código está en un solo archivo: [`main.py`](main.py).

## Comandos

```bash
uv sync                                  # instalar dependencias (Python 3.12)
uv run main.py "tema"                    # correr el crew
uv run --no-sync main.py "tema"          # igual, sin re-resolver dependencias (útil sin acceso a PyPI)
```

No hay tests, linter ni CI. La verificación es correr el crew con un tema real y mirar que termine con `APROBADO` y exit code 0. Una corrida completa consume tokens de la capa gratuita de Groq: no la repitas sin necesidad.

## Reglas para no romper cosas

Estas decisiones parecen arbitrarias, pero cada una arregla un fallo real. El porqué, con los mensajes de error, está en [docs/decisiones-tecnicas.md](docs/decisiones-tecnicas.md).

- **No cambies `crear_llm` al prefijo `groq/...`.** Con `crewai 1.15.20` esa ruta (litellm) manda `cache_breakpoint` a Groq y este responde 400. Se usa el proveedor nativo `openai/` con `base_url` de Groq y `custom_openai=True`.
- **No uses `output_pydantic` en la tarea del editor.** Con `gpt-oss` hace que el modelo emita el veredicto como una tool call `json` inexistente. El editor responde JSON como texto y `leer_veredicto` lo valida.
- **No pongas un `openai/gpt-oss-*` como modelo por defecto.** Fallan con el editor. El modelo se elige con `GROQ_MODEL`.
- **No quites la guarda de `evaluar`.** Recalcula el conteo de palabras real porque el editor LLM aprobó borradores de 281 y 257 palabras (máximo 250).
- **No quites `max_tokens` de `crear_llm`.** Sin tope, Groq asume ~1400 tokens de salida y rechaza el pedido con 429 (OTPM 1000 en la cuenta de prueba). Se configura con `GROQ_MAX_TOKENS`.
- **Las tareas del bucle reciben texto, no `Task`s previas.** Las rondas de corrección arman un Crew nuevo de dos agentes y le pasan notas, borrador y correcciones como strings en la descripción.

Si cambiás la versión de `crewai` o de Groq, revisá si esas reglas siguen vigentes antes de tocarlas, y actualizá el documento de decisiones con lo que encuentres.

## Convenciones

- Español en nombres, prompts, mensajes y docs; voseo en los prompts y en la documentación.
- Los criterios de edición y los límites son constantes al inicio de `main.py` (`PALABRAS_OBJETIVO`, `MAX_PALABRAS`, `MIN_DATOS`, `MAX_RONDAS`). Tanto el prompt del editor como la guarda las leen: cambialas ahí, no en los textos.
- Comentarios solo para explicar un porqué no evidente (los workarounds de arriba). No comentes lo que el código ya dice.
- Un archivo, sin paquetes ni capas. Si `main.py` crece lo suficiente como para dividirlo, proponelo antes.

## Secretos

- La key vive en `.env` (ignorado por git). Nunca imprimas ni loguees su valor, ni la copies a otros archivos. Para comprobar que existe, medí la longitud del valor en vez de mostrarlo.
- `.env.example` es la plantilla; no le pongas valores reales.

## Notas de entorno

- Python fijado en 3.12 (`.python-version`, `requires-python = ">=3.12,<3.14"`). `crewai` declara `<3.14`.
- La búsqueda usa `ddgs` (DuckDuckGo), sin key. Depende de la red y puede fallar por límites de tasa; `buscar_noticias` devuelve el error como texto para que el agente reintente.
- Archivos generados que no se versionan: `borrador_final.md`, `.venv/`, `db/`, `__pycache__/`.
