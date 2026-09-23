# 11 · Agente multimodal (solo documentación)

> Un agente que además de texto recibe imágenes o PDFs. No hay `main.py`: el entorno de este repo no tiene un modelo con visión disponible, y el parámetro clásico está deprecado.

## Por qué no hay código

1. **Groq no ofrece modelos de visión** en la cuenta usada (lista de modelos del 23/09/2026: `gpt-oss-20b/120b`, `qwen3.8-27b`, `whisper`, `orpheus`, `allam`, `prompt-guard`).
2. **`Agent(multimodal=True)` está deprecado** en 1.15 y se elimina en 2.0. Además, el soporte nativo de archivos (`input_files`) necesita el extra `crewai[file-processing]`, que no se pudo instalar sin PyPI.

Escribir un ejemplo sin poder correrlo iría contra la regla del repo de solo publicar código verificado, así que queda documentado.

## Cómo se hace en 1.15

La forma nueva es pasar archivos directamente, en la tarea o en `kickoff`:

```python
# uv add "crewai[file-processing]" y un LLM con visión (por ejemplo, LLM_PROVEEDOR=openai o anthropic)
from crewai import Agent, Task

tarea = Task(
    description="Describí qué hay en la foto y si el producto se ve dañado.",
    expected_output="Descripción y veredicto (dañado / sano).",
    agent=inspector,
    input_files={"foto": "fotos/caja.jpg"},
)

# o sin Crew:
inspector.kickoff("¿El producto está dañado?", input_files={"foto": "fotos/caja.jpg"})
```

Los mensajes de `kickoff` también aceptan un campo `files` por mensaje. El LLM tiene que soportar imágenes: si no, el proveedor rechaza el pedido.

## Cómo probarlo

1. `uv add "crewai[file-processing]"`.
2. Configurá un proveedor con visión en `.env` (ver [docs/proveedores-llm.md](../../../docs/proveedores-llm.md)). Con LM Studio, un modelo "VL" (por ejemplo, Qwen2.5-VL).
3. Adaptá el fragmento de arriba.

## Ver también

- [docs/clasificacion.md](../../../docs/clasificacion.md#3-por-capacidades-del-agente)
- [trampas §14](../../../docs/trampas-conocidas.md#14-parámetros-deprecados-que-todavía-aparecen-en-tutoriales): parámetros deprecados.
