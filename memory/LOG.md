# Registro de sesiones

> Entradas nuevas arriba. Formato: YYYY-MM-DD · agente · título. Historial append-only: no se editan entradas viejas.

## 2026-10-17 · OpenCode · Hook pre-commit activo

- Mariano aprobó la opción 1 (17/10/2026): resolver los hallazgos con lista blanca e instalar el hook.
- Hallazgos revisados: datos de ejemplo con formato DNI/teléfono; sin credenciales reales. Permitidos documentados en `scripts/secret_scan_allowlist.txt`.
- Escáner actualizado a v3.2 (saltea binarios y dumps `.b64`; soporta lista blanca).

## 2026-10-17 · OpenCode · agentificación inicial

- Repo revisado contra el estándar de agentificación; se agregaron solo las piezas faltantes.
- Cambios: AGENTS.md (si faltaba), puentes multi-agente, memory/STATE.md + memory/LOG.md, scripts/scan_secrets.py (hook no instalado: hallazgos preexistentes).
- Pendiente: nada registrado.
