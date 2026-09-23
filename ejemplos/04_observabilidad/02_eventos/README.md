# 02 · Eventos

> Un listener que registra cuándo arranca y termina un Crew, cada tarea terminada, las llamadas al LLM y los tokens, sin tocar el código del Crew.

## Qué vas a aprender

- El bus de eventos de CrewAI y la clase `BaseEventListener`.
- Suscribirse a eventos concretos con `@bus.on(TipoDeEvento)`.
- Aislar y esperar los handlers (`scoped_handlers`, `flush`).

## Cómo funciona

CrewAI emite eventos para casi todo:

| Área | Eventos (algunos) |
|---|---|
| Crew | `CrewKickoffStartedEvent`, `CrewKickoffCompletedEvent`, `CrewKickoffFailedEvent` |
| Tareas | `TaskStartedEvent`, `TaskCompletedEvent`, `TaskFailedEvent` |
| Agentes | `AgentExecutionStartedEvent`, `AgentExecutionCompletedEvent` |
| LLM | `LLMCallStartedEvent`, `LLMCallCompletedEvent` (con `usage`), `LLMStreamChunkEvent` |
| Herramientas | `ToolUsageStartedEvent`, `ToolUsageFinishedEvent`, `ToolUsageErrorEvent` |
| Flows | `FlowStartedEvent`, `MethodExecutionStartedEvent`, `FlowFinishedEvent` |
| Otros | memoria, knowledge, guardrails, MCP, A2A |

Los tipos están en `crewai.events.types.*`. Los handlers corren en segundo plano: no frenan al Crew, pero hay que esperarlos (`flush()`) antes de leer lo que acumularon.

## El código clave

```python
class Metricas(BaseEventListener):
    def setup_listeners(self, bus) -> None:
        @bus.on(LLMCallCompletedEvent)
        def al_responder_llm(fuente, evento):
            self.tokens += (evento.usage or {}).get("total_tokens", 0)

with crewai_event_bus.scoped_handlers():   # los handlers se quitan al salir
    metricas = Metricas()
    crew.kickoff()
    crewai_event_bus.flush()
```

## Correrlo

```bash
uv run main.py eventos
```

## Qué vas a ver

La salida real del 23/09/2026:

```
=== Lo que registró el listener ===
  - crew 'taller de poesía' iniciado
  - tarea terminada: Escribí un haiku sobre el colectivo a la mañana....
  - tarea terminada: Comentá el haiku en una oración....
  - crew terminado en 6.8 s
  - 2 llamadas al LLM, 266 tokens
```

## Para experimentar

1. Calculá el costo estimado con un precio por token.
2. Escuchá `ToolUsageFinishedEvent` en el ejemplo de [herramientas](../../01_agentes/02_herramientas) y registrá la duración de cada herramienta.
3. Mandá los eventos a un archivo JSON Lines.

## Tests

`tests/test_observabilidad.py::TestEventos`.
