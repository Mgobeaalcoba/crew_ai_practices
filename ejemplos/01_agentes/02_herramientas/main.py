"""Agente con herramientas: tres formas de darle acciones a un agente.

1. `@tool` sobre una función: la forma más corta. La docstring es lo que lee el LLM.
2. Subclase de `BaseTool` con `args_schema`: argumentos validados con Pydantic, caché y límite de usos.
3. `ToolFailure`: la herramienta informa un fallo de forma explícita en vez de devolver un texto cualquiera.

Todas son locales (sin red) para que el foco esté en el mecanismo, no en la API externa.

Uso:
    uv run main.py herramientas "¿Cuánto sale mandar 2 teclados a Córdoba?"
"""

import sys

from crewai import Agent
from crewai.tools import BaseTool, ToolFailure, tool
from pydantic import BaseModel, Field

from comun import crear_llm, describir_llm

CATALOGO = {"teclado": (25_000, 0.8), "mouse": (12_000, 0.2), "monitor": (180_000, 5.5)}  # precio ARS, peso kg
COSTO_POR_KG = {"caba": 1_500, "buenos aires": 2_000, "córdoba": 2_800, "mendoza": 3_200}


@tool("consultar_producto")
def consultar_producto(producto: str) -> str | ToolFailure:
    """Devuelve el precio unitario (en pesos) y el peso (en kg) de un producto del catálogo.
    Los productos son genéricos, sin modelos: teclado, mouse, monitor."""
    clave = producto.strip().lower()
    if clave not in CATALOGO:
        return ToolFailure(message=f"'{producto}' no está en el catálogo. Productos: {', '.join(CATALOGO)}.")
    precio, peso = CATALOGO[clave]
    return f"{clave}: precio unitario ${precio:,}, peso {peso} kg"


class EntradaEnvio(BaseModel):
    peso_kg: float = Field(gt=0, description="Peso total del paquete en kilogramos")
    provincia: str = Field(description="Provincia de destino, por ejemplo 'Córdoba'")


class CalcularEnvio(BaseTool):
    name: str = "calcular_envio"
    description: str = "Calcula el costo de envío en pesos según el peso total y la provincia de destino."
    args_schema: type[BaseModel] = EntradaEnvio
    max_usage_count: int | None = 3  # evita que el agente entre en un bucle de recálculos

    def _run(self, peso_kg: float, provincia: str) -> str | ToolFailure:
        tarifa = COSTO_POR_KG.get(provincia.strip().lower())
        if tarifa is None:
            return ToolFailure(message=f"No hay envíos a '{provincia}'. Destinos: {', '.join(COSTO_POR_KG)}.")
        return f"Envío de {peso_kg} kg a {provincia}: ${round(peso_kg * tarifa):,}"


def construir_agente(llm=None) -> Agent:
    return Agent(
        role="Vendedor de tienda online",
        goal="Responder presupuestos exactos usando solo los datos de las herramientas",
        backstory=(
            "Antes de responder, consulta cada producto con consultar_producto y el envío con calcular_envio. "
            "Nunca inventa precios ni pregunta por modelos: el catálogo no los tiene."
        ),
        llm=llm or crear_llm(0.0),
        tools=[consultar_producto, CalcularEnvio()],
        max_iter=6,
        verbose=True,
    )


def main() -> int:
    pregunta = " ".join(sys.argv[1:]) or "¿Cuánto sale en total comprar 2 teclados y mandarlos a Córdoba?"
    print(f"LLM: {describir_llm()}\n")
    respuesta = construir_agente().kickoff(pregunta)
    print(f"\n=== Presupuesto ===\n{respuesta.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
