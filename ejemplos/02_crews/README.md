# 02 · Crews

Un Crew es un **equipo**: varios agentes, varias tareas y un proceso que define quién hace qué y en qué orden. Este grupo recorre los procesos y las formas de controlar las tareas.

| # | Ejemplo | Qué muestra |
|---|---|---|
| 01 | [secuencial](01_secuencial) | El proceso básico: tareas en orden, cada una con el contexto de las anteriores |
| 02 | [jerarquico](02_jerarquico) | Un manager LLM reparte el trabajo y revisa |
| 03 | [delegacion](03_delegacion) | Un agente le pide ayuda a otro por su cuenta |
| 04 | [tareas_condicionales](04_tareas_condicionales) | Una tarea que se ejecuta solo si la anterior cumple una condición |
| 05 | [tareas_asincronas](05_tareas_asincronas) | Tareas independientes en paralelo y una que junta los resultados |
| 06 | [planificacion](06_planificacion) | Un planificador que arma el plan de todas las tareas antes de empezar |
| 07 | [humano_en_el_bucle](07_humano_en_el_bucle) | Una persona aprueba o corrige una tarea |
| 08 | [proyecto_yaml](08_proyecto_yaml) | Agentes y tareas en YAML con `@CrewBase` (el formato de `crewai create crew`) |
| 09 | [ejecucion_multiple](09_ejecucion_multiple) | Variables, `kickoff_for_each` y ejecución asíncrona |

## Anatomía de un Crew

```python
from crewai import Agent, Crew, Process, Task

investigador = Agent(role=..., goal=..., backstory=..., llm=...)
redactor = Agent(...)

investigar = Task(description="Investigá {tema}", expected_output="...", agent=investigador)
redactar = Task(description="Escribí un artículo", expected_output="...", agent=redactor,
                context=[investigar])            # recibe la salida de investigar

crew = Crew(
    agents=[investigador, redactor],
    tasks=[investigar, redactar],
    process=Process.sequential,                  # o Process.hierarchical + manager_llm
    verbose=True,
)
salida = crew.kickoff(inputs={"tema": "el mate"})  # {tema} se completa en todos los textos

salida.raw                  # texto de la última tarea
salida.tasks_output         # la salida de cada tarea
salida.pydantic             # si la última tarea tiene output_pydantic
salida.token_usage          # tokens consumidos
```

## Secuencial o jerárquico

| | Secuencial | Jerárquico |
|---|---|---|
| Quién asigna las tareas | Vos (`agent=` en cada Task) | El manager |
| Orden | El de la lista | El manager decide |
| Revisión de resultados | No (salvo guardrails) | El manager puede pedir rehacer |
| Costo | Una llamada por paso de cada agente | Más: el manager también razona y delega |
| Predecible | Sí | Menos |

Más criterios en [docs/clasificacion.md](../../docs/clasificacion.md#2-por-proceso-del-crew).
