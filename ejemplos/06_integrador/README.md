# 06 · Integrador

Un caso completo que junta varias piezas: un equipo de investigador, redactor y editor escribe una nota de actualidad con búsquedas web reales, y la corrige hasta que cumple los criterios. Está resuelto de dos formas, para comparar:

| # | Ejemplo | El bucle de corrección está hecho con |
|---|---|---|
| 01 | [redactor_editor](01_redactor_editor) | Un `while` en Python que arma Crews nuevos en cada ronda (el ejemplo original del repo) |
| 02 | [redactor_editor_flow](02_redactor_editor_flow) | Un Flow con `@router` |

Los dos comparten agentes, tareas y la guarda de longitud: la versión Flow importa todo eso de la 01.

## Piezas que usa

| Pieza | Dónde la viste sola |
|---|---|
| Herramientas reales (búsqueda en DuckDuckGo, contar palabras) | [01_agentes/02_herramientas](../01_agentes/02_herramientas) |
| Crew secuencial con contexto | [02_crews/01_secuencial](../02_crews/01_secuencial) |
| JSON validado con Pydantic | [01_agentes/08_salida_estructurada](../01_agentes/08_salida_estructurada) |
| Validación en código de lo que el LLM mide mal | [01_agentes/07_guardrails](../01_agentes/07_guardrails) |
| Router y bucle con tope | [03_flows/08_flow_con_crews](../03_flows/08_flow_con_crews) |
