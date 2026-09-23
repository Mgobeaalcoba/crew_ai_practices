"""Fábrica de LLMs: un mismo código de agentes, cualquier proveedor.

Todos los proveedores de acá hablan el protocolo de OpenAI (`/v1/chat/completions`), así que se conectan
con el proveedor nativo `openai/` de CrewAI cambiando solo `base_url`, la key y el modelo. No hace falta
instalar SDKs extra (ver docs/proveedores-llm.md para la alternativa con proveedores nativos).

Se elige con variables de entorno (en `.env`):

    LLM_PROVEEDOR=groq            # groq | lmstudio | ollama | openai | anthropic | gemini
    LLM_MODELO=qwen/qwen3.8-27b   # opcional si el proveedor tiene modelo por defecto
    LLM_MAX_TOKENS=900            # opcional; tope de tokens de salida por respuesta
"""

import os
from dataclasses import dataclass

from crewai import LLM


@dataclass(frozen=True)
class Proveedor:
    base_url: str
    variable_key: str | None  # None: servidor local, no pide key
    modelo_por_defecto: str | None  # None: obligatorio definir LLM_MODELO
    max_tokens_por_defecto: int | None = None
    notas: str = ""


PROVEEDORES: dict[str, Proveedor] = {
    "groq": Proveedor(
        base_url="https://api.groq.com/openai/v1",
        variable_key="GROQ_API_KEY",
        # gpt-oss-120b/20b fallan con los agentes en Groq (llaman tools inexistentes: `json`, `open_file`)
        modelo_por_defecto="qwen/qwen3.8-27b",
        # Groq rechaza (429) pedidos cuyo máximo de salida supera el límite de tokens de salida por minuto
        # del modelo (1000 en la cuenta de prueba). Sin tope explícito asume ~1400 y falla desde la primera llamada.
        max_tokens_por_defecto=900,
        notas="Capa gratuita. Key en https://console.groq.com/keys",
    ),
    "lmstudio": Proveedor(
        base_url="http://localhost:1234/v1",
        variable_key=None,
        modelo_por_defecto=None,
        notas="Local. Cargá un modelo de chat y encendé el servidor: `lms server start`",
    ),
    "ollama": Proveedor(
        base_url="http://localhost:11434/v1",
        variable_key=None,
        modelo_por_defecto="qwen3:8b",
        notas="Local. `ollama pull qwen3:8b` y `ollama serve`",
    ),
    "openai": Proveedor(
        base_url="https://api.openai.com/v1",
        variable_key="OPENAI_API_KEY",
        modelo_por_defecto=None,
        notas="Pago. Definí LLM_MODELO con un modelo de tu cuenta",
    ),
    "anthropic": Proveedor(
        base_url="https://api.anthropic.com/v1/",
        variable_key="ANTHROPIC_API_KEY",
        modelo_por_defecto="claude-haiku-4-5",
        notas="Pago. Usa la capa de compatibilidad con OpenAI de la API de Claude",
    ),
    "gemini": Proveedor(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        variable_key="GEMINI_API_KEY",
        modelo_por_defecto=None,
        notas="Tiene capa gratuita. Definí LLM_MODELO (por ejemplo, un gemini-*-flash de tu cuenta)",
    ),
}

# Nombres de la primera versión del repo; se siguen aceptando
_ALIAS_GROQ = {"LLM_MODELO": "GROQ_MODEL", "LLM_MAX_TOKENS": "GROQ_MAX_TOKENS"}


def _variable(nombre: str, proveedor: str) -> str | None:
    valor = os.getenv(nombre)
    if valor is None and proveedor == "groq":
        valor = os.getenv(_ALIAS_GROQ[nombre])
    return valor or None


def resolver(proveedor: str | None = None, modelo: str | None = None) -> tuple[str, Proveedor, str, int | None]:
    """Devuelve (nombre del proveedor, su configuración, modelo, max_tokens) sin crear el LLM."""
    nombre = (proveedor or os.getenv("LLM_PROVEEDOR") or "groq").lower()
    if nombre not in PROVEEDORES:
        raise ValueError(f"Proveedor desconocido: {nombre!r}. Opciones: {', '.join(PROVEEDORES)}")
    config = PROVEEDORES[nombre]
    modelo = modelo or _variable("LLM_MODELO", nombre) or config.modelo_por_defecto
    if not modelo:
        raise ValueError(f"El proveedor {nombre!r} no tiene modelo por defecto: definí LLM_MODELO en .env")
    max_tokens = _variable("LLM_MAX_TOKENS", nombre)
    return nombre, config, modelo, int(max_tokens) if max_tokens else config.max_tokens_por_defecto


def crear_llm(
    temperatura: float = 0.2,
    *,
    proveedor: str | None = None,
    modelo: str | None = None,
    **extra,
) -> LLM:
    """Crea el LLM del proveedor elegido. `extra` se pasa tal cual a `crewai.LLM` (por ejemplo, `stop`)."""
    nombre, config, modelo, max_tokens = resolver(proveedor, modelo)
    if config.variable_key:
        api_key = os.getenv(config.variable_key)
        if not api_key:
            raise ValueError(f"Falta {config.variable_key} en .env para usar el proveedor {nombre!r}")
    else:
        api_key = nombre  # los servidores locales ignoran la key, pero el cliente de OpenAI exige una

    # Se usa el proveedor nativo "openai/" en vez de, por ejemplo, "groq/..." (que pasa por litellm):
    # en crewai 1.15.20 la ruta litellm le manda a Groq un campo `cache_breakpoint` que rechaza con 400.
    # CrewAI corta el prefijo en la primera barra, así que "openai/qwen/qwen3.8-27b" llega como "qwen/qwen3.8-27b".
    return LLM(
        model=f"openai/{modelo}",
        base_url=config.base_url,
        api_key=api_key,
        custom_openai=True,
        temperature=temperatura,
        max_tokens=max_tokens,
        **extra,
    )


def describir_llm(proveedor: str | None = None, modelo: str | None = None) -> str:
    nombre, config, modelo, max_tokens = resolver(proveedor, modelo)
    tope = f", max_tokens={max_tokens}" if max_tokens else ""
    return f"{nombre} · {modelo} ({config.base_url}{tope})"
