"""Guardrails: validar la salida de un agente y devolvérsela para que la corrija si no cumple.

Un guardrail recibe la salida y devuelve `(True, valor)` si la acepta o `(False, "motivo")` si no. Si falla,
CrewAI le reenvía al agente el motivo y le pide otra respuesta, hasta `guardrail_max_retries` veces.

Hay dos tipos y se pueden combinar en una lista (se evalúan en orden):
- Función de Python: determinista, gratis, ideal para lo medible (longitud, formato, palabras prohibidas).
- Texto: CrewAI crea un `LLMGuardrail`, que le pregunta a un LLM si se cumple el criterio. Sirve para lo
  subjetivo (tono, relevancia), pero cuesta tokens y puede equivocarse.

Uso:
    uv run main.py guardrails "el lanzamiento de una app de delivery en bicicleta"
"""

import re
import sys

from crewai import Agent, Crew, Task
from crewai.tasks.task_output import TaskOutput

from comun import crear_llm, describir_llm

MAX_CARACTERES = 280


def entra_en_un_post(salida: TaskOutput) -> tuple[bool, str]:
    texto = salida.raw.strip().strip('"')
    if len(texto) > MAX_CARACTERES:
        return False, f"Tiene {len(texto)} caracteres y el máximo es {MAX_CARACTERES}. Acortalo."
    return True, texto  # el valor devuelto reemplaza a la salida: acá, sin comillas sueltas


def sin_hashtags(salida: TaskOutput) -> tuple[bool, str]:
    encontrados = re.findall(r"#\w+", salida.raw)
    if encontrados:
        return False, f"No uses hashtags. Sacá: {', '.join(encontrados)}"
    return True, salida.raw


def construir_crew(tema: str, llm=None) -> Crew:
    redactor = Agent(
        role="Community manager",
        goal="Escribir posts breves y atractivos para redes sociales",
        backstory="Escribe en español rioplatense, con energía y sin exagerar.",
        llm=llm or crear_llm(0.8),
    )
    post = Task(
        description=f"Escribí un post para redes sociales sobre: {tema}. Devolvé solo el texto del post.",
        expected_output="El texto del post, listo para publicar.",
        agent=redactor,
        guardrails=[
            entra_en_un_post,
            sin_hashtags,
            # Un texto se convierte en un LLMGuardrail que usa el LLM del agente
            "El post no promete cosas imposibles de verificar (por ejemplo, 'el mejor del mundo')",
        ],
        guardrail_max_retries=3,
    )
    return Crew(agents=[redactor], tasks=[post])


def main() -> int:
    tema = " ".join(sys.argv[1:]) or "el lanzamiento de una app de delivery en bicicleta en Rosario"
    print(f"LLM: {describir_llm()}\n")
    salida = construir_crew(tema).kickoff()
    print(f"\n=== Post aprobado ({len(salida.raw)} caracteres) ===\n{salida.raw}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
