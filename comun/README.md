# comun/

Piezas compartidas por todos los ejemplos y los tests. Importar el paquete (`import comun` o `from comun import ...`) carga `.env` y fija algunas variables de entorno de CrewAI.

| Archivo | Qué tiene |
|---|---|
| [`llm.py`](llm.py) | `crear_llm()`: crea el LLM del proveedor elegido en `.env` (Groq, LM Studio, Ollama, OpenAI, Anthropic, Gemini). `describir_llm()` y la tabla `PROVEEDORES` |
| [`embeddings.py`](embeddings.py) | `config_embedder()`: configuración de embeddings para knowledge y memoria (LM Studio, Ollama u OpenAI) |
| [`llm_falso.py`](llm_falso.py) | `LLMGuionado`: un LLM que devuelve respuestas fijas, para tests sin red ni tokens. Ayudas `respuesta_final()` y `usar_herramienta()` |
| [`herramientas.py`](herramientas.py) | `buscar_noticias` (DuckDuckGo) y `contar_palabras`, usadas por el integrador |
| [`entorno.py`](entorno.py) | `cargar_entorno()`: `.env`, almacenamiento en `db/`, telemetría y chequeo de versión apagados |

## `crear_llm`

```python
from comun import crear_llm

crear_llm()                                         # proveedor y modelo de .env (Groq por defecto)
crear_llm(0.7)                                      # temperatura
crear_llm(0.0, proveedor="ollama", modelo="llama3.2")
crear_llm(0.2, stop=["\n\n"])                       # parámetros extra de crewai.LLM
```

Errores claros si falta algo: `Falta GROQ_API_KEY en .env...`, `El proveedor 'openai' no tiene modelo por defecto: definí LLM_MODELO`. Detalle en [docs/proveedores-llm.md](../docs/proveedores-llm.md).

## Variables de entorno que fija `entorno.py`

Todas con `setdefault`: si las definís en `.env` o en la terminal, ganan las tuyas.

| Variable | Valor | Por qué |
|---|---|---|
| `CREWAI_STORAGE_DIR` | `<repo>/db` | Knowledge, memoria y estados de Flows quedan dentro del repo (ignorado por git) y no en `~/Library/Application Support` |
| `CREWAI_TRACING_ENABLED` | `false` | Evita la pregunta de trazas al terminar |
| `CREWAI_DISABLE_TELEMETRY`, `OTEL_SDK_DISABLED` | `true` | Sin telemetría anónima |
| `CREWAI_DISABLE_VERSION_CHECK` | `true` | Sin acceso a pypi.org, los Flows se colgaban ([trampas §9](../docs/trampas-conocidas.md#9-un-flow-se-cuelga-sin-acceso-a-pypi)) |

## `LLMGuionado`

```python
from comun import LLMGuionado
from comun.llm_falso import respuesta_final, usar_herramienta

llm = LLMGuionado(respuestas=[
    usar_herramienta("contar_palabras", '{"texto": "hola mundo"}'),
    respuesta_final("2 palabras"),
])
```

Guía completa en [docs/tests.md](../docs/tests.md).
