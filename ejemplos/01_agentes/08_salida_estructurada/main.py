"""Salida estructurada: que el agente devuelva datos (un objeto Pydantic) en vez de texto libre.

Tres caminos, del más cómodo al más robusto:

1. `Task(output_pydantic=Modelo)`: CrewAI le pide al modelo esa estructura y la valida. `salida.pydantic`
   es un objeto `Modelo`. Existe también `output_json=Modelo`, que deja un dict en `salida.json_dict`.
2. `Agent.kickoff(..., response_format=Modelo)`: lo mismo sin Crew (ver ejemplo 01).
3. Pedir JSON en el prompt y validarlo vos con `Modelo.model_validate_json`. Es lo que usa el ejemplo
   integrador, porque con los modelos `gpt-oss` de Groq los caminos 1 y 2 fallan (docs/decisiones-tecnicas.md).

Uso:
    uv run main.py salida_estructurada "Vendo bici rodado 29, poco uso, $350.000, zona Palermo"
"""

import sys

from crewai import Agent, Crew, Task
from pydantic import BaseModel, Field, ValidationError

from comun import crear_llm, describir_llm


class Aviso(BaseModel):
    producto: str
    precio: int | None = Field(description="Precio en pesos, sin puntos ni símbolo. null si no figura")
    estado: str = Field(description="nuevo, usado o no especificado")
    ubicacion: str | None = None
    etiquetas: list[str] = Field(description="Entre 2 y 4 etiquetas en minúscula")


def construir_agente(llm=None) -> Agent:
    return Agent(
        role="Clasificador de avisos",
        goal="Extraer datos estructurados de avisos clasificados escritos a mano",
        backstory="No inventa datos: si algo no figura en el aviso, lo deja vacío.",
        llm=llm or crear_llm(0.0),
    )


def extraer_con_output_pydantic(aviso: str, llm=None) -> Aviso:
    agente = construir_agente(llm)
    tarea = Task(
        description=f"Extraé los datos de este aviso:\n{aviso}",
        expected_output="Los datos del aviso.",
        agent=agente,
        output_pydantic=Aviso,
    )
    return Crew(agents=[agente], tasks=[tarea]).kickoff().pydantic


def extraer_con_json_en_texto(aviso: str, llm=None) -> Aviso | None:
    agente = construir_agente(llm)
    tarea = Task(
        description=f"Extraé los datos de este aviso:\n{aviso}",
        expected_output=(
            "Solo un objeto JSON, sin texto alrededor, con las claves: producto (string), precio (entero o null), "
            "estado (string), ubicacion (string o null) y etiquetas (lista de strings)."
        ),
        agent=agente,
    )
    texto = Crew(agents=[agente], tasks=[tarea]).kickoff().raw
    try:
        # Se recorta de la primera "{" a la última "}" por si el modelo agrega texto o ```json alrededor
        return Aviso.model_validate_json(texto[texto.find("{") : texto.rfind("}") + 1])
    except ValidationError:
        return None


def main() -> int:
    aviso = " ".join(sys.argv[1:]) or "Vendo bici rodado 29 poco uso, cambios Shimano. $350.000 charlables. Palermo."
    print(f"LLM: {describir_llm()}\n")

    print("=== 1. output_pydantic ===")
    print(extraer_con_output_pydantic(aviso).model_dump_json(indent=2))

    print("\n=== 3. JSON en texto + validación propia ===")
    resultado = extraer_con_json_en_texto(aviso)
    print(resultado.model_dump_json(indent=2) if resultado else "El modelo no devolvió un JSON válido")
    return 0


if __name__ == "__main__":
    sys.exit(main())
