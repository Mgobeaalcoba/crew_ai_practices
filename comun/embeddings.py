"""Configuración de embeddings para knowledge (RAG) y memoria.

Un embedding convierte texto en un vector de números; textos parecidos quedan cerca. CrewAI los usa para
buscar los fragmentos de knowledge más relevantes y para recordar memorias. Groq no ofrece embeddings, así
que por defecto se usa un modelo local servido por LM Studio.

    EMBEDDINGS_PROVEEDOR=lmstudio   # lmstudio | ollama | openai
    EMBEDDINGS_MODELO=...           # opcional
"""

import os

_POR_DEFECTO = {
    "lmstudio": ("http://localhost:1234/v1", "text-embedding-nomic-embed-text-v1.5"),
    "ollama": ("http://localhost:11434/v1", "nomic-embed-text"),
    "openai": ("https://api.openai.com/v1", "text-embedding-3-small"),
}


def config_embedder(proveedor: str | None = None, modelo: str | None = None) -> dict:
    """Devuelve el dict que aceptan `Crew(embedder=...)`, `Agent(embedder=...)` y `Memory(embedder=...)`."""
    nombre = (proveedor or os.getenv("EMBEDDINGS_PROVEEDOR") or "lmstudio").lower()
    if nombre not in _POR_DEFECTO:
        raise ValueError(f"Proveedor de embeddings desconocido: {nombre!r}. Opciones: {', '.join(_POR_DEFECTO)}")
    base_url, modelo_por_defecto = _POR_DEFECTO[nombre]
    api_key = os.getenv("OPENAI_API_KEY", "") if nombre == "openai" else nombre
    # LM Studio y Ollama exponen /v1/embeddings igual que OpenAI, así que los tres usan el proveedor "openai"
    return {
        "provider": "openai",
        "config": {
            "api_key": api_key,
            "api_base": base_url,
            "model_name": modelo or os.getenv("EMBEDDINGS_MODELO") or modelo_por_defecto,
        },
    }
