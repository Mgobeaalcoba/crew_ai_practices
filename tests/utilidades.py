"""Ayudas compartidas por los tests."""

import importlib
import json
import os
import shutil
import subprocess
import unittest
import urllib.request

import comun  # noqa: F401  (carga .env y los ajustes de entorno antes que crewai)
from comun.llm_falso import LLMGuionado, respuesta_final, usar_herramienta

__all__ = ["LLMGuionado", "ejemplo", "respuesta_final", "usar_herramienta", "json_final", "requiere_vivo",
           "requiere_embeddings", "requiere_docker", "responder_segun"]


def ejemplo(camino: str):
    """Importa el main.py de un ejemplo: ejemplo("02_crews/01_secuencial")."""
    return importlib.import_module("ejemplos." + camino.strip("/").replace("/", ".") + ".main")


def json_final(datos: dict) -> str:
    """Respuesta final guionada con un JSON (para response_format, output_pydantic o LLMGuardrail)."""
    return respuesta_final(json.dumps(datos, ensure_ascii=False))


def responder_segun(reglas: list[tuple[str, str]], por_defecto: str) -> callable:
    """Crea un responder para LLMGuionado: devuelve la respuesta de la primera regla cuyo texto aparece en el
    último mensaje de usuario. Sirve cuando varios agentes comparten el mismo LLM falso."""

    def responder(mensajes: list[dict]) -> str:
        texto = "\n".join(str(m.get("content", "")) for m in mensajes)
        for clave, respuesta in reglas:
            if clave in texto:
                return respuesta
        return por_defecto

    return responder


def _servidor_responde(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=2):
            return True
    except OSError:
        return False


def _docker_listo() -> bool:
    if shutil.which("docker") is None:
        return False
    imagen = os.getenv("SANDBOX_IMAGEN", "python:3.12-slim")
    return subprocess.run(["docker", "image", "inspect", imagen], capture_output=True).returncode == 0


requiere_vivo = unittest.skipUnless(
    os.getenv("CREW_VIVO") == "1", "test con LLM real: correlo con CREW_VIVO=1 (gasta tokens)"
)
requiere_embeddings = unittest.skipUnless(
    _servidor_responde(comun.config_embedder()["config"]["api_base"].rstrip("/") + "/models"),
    "no hay servidor de embeddings (lms server start)",
)
requiere_docker = unittest.skipUnless(_docker_listo(), "Docker apagado o sin la imagen de SANDBOX_IMAGEN")
