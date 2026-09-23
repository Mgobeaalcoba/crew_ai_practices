# 08 · Salida estructurada

> Que el agente devuelva **datos** (un objeto Pydantic con tipos) en vez de texto libre: extraer los campos de un aviso clasificado.

## Qué vas a aprender

- `Task(output_pydantic=...)` y `Task(output_json=...)`.
- Pedir JSON en el prompt y validarlo vos, la opción más robusta con modelos problemáticos.
- Por qué las `Field(description=...)` importan.

## Tres caminos

| Camino | Resultado | Cuándo |
|---|---|---|
| `Task(output_pydantic=Aviso)` | `salida.pydantic` es un `Aviso` | Por defecto, dentro de un Crew |
| `Task(output_json=Aviso)` | `salida.json_dict` es un `dict` | Si vas a serializar el resultado |
| `agente.kickoff(..., response_format=Aviso)` | `salida.pydantic` | Sin Crew ([01_agente_solo](../01_agente_solo)) |
| JSON en `expected_output` + `Aviso.model_validate_json` | Vos controlás el parseo | Modelos que fallan con los anteriores |

## El código clave

```python
class Aviso(BaseModel):
    producto: str
    precio: int | None = Field(description="Precio en pesos, sin puntos ni símbolo. null si no figura")
    estado: str = Field(description="nuevo, usado o no especificado")
    ubicacion: str | None = None
    etiquetas: list[str] = Field(description="Entre 2 y 4 etiquetas en minúscula")

Task(description=f"Extraé los datos de este aviso:\n{aviso}", expected_output="...", agent=a, output_pydantic=Aviso)
```

Camino manual:

```python
texto = crew.kickoff().raw
Aviso.model_validate_json(texto[texto.find("{") : texto.rfind("}") + 1])  # tolera texto o ```json alrededor
```

## Correrlo

```bash
uv run main.py salida_estructurada "Vendo bici rodado 29 poco uso, cambios Shimano. $350.000 charlables. Palermo."
```

## Qué vas a ver

La misma entrada por los dos caminos (23/09/2026):

| Campo | `output_pydantic` | JSON en texto |
|---|---|---|
| producto | bici rodado 29 | bici rodado 29 |
| precio | 350000 | 350000 |
| estado | **usado** | **poco uso** |
| ubicacion | Palermo | Palermo |
| etiquetas | **bici, rodado 29, shimano** | **Shimano** |

Con `output_pydantic`, el modelo recibe el esquema **con las descripciones**, así que respeta "nuevo, usado o no especificado" y "entre 2 y 4 etiquetas en minúscula". El camino manual solo le dio los nombres de las claves ([trampas §13](../../../docs/trampas-conocidas.md#13-sin-descripciones-la-salida-estructurada-es-más-pobre)).

## ¿Por qué existe el camino manual?

Con los modelos `openai/gpt-oss-*` de Groq, `output_pydantic` hace que el modelo emita la respuesta como una llamada a una herramienta `json` inexistente, y Groq responde 400. El integrador usa el camino manual por eso ([decisiones-tecnicas.md §4](../../../docs/decisiones-tecnicas.md#4-el-veredicto-del-editor-es-json-como-texto-no-output_pydantic)).

## Para experimentar

1. Agregá `moneda: Literal["ARS", "USD"]` y probá con "Vendo guitarra, 200 dólares".
2. Pasá un aviso sin precio y verificá que quede `None`.
3. Cambiá a `output_json` y mirá `salida.json_dict`.

## Tests

`tests/test_agentes.py::TestSalidaEstructurada`: `output_pydantic`, JSON rodeado de texto y JSON inválido (devuelve `None`).

## Ver también

- [02_crews/04_tareas_condicionales](../../02_crews/04_tareas_condicionales): una salida estructurada que decide si se ejecuta la tarea siguiente.
