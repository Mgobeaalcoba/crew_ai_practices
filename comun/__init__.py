"""Piezas compartidas por todos los ejemplos del repo.

- `crear_llm`: un LLM de CrewAI apuntando al proveedor que elijas (Groq, LM Studio, Ollama, OpenAI, Anthropic, Gemini).
- `config_embedder`: configuración de embeddings para knowledge y memoria (LM Studio u Ollama locales, u OpenAI).
- `LLMGuionado`: un LLM falso que responde textos fijos, para tests sin red ni tokens.
- `buscar_noticias`, `contar_palabras`: herramientas reutilizables.

Importar este paquete carga `.env` y apaga la pregunta de trazas de CrewAI.
"""

from comun.entorno import cargar_entorno

cargar_entorno()

from comun.embeddings import config_embedder  # noqa: E402
from comun.herramientas import buscar_noticias, contar, contar_palabras  # noqa: E402
from comun.llm import PROVEEDORES, crear_llm, describir_llm  # noqa: E402
from comun.llm_falso import LLMGuionado  # noqa: E402

__all__ = [
    "PROVEEDORES",
    "LLMGuionado",
    "buscar_noticias",
    "config_embedder",
    "contar",
    "contar_palabras",
    "crear_llm",
    "describir_llm",
]
