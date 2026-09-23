# tests/

Tests de todos los ejemplos y de `comun/`. Usan `unittest` (viene con Python; `pytest` también los corre si lo instalás).

```bash
uv run python -m unittest -b                                # todo lo offline (~20 s)
uv run python -m unittest -b -v tests.test_flows            # un archivo, con detalle
CREW_VIVO=1 uv run python -m unittest -b tests.test_vivo    # con el LLM real (gasta tokens)
```

`-b` oculta los paneles que imprime CrewAI, salvo en los tests que fallan.

## Archivos

| Archivo | Cubre | Necesita |
|---|---|---|
| [`test_comun.py`](test_comun.py) | Fábrica de LLMs, embeddings, LLM falso, herramientas, lanzador | — |
| [`test_agentes.py`](test_agentes.py) | `ejemplos/01_agentes` | Algunos: LM Studio (embeddings) o Docker |
| [`test_crews.py`](test_crews.py) | `ejemplos/02_crews` | — |
| [`test_flows.py`](test_flows.py) | `ejemplos/03_flows` | — |
| [`test_observabilidad.py`](test_observabilidad.py) | `ejemplos/04_observabilidad` | — |
| [`test_integrador.py`](test_integrador.py) | `ejemplos/05_proveedores_llm` y `ejemplos/06_integrador` | — |
| [`test_vivo.py`](test_vivo.py) | Siete ejemplos con el LLM real | `CREW_VIVO=1` y una key |
| [`utilidades.py`](utilidades.py) | `ejemplo()`, `json_final()`, `responder_segun()` y los decoradores `requiere_*` | — |

## Tests omitidos

Un test que necesita un servicio no disponible se **omite** (no falla) e informa el motivo:

| Decorador | Se omite si | Cómo habilitarlo |
|---|---|---|
| `@requiere_embeddings` | LM Studio no responde en `:1234` | `lms server start` |
| `@requiere_docker` | Docker apagado o sin la imagen de `SANDBOX_IMAGEN` | Encender Docker; `docker pull python:3.12-slim` |
| `@requiere_vivo` | `CREW_VIVO` distinto de `1` | `CREW_VIVO=1` |

## Resultado de referencia (23/09/2026)

```
Ran 78 tests in 18.517s
OK (skipped=7)      ← los 7 de test_vivo; con LM Studio y Docker encendidos
```

Cómo funcionan el LLM falso y qué conviene verificar: [docs/tests.md](../docs/tests.md).
