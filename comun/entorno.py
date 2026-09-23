import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent


def cargar_entorno() -> None:
    load_dotenv(RAIZ / ".env")
    # Knowledge, memoria, persistencia de flows y checkpoints se guardan en "<datos de usuario>/<este valor>".
    # Un camino absoluto gana en ese join, así que todo queda en db/ dentro del repo (ignorado por git)
    # en vez de en ~/Library/Application Support/.
    os.environ.setdefault("CREWAI_STORAGE_DIR", str(RAIZ / "db"))
    os.environ.setdefault("CREWAI_TRACING_ENABLED", "false")  # evita la pregunta de trazas al terminar
    # CrewAI manda telemetría anónima por defecto; en un repo de práctica no aporta y suma latencia
    os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
    os.environ.setdefault("OTEL_SDK_DISABLED", "true")
    # Al iniciar un Flow, CrewAI consulta PyPI por versiones nuevas. Su timeout no cubre la resolución DNS:
    # en una red sin acceso a pypi.org el Flow queda colgado indefinidamente antes del primer paso.
    os.environ.setdefault("CREWAI_DISABLE_VERSION_CHECK", "true")
