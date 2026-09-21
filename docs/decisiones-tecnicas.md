# Decisiones técnicas

Por qué [`main.py`](../main.py) es como es. La mayoría de estas decisiones son workarounds de fallos reales encontrados al conectar CrewAI con Groq.

**Versiones donde se observó todo esto:** `crewai 1.15.20`, `litellm 1.100.0`, Python 3.12.13, Groq (capa gratuita), 21/09/2026. Con otras versiones el comportamiento puede ser distinto: antes de "arreglar" un workaround, comprobá si el fallo original sigue ocurriendo.

## 1. Python 3.12, no 3.14

`crewai 1.15.20` declara `Requires-Python: <3.14,>=3.10`. El proyecto fija 3.12 en `.python-version` y `requires-python = ">=3.12,<3.14"`.

## 2. Groq se conecta como API compatible con OpenAI, no con `groq/...`

**Síntoma.** Con `LLM(model="groq/<modelo>")`, la primera llamada falla:

```
GroqException - 'messages.0' : for 'role:system' the following must be satisfied
[('messages.0' : property 'cache_breakpoint' is unsupported)]
```

**Causa.** Los ejecutores de agentes de CrewAI marcan los mensajes con un campo `cache_breakpoint` (`crewai/llms/cache.py`). Los proveedores nativos lo eliminan antes de enviar (`crewai/llms/base_llm.py`), pero la ruta de litellm, que es la que usa el prefijo `groq/`, lo deja pasar y Groq lo rechaza.

**Decisión.** Groq expone el protocolo de OpenAI, así que se usa el proveedor nativo apuntando a su URL:

```python
LLM(
    model=f"openai/{MODELO}",           # "openai/" es el proveedor; MODELO es el id de Groq
    base_url="https://api.groq.com/openai/v1",
    api_key=os.environ["GROQ_API_KEY"],
    custom_openai=True,
    temperature=temperatura,
)
```

Ojo con el nombre: el id de un modelo de Groq puede llevar su propia barra (`openai/gpt-oss-120b`), lo que da `openai/openai/gpt-oss-120b`. CrewAI corta en la primera barra y manda el resto a Groq, que es lo que se quiere.

**Consecuencia.** `litellm` ya no interviene. Quedó instalado por el extra `crewai[litellm]` y se puede quitar con `uv remove litellm`.

**Cuándo revisar.** Si una versión nueva de CrewAI elimina el marcador también en la ruta de litellm, el prefijo `groq/...` volvería a ser viable.

## 3. Modelo por defecto: `qwen/qwen3.8-27b`

`llama-3.3-70b-versatile`, el modelo que se usó al principio, ya no figura en Groq. Entre los modelos de texto que listaba la API estaban `openai/gpt-oss-120b`, `openai/gpt-oss-20b` y `qwen/qwen3.8-27b` (el resto eran de audio, moderación o especializados).

Los dos `gpt-oss` fallan en este crew, con dos síntomas distintos:

| Agente | Mensaje de Groq | Qué pasa |
|---|---|---|
| Investigador | `attempted to call tool 'open_file' which was not in request.tools` | El modelo intenta usar una herramienta de navegación de su entrenamiento que no existe en el pedido. |
| Editor | `attempted to call tool 'json' which was not in request.tools` | El modelo emite el veredicto como una llamada a una función `json` en vez de texto. |

En ambos casos Groq responde 400 y CrewAI no lo recupera: la ejecución se cae. `qwen/qwen3.8-27b` completó las corridas sin esos errores.

El modelo se elige con `GROQ_MODEL` en `.env`, sin tocar el código.

## 4. El veredicto del editor es JSON como texto, no `output_pydantic`

**Síntoma.** Con `output_pydantic=Veredicto` en la tarea del editor y `gpt-oss`, el editor llegaba a un veredicto correcto pero la ejecución caía con el error de la herramienta `json` de arriba. Pedirle "solo JSON" en el prompt, con la herramienta `contar_palabras` disponible, produce el mismo fallo con `gpt-oss`.

**Decisión.** La tarea pide un objeto JSON en `expected_output`, y `leer_veredicto` extrae de la primera `{` a la última `}` y lo valida con Pydantic (`Veredicto`). Si no se puede parsear, devuelve `None` y `evaluar` lo trata como rechazo.

Con `qwen` esto funciona, y también funcionaría con cualquier modelo que devuelva JSON en texto.

## 5. El bucle editor → redactor está en Python, no en CrewAI

CrewAI ejecuta sus tareas en secuencia y no ofrece un bucle condicional entre ellas. Las alternativas eran:

- **Proceso jerárquico** (un manager que delega): depende de que un modelo pequeño delegue bien y tiene un comportamiento difícil de predecir.
- **Flows de CrewAI** (`@router` / `@listen`): sirven, pero suman un concepto para un bucle de tres pasos.
- **Un `while` en Python** (elegido): explícito, con tope de rondas y fácil de depurar.

Estructura: la primera pasada es un Crew con los tres agentes y tres tareas. Cada ronda de corrección es un Crew nuevo con redactor y editor, al que se le pasan las notas, el borrador anterior y las correcciones como texto en la descripción de la tarea (no como `Task`s previas), para no depender de cómo CrewAI arrastra el contexto entre Crews.

## 6. Guarda de longitud en código

**Evidencia.** En las corridas de prueba el editor aprobó:

- Un borrador de **281** palabras, reportando `"palabras": 250`. Su herramienta `contar_palabras` había contado 156: el modelo le pasó el texto incompleto.
- Un borrador de **257** palabras.
- Otros borradores donde reportó 218 y el conteo real era 234.

**Decisión.** `evaluar` recalcula `len(borrador.split())` y, si el editor aprobó pero el conteo real supera `MAX_PALABRAS`, lo trata como rechazo y agrega la corrección. La constante es la misma que usa el prompt del editor.

El editor sigue teniendo `contar_palabras` porque ayuda a que sus correcciones sean concretas, pero su cifra no se toma como verdad.

**Lo que no cubre.** El criterio de "al menos 2 datos concretos que figuren en las notas" lo decide solo el LLM. Es verificable en código de forma parcial (por ejemplo, buscando en el borrador los números de las notas), pero no se implementó.

## 7. Búsqueda con `ddgs` (DuckDuckGo)

Se eligió por ser gratis y no requerir API key, lo que mantiene todo el ejemplo en capas gratuitas. La herramienta pide noticias de la última semana (`timelimit="w"`) y recorta cada resumen a 500 caracteres para cuidar los tokens.

`ddgs` lanza excepción tanto ante un límite de tasa como ante una búsqueda sin resultados. `buscar_noticias` la captura y devuelve el mensaje como texto para que el agente pruebe con otra consulta.

Al investigador se le indica que no puede abrir enlaces, para que trabaje con los resúmenes en vez de intentar navegar (ver punto 3).

## 8. Otros ajustes

- **`max_rpm=20`** en cada Crew: tope prudente de peticiones por minuto, no derivado de un límite medido. Para `qwen/qwen3.8-27b`, la API informó el 21/09/2026 (cabeceras `x-ratelimit-*`) un límite de 1000 peticiones y de 8000 tokens por minuto; el de tokens es el que más probablemente se alcance con notas largas.
- **`CREWAI_TRACING_ENABLED=false`** por defecto, para que CrewAI no pregunte por las trazas al terminar la ejecución.
- **Temperaturas por agente**: 0.1 investigador, 0.5 redactor, 0.0 editor.
