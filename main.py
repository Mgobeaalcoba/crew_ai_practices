"""Crew de tres agentes (investigador -> redactor -> editor) sobre Groq.

Uso:
    uv run main.py "tema a investigar"
    uv run main.py            # el investigador elige un tema tecnológico de hoy
"""

import os
import sys
from datetime import date
from pathlib import Path

from crewai import LLM, Agent, Crew, Process, Task
from crewai.tools import tool
from ddgs import DDGS
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()
os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")  # evita la pregunta de trazas al terminar

# Criterios de la edición: el editor y la guarda del código leen las mismas constantes.
PALABRAS_OBJETIVO = 200
MAX_PALABRAS = 250
MIN_DATOS = 2
MAX_RONDAS = 3

# gpt-oss-120b/20b fallan con el editor en Groq (emiten el JSON como una tool call "json" inexistente)
MODELO = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
# Groq rechaza (429) pedidos cuyo máximo de salida supera el límite de tokens de salida por minuto del modelo
# (1000 en la cuenta de prueba). Sin tope explícito asume ~1400 y falla desde la primera llamada.
MAX_TOKENS_SALIDA = int(os.getenv("GROQ_MAX_TOKENS", "900"))
TEMA_POR_DEFECTO = "el tema de tecnología más relevante de hoy"


def contar(texto: str) -> int:
    return len(texto.split())


@tool("buscar_noticias")
def buscar_noticias(consulta: str) -> str:
    """Busca noticias recientes en la web. Devuelve título, fecha, fuente, resumen y URL de cada resultado."""
    try:
        resultados = DDGS().news(consulta, region="wt-wt", timelimit="w", max_results=6)
    except Exception as error:  # ddgs lanza excepción tanto por rate limit como por "sin resultados"
        return f"Sin resultados para '{consulta}' ({error}). Probá con otra consulta más corta."
    return "\n\n".join(
        f"- {r['title']} ({r['date'][:10]}, {r['source']})\n  {r['body'][:500]}\n  {r['url']}"
        for r in resultados
    )


@tool("contar_palabras")
def contar_palabras(texto: str) -> str:
    """Cuenta las palabras de un texto. Usala siempre para medir la longitud de un borrador."""
    return f"{contar(texto)} palabras"


class Veredicto(BaseModel):
    datos_concretos: list[str] = Field(
        description="Datos concretos (cifras, fechas, nombres propios) del borrador que figuran en las notas de investigación"
    )
    palabras: int = Field(description="Cantidad de palabras del borrador, medida con contar_palabras")
    aprobado: bool = Field(description="True solo si se cumplen todos los criterios")
    correcciones: str = Field(description="Instrucciones concretas para el redactor. Vacío si está aprobado")


def crear_llm(temperatura: float) -> LLM:
    # Groq habla el protocolo de OpenAI. Se usa el proveedor nativo en vez de "groq/..." (litellm):
    # en crewai 1.15.20 la ruta litellm le manda a Groq un campo `cache_breakpoint` que rechaza.
    return LLM(
        model=f"openai/{MODELO}",
        base_url="https://api.groq.com/openai/v1",
        api_key=os.environ["GROQ_API_KEY"],
        custom_openai=True,
        temperature=temperatura,
        max_tokens=MAX_TOKENS_SALIDA,
    )


investigador = Agent(
    role="Investigador de actualidad",
    goal="Reunir hechos verificables y recientes sobre un tema, cada uno con su fuente",
    backstory="Periodista de datos. Solo afirma lo que encuentra en las fuentes y nunca inventa cifras.",
    llm=crear_llm(0.1),
    tools=[buscar_noticias],
    max_iter=6,
    allow_delegation=False,
)

redactor = Agent(
    role="Redactor",
    goal=f"Escribir borradores claros de unas {PALABRAS_OBJETIVO} palabras basados únicamente en las notas recibidas",
    backstory="Redactor de noticias en español. Escribe corrido, sin relleno, e incluye los datos duros de las notas.",
    llm=crear_llm(0.5),
    max_iter=3,
    allow_delegation=False,
)

editor = Agent(
    role="Editor",
    goal="Verificar que cada borrador cumpla los criterios de edición y devolver correcciones concretas si no",
    backstory="Editor estricto. Mide, no estima: cuenta las palabras con la herramienta y coteja cada dato con las notas.",
    llm=crear_llm(0.0),
    tools=[contar_palabras],
    max_iter=5,
    allow_delegation=False,
)


def tarea_investigar(tema: str) -> Task:
    return Task(
        description=(
            f"Hoy es {date.today():%d/%m/%Y}. Investigá: {tema}.\n"
            "Usá buscar_noticias (máximo 3 búsquedas) y elegí UN tema concreto y actual. "
            "Es tu única herramienta: no podés abrir enlaces ni archivos, así que trabajá con los resúmenes que devuelve. "
            "Devolvé entre 5 y 8 hechos puntuales con cifras, fechas y nombres, cada uno con su fuente (URL). "
            "No agregues nada que no esté en los resultados."
        ),
        expected_output="Título del tema elegido y una lista de hechos, cada uno con su fuente.",
        agent=investigador,
    )


