# config/

Los archivos que carga `@CrewBase` en [crew.py](../crew.py):

- `agents.yaml`: un bloque por agente (`role`, `goal`, `backstory`). La clave tiene que coincidir con un método `@agent`.
- `tasks.yaml`: un bloque por tarea (`description`, `expected_output`, `agent`). La clave tiene que coincidir con un método `@task`, y `agent` con una clave de `agents.yaml`.

Los `{textos}` entre llaves se completan con `crew.kickoff(inputs={...})`. `>` en YAML une las líneas en un solo párrafo.
