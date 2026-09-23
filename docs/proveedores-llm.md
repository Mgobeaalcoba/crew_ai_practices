# Proveedores de LLM y de embeddings

Todos los ejemplos crean su LLM con `crear_llm()` ([comun/llm.py](../comun/llm.py)), que elige el proveedor según `.env`. Cambiar de proveedor no requiere tocar código.

## Cómo funciona

Groq, LM Studio, Ollama, OpenAI, Anthropic y Gemini ofrecen una API **compatible con OpenAI** (`POST /v1/chat/completions`). CrewAI tiene un proveedor nativo para OpenAI, así que basta con apuntarlo a otra URL:

```python
LLM(
    model="openai/<modelo>",      # "openai/" = usar el cliente de OpenAI; <modelo> es el id del proveedor
    base_url="<url del proveedor>",
    api_key="<key>",
    custom_openai=True,
)
```

`crear_llm` arma exactamente esto a partir de una tabla (`PROVEEDORES`):

| `LLM_PROVEEDOR` | URL | Key | Modelo por defecto | Costo |
|---|---|---|---|---|
| `groq` *(por defecto)* | `https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `qwen/qwen3.8-27b` | Gratis con límites |
| `lmstudio` | `http://localhost:1234/v1` | — | *(obligatorio `LLM_MODELO`)* | Gratis, local |
| `ollama` | `http://localhost:11434/v1` | — | `qwen3:8b` | Gratis, local |
| `openai` | `https://api.openai.com/v1` | `OPENAI_API_KEY` | *(obligatorio `LLM_MODELO`)* | Pago |
| `anthropic` | `https://api.anthropic.com/v1/` | `ANTHROPIC_API_KEY` | `claude-haiku-4-5` | Pago |
| `gemini` | `https://generativelanguage.googleapis.com/v1beta/openai/` | `GEMINI_API_KEY` | *(obligatorio `LLM_MODELO`)* | Capa gratuita |

Para ver qué proveedor y modelo está usando un ejemplo, fijate en la primera línea que imprime:

```
LLM: groq · qwen/qwen3.8-27b (https://api.groq.com/openai/v1, max_tokens=900)
```

Para comparar todos los que tengas configurados, con la misma pregunta:

```bash
uv run main.py comparar_proveedores
```

## Configurar cada uno

### Groq (nube, gratis)

1. Creá una key en <https://console.groq.com/keys>.
2. En `.env`: `GROQ_API_KEY=gsk_...`