def tarea_redactar(contexto: list[Task]) -> Task:
    return Task(
        description=(
            f"Con las notas de la investigación, escribí un borrador de {PALABRAS_OBJETIVO} palabras. "
            f"Incluí al menos {MIN_DATOS} datos concretos tomados de las notas. "
            "Devolvé solo el texto del borrador, sin comentarios ni encabezados."
        ),
        expected_output=f"Un borrador de unas {PALABRAS_OBJETIVO} palabras.",
        agent=redactor,
        context=contexto,
    )


def tarea_reescribir(notas: str, borrador: str, correcciones: str) -> Task:
    return Task(
        description=(
            f"Tu borrador fue devuelto por el editor. Reescribilo aplicando sus correcciones.\n\n"
            f"NOTAS DE INVESTIGACIÓN:\n{notas}\n\n"
            f"BORRADOR ANTERIOR:\n{borrador}\n\n"
            f"CORRECCIONES DEL EDITOR:\n{correcciones}\n\n"
            f"Apuntá a {PALABRAS_OBJETIVO} palabras y usá solo datos de las notas. "
            "Devolvé solo el texto del nuevo borrador."
        ),
        expected_output=f"Un borrador corregido de unas {PALABRAS_OBJETIVO} palabras.",
        agent=redactor,
    )


def tarea_editar(contexto: list[Task], notas: str = "") -> Task:
    bloque_notas = f"\nNOTAS DE INVESTIGACIÓN (para cotejar los datos):\n{notas}\n" if notas else ""
    return Task(
        description=(
            "Revisá el borrador contra estos criterios:\n"
            f"1. Menciona al menos {MIN_DATOS} datos concretos (cifras, fechas, nombres) que figuren en las notas.\n"
            f"2. No supera las {MAX_PALABRAS} palabras. Medilo con contar_palabras, no lo estimes.\n"
            f"{bloque_notas}"
            "Aprobalo solo si cumple ambos. Si no, explicá qué corregir de forma concreta."
        ),
        expected_output=(
            "Solo un objeto JSON, sin texto alrededor, con las claves: datos_concretos (lista de strings), "
            "palabras (entero), aprobado (booleano) y correcciones (string, vacío si aprobado)."
        ),
        agent=editor,
        context=contexto,
    )


def leer_veredicto(texto: str) -> Veredicto | None:
    # output_pydantic hace que gpt-oss emita el resultado como una "tool call" inexistente y Groq la rechaza;
    # por eso el editor responde JSON como texto y se valida acá.
    try:
        return Veredicto.model_validate_json(texto[texto.find("{") : texto.rfind("}") + 1])
    except ValueError:
        return None


def ejecutar(agentes: list[Agent], tareas: list[Task]):
    # max_rpm es un tope prudente para la capa gratuita de Groq (no sale de un límite medido)
    return Crew(agents=agentes, tasks=tareas, process=Process.sequential, max_rpm=20, verbose=True).kickoff()


def evaluar(veredicto: Veredicto | None, borrador: str) -> tuple[bool, str]:
    """Devuelve (aprobado, correcciones). Recalcula el conteo real: un editor LLM puede errarle."""
    if veredicto is None:
        return False, "El editor no devolvió un veredicto válido; revisá los criterios y reescribí."
    palabras = contar(borrador)
    if veredicto.aprobado and palabras > MAX_PALABRAS:
        return False, f"Conteo real: {palabras} palabras (el editor lo aprobó con un conteo erróneo). El máximo es {MAX_PALABRAS}: recortalo a ~{PALABRAS_OBJETIVO}."
    return veredicto.aprobado, veredicto.correcciones


def main() -> int:
    tema = " ".join(sys.argv[1:]) or TEMA_POR_DEFECTO

    investigar = tarea_investigar(tema)
    redactar = tarea_redactar([investigar])
    editar = tarea_editar([investigar, redactar])
    salida = ejecutar([investigador, redactor, editor], [investigar, redactar, editar])
    notas, borrador = (t.raw for t in salida.tasks_output[:2])
    aprobado, correcciones = evaluar(leer_veredicto(salida.raw), borrador)

    ronda = 1
    while not aprobado and ronda < MAX_RONDAS:
        print(f"\n>>> Ronda {ronda}: borrador devuelto al redactor ({contar(borrador)} palabras). Motivo: {correcciones}\n")
        ronda += 1
        reescribir = tarea_reescribir(notas, borrador, correcciones)
        editar = tarea_editar([reescribir], notas)
        salida = ejecutar([redactor, editor], [reescribir, editar])
        borrador = salida.tasks_output[0].raw
        aprobado, correcciones = evaluar(leer_veredicto(salida.raw), borrador)

    estado = "APROBADO" if aprobado else f"SIN APROBAR tras {MAX_RONDAS} rondas"
    print(f"\n=== Borrador final ({estado}, {contar(borrador)} palabras, {ronda} ronda/s) ===\n\n{borrador}\n")
    if not aprobado:
        print(f"Última observación del editor: {correcciones}")
    Path("borrador_final.md").write_text(borrador + "\n", encoding="utf-8")
    return 0 if aprobado else 1


if __name__ == "__main__":
    sys.exit(main())
