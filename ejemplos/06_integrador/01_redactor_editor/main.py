"""Integrador: crew de tres agentes (investigador -> redactor -> editor) con bucle de revisión en Python.

Es el ejemplo original del repo. Junta varias piezas de los ejemplos anteriores: herramientas reales
(búsqueda web), un Crew secuencial, JSON validado con Pydantic y un bucle de corrección con tope de rondas.

Uso:
    uv run main.py redactor_editor "tema a investigar"
    uv run main.py redactor_editor     # el investigador elige un tema tecnológico de hoy
"""

import sys
from datetime import date
from pathlib import Path

from crewai import Agent, Crew, Process, Task
from pydantic import BaseModel, Field

from comun import buscar_noticias, contar, contar_palabras, crear_llm, describir_llm

# Criterios de la edición: el editor y la guarda del código leen las mismas constantes.
PALABRAS_OBJETIVO = 200
MAX_PALABRAS = 250
MIN_DATOS = 2
MAX_RONDAS = 3

TEMA_POR_DEFECTO = "el tema de tecnología más relevante de hoy"


class Veredicto(BaseModel):
    datos_concretos: list[str] = Field(
        description="Datos concretos (cifras, fechas, nombres propios) del borrador que figuran en las notas de investigación"
    )
    palabras: int = Field(description="Cantidad de palabras del borrador, medida con contar_palabras")
    aprobado: bool = Field(description="True solo si se cumplen todos los criterios")
    correcciones: str = Field(description="Instrucciones concretas para el redactor. Vacío si está aprobado")


def construir_agentes(llm=None) -> tuple[Agent, Agent, Agent]:
    """Crea investigador, redactor y editor. `llm` reemplaza a los tres LLM (útil en tests)."""
    investigador = Agent(
        role="Investigador de actualidad",
        goal="Reunir hechos verificables y recientes sobre un tema, cada uno con su fuente",
        backstory="Periodista de datos. Solo afirma lo que encuentra en las fuentes y nunca inventa cifras.",
        llm=llm or crear_llm(0.1),
        tools=[buscar_noticias],
        max_iter=6,
        allow_delegation=False,
    )

    redactor = Agent(
        role="Redactor",
        goal=f"Escribir borradores claros de unas {PALABRAS_OBJETIVO} palabras basados únicamente en las notas recibidas",
        backstory="Redactor de noticias en español. Escribe corrido, sin relleno, e incluye los datos duros de las notas.",
        llm=llm or crear_llm(0.5),
        max_iter=3,
        allow_delegation=False,
    )

    editor = Agent(
        role="Editor",
        goal="Verificar que cada borrador cumpla los criterios de edición y devolver correcciones concretas si no",
        backstory="Editor estricto. Mide, no estima: cuenta las palabras con la herramienta y coteja cada dato con las notas.",
        llm=llm or crear_llm(0.0),
        tools=[contar_palabras],
        max_iter=5,
        allow_delegation=False,
    )
    return investigador, redactor, editor


def tarea_investigar(tema: str, investigador: Agent) -> Task:
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


def tarea_redactar(contexto: list[Task], redactor: Agent) -> Task:
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


def tarea_reescribir(notas: str, borrador: str, correcciones: str, redactor: Agent) -> Task:
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


def tarea_editar(contexto: list[Task], editor: Agent, notas: str = "") -> Task:
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


def revisar(tema: str, llm=None) -> tuple[bool, str, int]:
    """Corre el crew y el bucle de revisión. Devuelve (aprobado, borrador, rondas)."""
    investigador, redactor, editor = construir_agentes(llm)
    investigar = tarea_investigar(tema, investigador)
    redactar = tarea_redactar([investigar], redactor)
    editar = tarea_editar([investigar, redactar], editor)
    salida = ejecutar([investigador, redactor, editor], [investigar, redactar, editar])
    notas, borrador = (t.raw for t in salida.tasks_output[:2])
    aprobado, correcciones = evaluar(leer_veredicto(salida.raw), borrador)

    ronda = 1
    while not aprobado and ronda < MAX_RONDAS:
        print(f"\n>>> Ronda {ronda}: borrador devuelto al redactor ({contar(borrador)} palabras). Motivo: {correcciones}\n")
        ronda += 1
        reescribir = tarea_reescribir(notas, borrador, correcciones, redactor)
        editar = tarea_editar([reescribir], editor, notas)
        salida = ejecutar([redactor, editor], [reescribir, editar])
        borrador = salida.tasks_output[0].raw
        aprobado, correcciones = evaluar(leer_veredicto(salida.raw), borrador)

    if not aprobado:
        print(f"Última observación del editor: {correcciones}")
    return aprobado, borrador, ronda


def main() -> int:
    tema = " ".join(sys.argv[1:]) or TEMA_POR_DEFECTO
    print(f"LLM: {describir_llm()}\n")
    aprobado, borrador, rondas = revisar(tema)
    estado = "APROBADO" if aprobado else f"SIN APROBAR tras {MAX_RONDAS} rondas"
    print(f"\n=== Borrador final ({estado}, {contar(borrador)} palabras, {rondas} ronda/s) ===\n\n{borrador}\n")
    Path("borrador_final.md").write_text(borrador + "\n", encoding="utf-8")
    return 0 if aprobado else 1


if __name__ == "__main__":
    sys.exit(main())
