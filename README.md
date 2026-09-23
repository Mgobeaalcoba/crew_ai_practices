# crew-practices

Un repositorio para **aprender CrewAI haciendo**: 33 ejemplos ejecutables (y uno documentado) que cubren todos los tipos de agentes, Crews y Flows que se pueden armar con [CrewAI](https://docs.crewai.com/). Cada uno tiene su código comentado, su README con la salida real y sus tests.

Funciona gratis: por defecto usa [Groq](https://groq.com/) (capa gratuita) como LLM y [LM Studio](https://lmstudio.ai/) local para los embeddings. Se puede cambiar a Ollama, OpenAI, Anthropic o Gemini sin tocar código.

## ¿Qué vas a encontrar?

| Si querés... | Andá a |
|---|---|
| Entender qué es cada pieza (agente, tarea, Crew, Flow...) | [docs/conceptos.md](docs/conceptos.md) |
| Ver **qué tipos de cosas** se pueden armar y cómo clasificarlas | [docs/clasificacion.md](docs/clasificacion.md) |
| Correr ejemplos | [ejemplos/](ejemplos) |
| Evitar los problemas que ya encontramos | [docs/trampas-conocidas.md](docs/trampas-conocidas.md) |
| Testear agentes sin gastar tokens | [docs/tests.md](docs/tests.md) |
| Usar otro proveedor de LLM | [docs/proveedores-llm.md](docs/proveedores-llm.md) |

## Inicio rápido

### 1. Requisitos

- [uv](https://docs.astral.sh/uv/) (maneja Python y las dependencias).
- Python 3.12 (uv lo instala solo; `crewai 1.15.20` no soporta 3.14).
- Una API key gratuita de Groq: <https://console.groq.com/keys>.
- Opcionales:
  - [LM Studio](https://lmstudio.ai/) para los ejemplos de knowledge y memoria.
  - [Docker](https://www.docker.com/) para el de ejecución de código.

### 2. Instalación

```bash
git clone <este repo> && cd crew_ai_practices
uv sync
cp .env.example .env
```

Abrí `.env` y pegá tu key:

```
GROQ_API_KEY=gsk_...
```

### 3. Tu primer agente

```bash
uv run main.py agente_solo "¿Qué es una API?"
```

Vas a ver el razonamiento del agente en la terminal y, al final, una respuesta libre y otra estructurada (JSON).

### 4. Ver todos los ejemplos

```bash
uv run main.py
```

```
01_agentes
  01_agente_solo
  02_herramientas
  03_mcp
  ...
06_integrador
  01_redactor_editor
  02_redactor_editor_flow
```

Corré cualquiera con una parte de su nombre: `uv run main.py router`, `uv run main.py jerarquico`...

### 5. Correr los tests

```bash
uv run python -m unittest -b
```

78 tests en ~20 segundos, **sin gastar tokens**: usan un LLM falso (ver [docs/tests.md](docs/tests.md)).

## Qué se puede armar con CrewAI

Resumen de [docs/clasificacion.md](docs/clasificacion.md). CrewAI no tiene "tipos de agente" oficiales: tiene piezas que se combinan. Este repo las ordena con siete criterios:

| Criterio | Valores | Ejemplos |
|---|---|---|
| **Unidad de orquestación** | Agente solo · Crew · Flow · Flow con Crews | [01_agente_solo](ejemplos/01_agentes/01_agente_solo), [02_crews](ejemplos/02_crews), [03_flows](ejemplos/03_flows) |
| **Proceso** | Secuencial · Jerárquico | [01_secuencial](ejemplos/02_crews/01_secuencial), [02_jerarquico](ejemplos/02_crews/02_jerarquico) |
| **Capacidades del agente** | Herramientas · MCP · Knowledge · Memoria · Planificación · Guardrails · Salida estructurada · Código · A2A · Delegación · Multimodal | [01_agentes](ejemplos/01_agentes) |
| **Control de tareas** | Contexto · Asíncronas · Condicionales · Con humano · Callbacks | [02_crews](ejemplos/02_crews) |
| **Autonomía** | Determinista → Guiado → Autónomo | [clasificacion.md §5](docs/clasificacion.md#5-por-grado-de-autonomía) |
| **Interacción** | Batch · Humano en el bucle | [07_humano_en_el_bucle](ejemplos/02_crews/07_humano_en_el_bucle), [06_human_feedback](ejemplos/03_flows/06_human_feedback) |
| **Definición y despliegue** | Script · Proyecto YAML · CrewAI AMP | [08_proyecto_yaml](ejemplos/02_crews/08_proyecto_yaml) |

**Además de agentes**, con CrewAI se arman Flows sin LLM (orquestación con estado, ramas y persistencia), herramientas, servidores MCP y A2A, bases de knowledge, memoria independiente, guardrails, hooks y listeners de eventos, y LLMs propios.

## Estructura

```
main.py                     lanzador: lista y corre los ejemplos
comun/                      piezas compartidas: crear_llm, embeddings, LLM falso, herramientas
ejemplos/
├── 01_agentes/             una capacidad de agente por ejemplo (11)
├── 02_crews/               procesos y control de tareas (9)
├── 03_flows/               orquestación con Flows (8)
├── 04_observabilidad/      hooks, eventos, callbacks (3)
├── 05_proveedores_llm/     el mismo agente en varios proveedores (1)
└── 06_integrador/          un caso completo, con bucle en Python y como Flow (2)
tests/                      tests offline con LLM falso + tests en vivo opcionales
docs/                       conceptos, clasificación, proveedores, tests, trampas, decisiones
.env.example                plantilla de configuración
AGENTS.md                   guía para agentes de código (Claude Code, Codex...)
```

Cada carpeta tiene su propio `README.md`.

## Configuración

Todo se configura en `.env` (ver [.env.example](.env.example)):

| Variable | Para qué | Por defecto |
|---|---|---|
| `GROQ_API_KEY` | Key de Groq | — (obligatoria con Groq) |
| `LLM_PROVEEDOR` | `groq`, `lmstudio`, `ollama`, `openai`, `anthropic`, `gemini` | `groq` |
| `LLM_MODELO` | Modelo del proveedor | `qwen/qwen3.8-27b` en Groq |
| `LLM_MAX_TOKENS` | Tope de tokens por respuesta | `900` en Groq |
| `EMBEDDINGS_PROVEEDOR` | `lmstudio`, `ollama`, `openai` | `lmstudio` |
| `SANDBOX_IMAGEN` | Imagen de Docker para ejecutar código | `python:3.12-slim` |
| `CREW_VIVO` | `1` activa los tests con LLM real | — |

## Límites conocidos

- **Capa gratuita de Groq:** 1000 tokens de salida y 7000 de entrada por minuto, y **200.000 por día**. Correr todos los ejemplos seguidos alcanza el límite diario. Ver [trampas §11](docs/trampas-conocidas.md#11-límites-de-groq-entrada-por-minuto-413-y-tokens-por-día-429).
- **Versión fija:** todo se verificó con `crewai 1.15.20`. Varias trampas documentadas dependen de esa versión.
- **Verificación parcial:** la mayoría de los ejemplos se corrieron en vivo, pero no todos. A2A y multimodal no se pudieron ejecutar, y los proveedores distintos de Groq no se probaron con un modelo de chat real. Detalle en [ejemplos/README.md](ejemplos/README.md#estado-de-verificación).
- **Los LLM se equivocan:** los ejemplos muestran casos reales de datos inventados y cálculos mal hechos. Nada de lo que generan los agentes está verificado contra la realidad salvo donde el código lo controla.
- **Extras no instalados:** `crewai[a2a]`, `crewai[tools]`, `crewai[anthropic]` y `crewai[google-genai]` no están en las dependencias. Los ejemplos que los mencionan explican cómo agregarlos.

## Licencia

[MIT](LICENSE).
