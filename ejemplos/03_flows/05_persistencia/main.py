"""Persistencia: guardar el estado del Flow para retomarlo en otra ejecución (otro proceso, otro día).

`@persist()` sobre la clase guarda el estado después de cada paso (por defecto en SQLite, dentro de db/).
Para retomar, se llama a `kickoff(inputs={"id": <id guardado>})`: CrewAI carga el estado de ese id antes
de arrancar.

Uso (cada línea es un proceso distinto; el estado sobrevive entre ellos):
    uv run main.py persistencia                 # crea un contador nuevo e imprime su id
    uv run main.py persistencia <id>            # retoma ese contador y le suma 1
"""

import sys

import comun  # noqa: F401  (carga .env y ajustes de entorno; ver comun/entorno.py)
from crewai.flow.flow import Flow, FlowState, start
from crewai.flow.persistence import persist


class EstadoSuscripcion(FlowState):  # FlowState ya trae el campo `id`, obligatorio para persistir
    renovaciones: int = 0
    historial: list[str] = []


@persist()
class FlowSuscripcion(Flow[EstadoSuscripcion]):
    @start()
    def renovar(self) -> int:
        self.state.renovaciones += 1
        self.state.historial.append(f"renovación #{self.state.renovaciones}")
        return self.state.renovaciones


def ejecutar(id_existente: str | None = None) -> EstadoSuscripcion:
    flow = FlowSuscripcion()
    flow.kickoff(inputs={"id": id_existente} if id_existente else None)
    return flow.state


def main() -> int:
    estado = ejecutar(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"id: {estado.id}\nrenovaciones: {estado.renovaciones}\nhistorial: {estado.historial}")
    print(f"\nPara retomar: uv run main.py persistencia {estado.id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
