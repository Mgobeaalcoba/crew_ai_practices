# Cómo se testean agentes, Crews y Flows

Testear código con LLMs tiene dos problemas: cada llamada **cuesta** (tokens, cuota diaria) y **nunca responde igual dos veces**. El repo los resuelve separando los tests en niveles.

## Niveles

| Nivel | Qué usa | Cuándo corre | Qué prueba |
|---|---|---|---|
| **Offline** | `LLMGuionado` (LLM falso) | Siempre | Que el *cableado* sea correcto: qué llega al prompt, qué herramienta se llama, qué rama toma un Flow |
| **Con servicios locales** | LM Studio (embeddings), Docker, servidor MCP | Si el servicio está disponible; si no, se omite con el motivo | Integración real con esos servicios, con el LLM falso |
| **En vivo** | El LLM de `.env` | Solo con `CREW_VIVO=1` | Que el modelo real resuelva la tarea (propiedades, no textos exactos) |

```bash
uv run python -m unittest -b                                  # offline + servicios locales disponibles
CREW_VIVO=1 uv run python -m unittest -b tests.test_vivo      # en vivo (gasta tokens)
uv run python -m unittest -b -v tests.test_flows              # un archivo, con el nombre de cada test
uv run python -m unittest tests.test_crews.TestSecuencial     # una clase, sin -b para ver la salida de CrewAI
```

`-b` guarda la salida (los paneles de CrewAI) y solo la muestra si un test falla.

## El LLM falso: `LLMGuionado`

CrewAI acepta cualquier subclase de `BaseLLM` como LLM de un agente. [`comun/llm_falso.py`](../comun/llm_falso.py) define una que:

1. devuelve respuestas guionadas, en orden (o las calcula con una función);
2. guarda los mensajes que recibió en cada llamada (`llm.llamadas`), para verificar el prompt.

```python
from comun.llm_falso import LLMGuionado, respuesta_final

llm = LLMGuionado(respuestas=[respuesta_final("Una API es un contrato.")])
agente = Agent(role="Profesor", goal="...", backstory="...", llm=llm)

assert agente.kickoff("¿Qué es una API?").raw == "Una API es un contrato."
assert "¿Qué es una API?" in llm.texto_de_llamada(0)
```

### Hacer que el agente use una herramienta

`LLMGuionado` no declara soporte de *function calling*, así que CrewAI le habla en formato **ReAct** (texto). Una respuesta con `Action` hace que CrewAI ejecute la herramienta **de verdad** y le devuelva el resultado en la llamada siguiente:

```python
from comun.llm_falso import usar_herramienta

llm = LLMGuionado(respuestas=[
    usar_herramienta("consultar_producto", '{"producto": "teclado"}'),  # → Action: consultar_producto
    respuesta_final("Sale $25.000"),                                     # → Final Answer: ...
])
agente.kickoff("¿Cuánto sale un teclado?")
assert "precio unitario $25,000" in llm.texto_de_llamada(1)  # el resultado real de la herramienta llegó al LLM
```

Así se prueban herramientas, hooks (que bloquean o modifican llamadas), MCP (con un servidor real) y delegación, sin gastar un token.

### Salidas estructuradas

Para `response_format`, `output_pydantic` o un `LLMGuardrail`, la respuesta final es un JSON:

```python
from tests.utilidades import json_final
LLMGuionado(respuestas=[json_final({"valid": True, "feedback": None})])
```

### Varios agentes con el mismo LLM falso

En un Crew las llamadas se intercalan. En vez de adivinar el orden, `responder_segun` elige la respuesta según el texto del prompt (por ejemplo, el rol del agente, que aparece como `You are <rol>` en el mensaje de sistema):

```python
llm = LLMGuionado(respuestas=responder_segun(
    [("You are Contador", respuesta_final("$450.000")),
     ("3 riesgos", respuesta_final("RIESGO-1"))],
    por_defecto=respuesta_final("ok"),
))
```

## Qué verificar (y qué no)

**Sí:**
- Qué llegó al prompt (`llm.texto_de_llamada(i)`): el contexto de tareas previas, el resultado de una herramienta, la corrección de un guardrail, los fragmentos de knowledge.
- Cuántas llamadas hubo: una `ConditionalTask` salteada no llama al LLM.
- El estado final de un Flow y la rama que tomó.
- La lógica propia (guardas, routers, validadores) con entradas límite.

**No:**
- El texto exacto de una respuesta real. En los tests en vivo se verifican propiedades: "el total contiene 54480", "el post tiene ≤ 280 caracteres y ningún hashtag", "la categoría es `facturacion`".

## Aislamiento

- **Hooks globales**: `clear_all_global_hooks()` en `tearDown`.
- **Listeners de eventos**: `with crewai_event_bus.scoped_handlers():` y `crewai_event_bus.flush()` antes de verificar, porque los handlers corren en segundo plano.
- **Memoria y knowledge**: se guardan en `db/`; los tests hacen `memoria.reset()`.
- **MCP con `-b`**: el cliente stdio necesita un `stderr` real; el test lo restaura con `mock.patch("sys.stderr", sys.__stderr__)`.
- **Entrada humana**: `mock.patch("builtins.input", side_effect=[...])` para `human_input=True`; un `HumanFeedbackProvider` propio para `@human_feedback`.

## Agregar un test para un ejemplo nuevo

1. Escribí el ejemplo de forma que el LLM se pueda inyectar: `def construir_crew(..., llm=None)` con `llm or crear_llm(...)`.
2. En `tests/test_<grupo>.py`, importalo con `ejemplo("<grupo>/<nn_nombre>")`.
3. Guioná las respuestas y verificá el cableado.
4. Si necesita un servicio, usá `@requiere_embeddings`, `@requiere_docker` o `@requiere_vivo`.

Más detalle sobre la estructura de los tests en [tests/README.md](../tests/README.md).
