from crewai.tools import tool
from ddgs import DDGS


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
