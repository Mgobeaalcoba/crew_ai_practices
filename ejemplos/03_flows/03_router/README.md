# 03 · Router

> Un Flow que aprueba, deriva a revisión o rechaza un crédito según el puntaje.

## Qué vas a aprender

- `@router(paso)`: devolver una etiqueta que decide la rama.
- `@listen("etiqueta")`: los pasos de cada rama.
- La base para armar bucles.

## Cómo funciona

```mermaid
flowchart LR
    E["evaluar<br/>@start"] --> R{"decidir<br/>@router"}
    R -- '"aprobado"' --> A[aprobar]
    R -- '"revision"' --> V[pedir_revision]
    R -- '"rechazado"' --> X[rechazar]
```

## El código clave

```python
@router(evaluar)
def decidir(self) -> str:
    if self.state.puntaje >= 700:
        return "aprobado"
    if self.state.puntaje >= 500:
        return "revision"
    return "rechazado"

@listen("aprobado")
def aprobar(self):
    self.state.decision = "Crédito aprobado automáticamente"
```

## Bucles

Un paso puede escuchar una etiqueta que emite un router **posterior**, y así volver atrás. Así funcionan los bucles de corrección de [08_flow_con_crews](../08_flow_con_crews) y del [integrador](../../06_integrador/02_redactor_editor_flow). Poné siempre un tope (un contador en el estado) y leé la [trampa §6](../../../docs/trampas-conocidas.md#6-un-or_-de-métodos-no-se-vuelve-a-disparar-en-un-bucle).

## Correrlo

```bash
uv run main.py flows/03_router            # prueba 820, 610 y 300
uv run main.py flows/03_router 450 700
```

## Qué vas a ver

```
Evaluando puntaje 820
  → Crédito aprobado automáticamente
Evaluando puntaje 610
  → Pasa a revisión manual de un analista
Evaluando puntaje 300
  → Crédito rechazado
```

## Para experimentar

1. Reemplazá la regla por un agente que decida (como en [07_flow_con_agentes](../07_flow_con_agentes)).
2. Agregá una rama "fraude" si el puntaje es negativo.

## Tests

`tests/test_flows.py::TestRouter`: las tres ramas.
