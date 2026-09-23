"""La clase del Crew: une los YAML con el código (LLMs, herramientas, callbacks).

Es la estructura que genera `crewai create crew <nombre>`. Los decoradores registran cada pieza y `@crew`
las junta: `self.agents` y `self.tasks` se llenan solos con los métodos decorados, en orden de definición.
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, after_kickoff, agent, before_kickoff, crew, task

from comun import crear_llm


@CrewBase
class CrewSlogans:
    # Caminos relativos a este archivo (son los valores por defecto; se dejan explícitos para mostrarlos)
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, llm=None) -> None:
        self.llm = llm or crear_llm(0.7)

    @before_kickoff
    def normalizar(self, inputs: dict) -> dict:
        inputs["producto"] = inputs.get("producto", "").strip() or "un mate térmico"
        return inputs

    @agent
    def investigador(self) -> Agent:
        return Agent(config=self.agents_config["investigador"], llm=self.llm)

    @agent
    def publicista(self) -> Agent:
        return Agent(config=self.agents_config["publicista"], llm=self.llm)

    @task
    def analisis(self) -> Task:
        return Task(config=self.tasks_config["analisis"])

    @task
    def slogans(self) -> Task:
        return Task(config=self.tasks_config["slogans"])

    @after_kickoff
    def firmar(self, salida):
        salida.raw = f"{salida.raw}\n\n(generado por CrewSlogans)"
        return salida

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks, process=Process.sequential, verbose=True)
