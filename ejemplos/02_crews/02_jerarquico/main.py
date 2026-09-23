"""Crew jerárquico: un manager decide quién hace cada tarea, revisa el resultado y puede pedir rehacerlo.

Con `Process.hierarchical` las tareas no llevan `agent`: el manager (un agente extra que crea CrewAI) las
reparte entre los "trabajadores" usando herramientas de delegación. Hay dos formas de definir al manager:

- `manager_llm=...`: CrewAI arma un manager genérico con ese LLM.
- `manager_agent=Agent(...)`: vos definís su rol, objetivo y estilo (usar `--manager-propio`).

Es más flexible que el secuencial pero menos predecible y gasta más tokens: el manager también "piensa".

Uso:
    uv run main.py jerarquico
    uv run main.py jerarquico --manager-propio
"""

import sys

from crewai import Agent, Crew, Process, Task

from comun import crear_llm, describir_llm


def construir_crew(manager_propio: bool = False, llm=None, llm_manager=None) -> Crew:
    llm = llm or crear_llm(0.3)
    abogado = Agent(role="Abogado laboral", goal="Explicar derechos laborales en Argentina en lenguaje simple",
                    backstory="Especialista en la Ley de Contrato de Trabajo.", llm=llm)
    # La regla va explícita: sin ella, qwen dividió el sueldo por 12 ($75.000) en vez de por 2 ($450.000)
    contador = Agent(role="Contador", goal="Hacer cálculos de liquidaciones con claridad",
                     backstory=("Muestra cada cuenta paso a paso. Regla del SAC: cada cuota semestral es el 50% "
                                "de la mejor remuneración mensual del semestre."), llm=llm)

    tareas = [
        Task(description="Explicá qué es el SAC (aguinaldo) y cuándo se paga.",
             expected_output="Dos párrafos cortos."),
        Task(description="Calculá el aguinaldo del primer semestre de alguien cuyo mejor sueldo fue $900.000.",
             expected_output="El cálculo paso a paso y el monto final."),
    ]  # sin agent: las asigna el manager

    manager = dict(manager_llm=llm_manager or crear_llm(0.0))
    if manager_propio:
        manager = dict(manager_agent=Agent(
            role="Coordinador de consultas",
            goal="Asignar cada consulta al especialista correcto y verificar que la respuesta sea completa",
            backstory="Jefe de un estudio contable-legal. Delega siempre, no responde él mismo.",
            llm=llm_manager or crear_llm(0.0),
            allow_delegation=True,
        ))
    return Crew(agents=[abogado, contador], tasks=tareas, process=Process.hierarchical, verbose=True, **manager)


def main() -> int:
    print(f"LLM: {describir_llm()}\n")
    salida = construir_crew(manager_propio="--manager-propio" in sys.argv).kickoff()
    for tarea in salida.tasks_output:
        print(f"\n=== {tarea.description[:60]} ===\n{tarea.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
