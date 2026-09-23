"""Lanzador de ejemplos.

Uso:
    uv run main.py                        # lista todos los ejemplos
    uv run main.py agente_solo            # corre el ejemplo cuyo camino contiene "agente_solo"
    uv run main.py redactor_editor "tema" # los argumentos extra se le pasan al ejemplo

Equivale a `uv run -m ejemplos.<grupo>.<ejemplo>.main`, pero sin escribir el camino completo.
"""

import runpy
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
EJEMPLOS = RAIZ / "ejemplos"


def listar() -> list[Path]:
    return sorted(p.parent for p in EJEMPLOS.glob("*/*/main.py"))


def buscar(consulta: str) -> list[Path]:
    consulta = consulta.strip("/").lower()
    return [d for d in listar() if consulta in d.relative_to(EJEMPLOS).as_posix().lower()]


def imprimir_catalogo() -> None:
    grupo_actual = None
    for directorio in listar():
        grupo, ejemplo = directorio.relative_to(EJEMPLOS).parts
        if grupo != grupo_actual:
            print(f"\n{grupo}")
            grupo_actual = grupo
        print(f"  {ejemplo}")
    print("\nCorré uno con: uv run main.py <parte del nombre> [argumentos]")


def main() -> int:
    if len(sys.argv) < 2:
        imprimir_catalogo()
        return 0
    candidatos = buscar(sys.argv[1])
    if len(candidatos) != 1:
        opciones = "\n".join(f"  {d.relative_to(EJEMPLOS)}" for d in candidatos) or "  (ninguno)"
        print(f"'{sys.argv[1]}' coincide con {len(candidatos)} ejemplos:\n{opciones}")
        return 2
    modulo = ".".join(candidatos[0].relative_to(RAIZ).parts) + ".main"
    sys.argv = [str(candidatos[0] / "main.py"), *sys.argv[2:]]
    try:
        runpy.run_module(modulo, run_name="__main__", alter_sys=True)
    except SystemExit as salida:
        return salida.code if isinstance(salida.code, int) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
