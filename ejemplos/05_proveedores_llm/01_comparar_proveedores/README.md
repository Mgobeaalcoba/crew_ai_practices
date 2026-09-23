# 01 · Comparar proveedores

> Le hace la misma pregunta al mismo agente usando cada proveedor configurado (nube y local) y muestra la respuesta y el tiempo de cada uno.

## Qué vas a aprender

- Que cambiar de proveedor es cambiar un parámetro: `crear_llm(proveedor=..., modelo=...)`.
- Detectar qué proveedores están disponibles (key en `.env` o servidor local encendido).
- Comparar calidad y latencia.

## Cómo funciona

Para cada proveedor de `comun.PROVEEDORES`:

1. **En la nube** (Groq, OpenAI, Anthropic, Gemini): ¿está la key en `.env`?
2. **Local** (LM Studio, Ollama): ¿responde `GET /v1/models` y ofrece un modelo de **chat** (no de embeddings)?
3. Si está disponible, crea el agente con ese LLM, pregunta y mide el tiempo. Si un proveedor falla, lo informa y sigue con el resto.

## El código clave

```python
agente = Agent(role="Divulgador", goal="...", backstory="...",
               llm=crear_llm(0.2, proveedor=nombre, modelo=modelo))
```

## Correrlo

```bash
uv run main.py comparar_proveedores              # todos
uv run main.py comparar_proveedores groq ollama  # solo esos
```

## Qué vas a ver

Con solo Groq configurado (23/09/2026):

```
Pregunta: En una sola oración: ¿qué es un agente de IA?

· groq       qwen/qwen3.8-27b (1.4 s)
  Un agente de IA es un programa que percibe su entorno y toma decisiones autónomas para lograr objetivos específicos.

· lmstudio   omitido: sin servidor o sin modelo de chat en http://localhost:1234/v1
· ollama     omitido: sin servidor o sin modelo de chat en http://localhost:11434/v1
· openai     omitido: falta OPENAI_API_KEY en .env
· anthropic  omitido: falta ANTHROPIC_API_KEY en .env
· gemini     omitido: falta GEMINI_API_KEY en .env
```

Para sumar un modelo local: `lms get qwen/qwen3-4b`, `lms load qwen/qwen3-4b` y `lms server start` ([docs/proveedores-llm.md](../../../docs/proveedores-llm.md#lm-studio-local)).

## Para experimentar

1. Cambiá la pregunta por una que requiera razonar ("si tengo 3 manzanas y me como la mitad de 4...").
2. Corré el [ejemplo de herramientas](../../01_agentes/02_herramientas) con un modelo local chico (`LLM_PROVEEDOR=lmstudio`) y compará: ¿usa bien las herramientas?

## Tests

`tests/test_integrador.py::TestComparadorDeProveedores`: la detección de disponibilidad y la elección de un modelo de chat entre varios.
