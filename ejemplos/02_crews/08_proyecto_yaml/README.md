# 08 · Proyecto con YAML y `@CrewBase`

> El formato "de proyecto" de CrewAI: los textos de agentes y tareas viven en archivos YAML y una clase decorada los arma.

## Qué vas a aprender

- La estructura que genera `crewai create crew <nombre>`.
- Los decoradores `@CrewBase`, `@agent`, `@task`, `@crew`, `@before_kickoff` y `@after_kickoff`.
- Por qué separar textos de código.

## Estructura

```
08_proyecto_yaml/
├── config/
│   ├── agents.yaml     investigador, publicista: role, goal, backstory
│   └── tasks.yaml      analisis, slogans: description, expected_output, agent
├── crew.py             class CrewSlogans (@CrewBase)
└── main.py             punto de entrada
```

## Cómo se conectan

```yaml
# config/agents.yaml
investigador:
  role: Investigador de {producto}
  goal: ...
```

```python
# crew.py
@CrewBase
class CrewSlogans:
    agents_config = "config/agents.yaml"     # relativo a este archivo
    tasks_config = "config/tasks.yaml"

    @agent
    def investigador(self) -> Agent:          # el nombre del método = la clave del YAML
        return Agent(config=self.agents_config["investigador"], llm=self.llm)

    @task
    def analisis(self) -> Task:
        return Task(config=self.tasks_config["analisis"])

    @crew
    def crew(self) -> Crew:
        return Crew(agents=self.agents, tasks=self.tasks)   # se llenan solos con los métodos decorados
```

| Decorador | Qué hace |
|---|---|
| `@CrewBase` | Carga los YAML y registra los métodos decorados |
| `@agent` / `@task` | Registra un agente o una tarea; `self.agents` y `self.tasks` los juntan en orden |
| `@crew` | Arma el Crew final |
| `@before_kickoff` | Recibe y puede modificar los `inputs` (acá, completa un producto vacío) |
| `@after_kickoff` | Recibe y puede modificar la salida (acá, agrega una firma) |

## Por qué YAML

- Ajustar prompts sin tocar Python (o que lo haga alguien que no programa).
- Diffs limpios cuando cambia un texto.
- Es el formato que entiende la CLI (`crewai run`, `crewai train`, `crewai test`) y la plataforma AMP.

## Correrlo

```bash
uv run main.py proyecto_yaml "una bicicleta eléctrica plegable"
uv run main.py proyecto_yaml          # sin producto: before_kickoff pone "un mate térmico"
```

## Qué vas a ver

La salida real del 23/09/2026, sin producto:

```
=== Slogans ===
Aquí tienes 3 slogans memorables para el mate térmico:
1. Tu ritual, sin excusas.
2. Calor perfecto, diseño impecable.
3. Independencia en cada sorbo.

(generado por CrewSlogans)
```

## Para experimentar

1. Cambiá el `backstory` del publicista en el YAML, sin tocar Python.
2. Agregá un tercer agente "traductor" y una tarea que traduzca los slogans al inglés.
3. Generá un proyecto real con `uv run crewai create crew mi_proyecto` y compará la estructura.

## Tests

`tests/test_crews.py::TestProyectoYaml`: los agentes salen del YAML, `before_kickoff` completa el input y `after_kickoff` firma la salida.
