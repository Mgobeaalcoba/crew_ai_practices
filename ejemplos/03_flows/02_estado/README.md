# 02 · Estado de un Flow

> Datos compartidos por todos los pasos: un contador con un dict y un carrito de compras con un modelo Pydantic.

## Qué vas a aprender

- Estado **no estructurado** (`Flow`, un dict) y **estructurado** (`Flow[Modelo]`).
- Cómo los `inputs` de `kickoff` se cargan en el estado.
- El `id` automático del estado.

## Las dos formas

| | No estructurado | Estructurado |
|---|---|---|
| Declaración | `class F(Flow)` | `class F(Flow[EstadoCarrito])` |
| Acceso | `self.state["visitas"]` | `self.state.total` |
| Tipos y defaults | No | Sí (Pydantic) |
| Autocompletado y validación | No | Sí |
| Recomendado para | Pruebas rápidas | Todo lo demás |

## El código clave

```python
class EstadoCarrito(BaseModel):
    cliente: str = "anónimo"
    items: list[str] = []
    total: float = 0.0
    descuento_aplicado: bool = False

class FlowCarrito(Flow[EstadoCarrito]):
    @start()
    def agregar(self):
        self.state.items += ["yerba", "azúcar", "galletitas"]
        self.state.total = 12_300
    ...

flow.kickoff(inputs={"cliente": "Marta"})   # pisa el default de `cliente` antes del primer paso
```

## Correrlo

```bash
uv run main.py flows/02_estado
```

## Qué vas a ver

```
No estructurado → visitas = 3
Estructurado    → Marta: 3 ítems, total $11,070
Estado final    → {'cliente': 'Marta', 'items': ['yerba', 'azúcar', 'galletitas'], 'total': 11070.0,
                   'descuento_aplicado': True, 'id': '72e9141a-...'}
```

El `id` lo agrega CrewAI a todo estado y es la clave para [persistirlo](../05_persistencia).

## Para experimentar

1. Pasá `inputs={"total": "mucho"}` al carrito: ¿qué hace la validación de Pydantic?
2. Agregá un campo calculado (`@property`) con la cantidad de ítems.

## Tests

`tests/test_flows.py::TestEstado`.