Es el proveedor por defecto y el único con el que se corrieron los ejemplos en vivo (el detalle de cuáles, en [ejemplos/README.md](../ejemplos/README.md#estado-de-verificación)). Sus límites gratuitos (tokens por minuto y por día) se alcanzan fácil: ver [trampas-conocidas.md §11](trampas-conocidas.md#11-límites-de-groq-entrada-por-minuto-413-y-tokens-por-día-429). **No uses los modelos `openai/gpt-oss-*`**: llaman herramientas que no existen ([decisiones-tecnicas.md §3](decisiones-tecnicas.md#3-modelo-por-defecto-qwenqwen38-27b)).

### LM Studio (local)

LM Studio corre modelos en tu máquina, sin internet ni costo.

```bash
lms ls                                  # modelos descargados
lms get qwen/qwen3-4b                   # descargar un modelo de chat (varios GB)
lms load qwen/qwen3-4b                  # cargarlo en memoria
lms server start                        # servidor en http://localhost:1234
```

En `.env`:

```
LLM_PROVEEDOR=lmstudio
LLM_MODELO=qwen/qwen3-4b
```

`LLM_MODELO` tiene que coincidir con un id de `curl http://localhost:1234/v1/models`. Para agentes con herramientas conviene un modelo que soporte *tool calling* (Qwen 3, Llama 3.1+, Mistral). Con modelos chicos (<7B) esperá respuestas más pobres y más errores al usar herramientas.

> El servidor de LM Studio puede apagarse solo ([trampas-conocidas.md §16](trampas-conocidas.md#16-el-servidor-de-lm-studio-se-apaga-solo)). Si un ejemplo no conecta, corré `lms server start`.

### Ollama (local)

```bash
brew install ollama        # o desde https://ollama.com
ollama serve               # servidor en http://localhost:11434
ollama pull qwen3:8b
```

En `.env`: `LLM_PROVEEDOR=ollama` (el modelo por defecto es `qwen3:8b`).

### OpenAI, Anthropic, Gemini

Poné la key correspondiente en `.env`, `LLM_PROVEEDOR` con el nombre del proveedor y, si el proveedor no tiene modelo por defecto, `LLM_MODELO` con un modelo disponible en tu cuenta. No se fijan modelos por defecto para OpenAI ni Gemini porque sus catálogos cambian seguido.

## Tope de tokens de salida

`LLM_MAX_TOKENS` limita la longitud de cada respuesta. Para Groq el repo usa 900 por defecto, porque sin tope Groq rechaza los pedidos ([decisiones-tecnicas.md §8](decisiones-tecnicas.md#8-tope-de-tokens-de-salida-max_tokens900)). Para el resto no hay tope salvo que lo definas.

## Varios proveedores en el mismo programa

`crear_llm` acepta el proveedor y el modelo como parámetros, así que un Crew puede mezclar modelos: uno barato para tareas simples y uno mejor para las difíciles.

```python
investigador = Agent(..., llm=crear_llm(0.1, proveedor="groq"))
editor = Agent(..., llm=crear_llm(0.0, proveedor="anthropic", modelo="claude-sonnet-5"))
Crew(..., manager_llm=crear_llm(0.0, proveedor="lmstudio", modelo="qwen/qwen3-4b"))
```

## Embeddings (knowledge y memoria)

Knowledge y memoria necesitan un **modelo de embeddings**, que es distinto del de chat. Groq no ofrece embeddings, así que el repo usa uno local por defecto ([comun/embeddings.py](../comun/embeddings.py)):

| `EMBEDDINGS_PROVEEDOR` | Modelo por defecto | Cómo prepararlo |
|---|---|---|
| `lmstudio` *(por defecto)* | `text-embedding-nomic-embed-text-v1.5` | `lms get nomic-ai/nomic-embed-text-v1.5` y `lms server start` |
| `ollama` | `nomic-embed-text` | `ollama pull nomic-embed-text` |
| `openai` | `text-embedding-3-small` | `OPENAI_API_KEY` en `.env` |

Los tres se conectan por el protocolo de OpenAI (`POST /v1/embeddings`). Si cambiás de modelo de embeddings, borrá `db/`: los vectores de modelos distintos no son comparables.

> Sin `embedder`, CrewAI usa OpenAI por defecto y pide `OPENAI_API_KEY`, aunque tus agentes usen otro LLM. Por eso los ejemplos lo pasan siempre de forma explícita.

## Alternativa: proveedores nativos de CrewAI

CrewAI también tiene clientes nativos para Anthropic, Gemini, Azure y Bedrock, que se instalan como extras:

```bash
uv add "crewai[anthropic]"      # habilita LLM(model="anthropic/claude-...")
uv add "crewai[google-genai]"   # habilita LLM(model="gemini/gemini-...")
```

Conviene usarlos cuando necesitás funciones propias de cada API que la capa de compatibilidad con OpenAI no expone (por ejemplo, el caché de prompts de Anthropic). El repo no los usa para no sumar dependencias (ver [decisiones-tecnicas.md §12](decisiones-tecnicas.md#12-proveedores-por-su-api-compatible-con-openai)).

Para Groq, **no** uses el prefijo `groq/` (pasa por litellm y Groq responde 400; ver [decisiones-tecnicas.md §2](decisiones-tecnicas.md#2-groq-se-conecta-como-api-compatible-con-openai-no-con-groq)).

## Estado de verificación

| Proveedor | Verificado en este repo |
|---|---|
| Groq (`qwen/qwen3.8-27b`) | Sí, en la mayoría de los ejemplos, entre el 21 y el 23/09/2026 ([detalle](../ejemplos/README.md#estado-de-verificación)) |
| LM Studio (embeddings) | Sí: knowledge y memoria |
| LM Studio (chat), Ollama, OpenAI, Anthropic, Gemini | No: la configuración sigue la documentación de cada proveedor, pero no se probó con un modelo real (no había modelo de chat local ni keys de pago) |
