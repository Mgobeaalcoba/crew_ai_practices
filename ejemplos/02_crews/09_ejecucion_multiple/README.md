# 09 · Ejecutar un Crew muchas veces

> Un Crew como plantilla: el mismo guía de turismo para Salta, Ushuaia y Mendoza, en secuencia o en paralelo.

## Qué vas a aprender

- Variables `{así}` en los textos, completadas con `kickoff(inputs={...})`.
- `kickoff_for_each`: una corrida por cada input.
- `kickoff_async` con `asyncio.gather`: varias corridas en paralelo.

## El código clave

```python
guia = Agent(role="Guía de turismo de {ciudad}", goal="Recomendar planes auténticos en {ciudad}", ...)
plan = Task(description="Recomendá un plan de un día en {ciudad}.", ...)

crew.kickoff(inputs={"ciudad": "Córdoba"})                                  # una vez
crew.kickoff_for_each(inputs=[{"ciudad": "Salta"}, {"ciudad": "Ushuaia"}])  # en secuencia

async def en_paralelo():
    return await asyncio.gather(*(construir_crew().kickoff_async(inputs=i) for i in CIUDADES))
```

En paralelo, cada corrida usa **su propio Crew** (`construir_crew()` dentro del `gather`): una misma instancia no debe ejecutarse dos veces al mismo tiempo, porque comparte estado.

## Correrlo

```bash
uv run main.py ejecucion_multiple
```

Son 7 corridas (1 + 3 + 3). En la capa gratuita de Groq, las 3 en paralelo pueden chocar con el límite por minuto.

> No se verificó en vivo: se agotó la cuota diaria de Groq. Los tests offline verifican la interpolación de variables y la ejecución en paralelo.

## Para experimentar

1. Agregá una segunda variable `{estacion}` ("invierno", "verano").
2. Medí el tiempo de `kickoff_for_each` contra la versión en paralelo.
3. Probá `crew.akickoff(...)`, la variante asíncrona nativa.

## Tests

`tests/test_crews.py::TestEjecucionMultiple`: cada corrida recibe su ciudad, en secuencia y en paralelo.
