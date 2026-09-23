# 03 · Flows

Un Flow es un programa de Python orientado a eventos: métodos que se disparan entre sí, con un estado compartido. Es la pieza de CrewAI para el **control**: ramas, bucles, paralelismo, persistencia y aprobaciones. Los agentes y Crews se llaman desde los pasos que necesitan "pensar".

| # | Ejemplo | Qué muestra | LLM |
|---|---|---|---|
| 01 | [basico](01_basico) | `@start` y `@listen`: pasos encadenados | No |
| 02 | [estado](02_estado) | `self.state` como dict o como modelo Pydantic | No |
| 03 | [router](03_router) | `@router`: bifurcar según una condición | No |
| 04 | [paralelo_and_or](04_paralelo_and_or) | Pasos en paralelo; esperar a todos (`and_`) o al primero (`or_`) | No |
| 05 | [persistencia](05_persistencia) | `@persist`: retomar el estado en otra ejecución | No |
| 06 | [human_feedback](06_human_feedback) | `@human_feedback`: una persona opina y su respuesta elige la rama | Sí (clasifica) |
| 07 | [flow_con_agentes](07_flow_con_agentes) | Pasos que llaman a agentes; el ruteo lo decide el código | Sí |
| 08 | [flow_con_crews](08_flow_con_crews) | Pasos que llaman a Crews, con un bucle de corrección | Sí |

Los cinco primeros no usan ningún LLM: se corren y se testean gratis. Sirven para entender la mecánica antes de sumar agentes.

## Anatomía de un Flow

```python
from crewai.flow.flow import Flow, and_, listen, or_, router, start
from pydantic import BaseModel

class Estado(BaseModel):
    pedido: str = ""
    aprobado: bool = False

class MiFlow(Flow[Estado]):
    @start()
    def recibir(self):                   # arranca acá
        ...

    @router(recibir)
    def decidir(self) -> str:            # devuelve una etiqueta
        return "ok" if self.state.aprobado else "revisar"

    @listen("ok")
    def terminar(self):                  # corre si el router emitió "ok"
        return "listo"

flow = MiFlow()
resultado = flow.kickoff(inputs={"pedido": "..."})   # los inputs se cargan en el estado
flow.state                                            # el estado final
flow.plot("mi_flow.html")                             # un diagrama interactivo del Flow
```

## Tres trampas de los Flows

1. **No apiles `@listen`**: el de abajo se pierde en silencio. Usá `@listen(or_(a, "etiqueta"))`. [§5](../../docs/trampas-conocidas.md#5-apilar-listen-pierde-disparadores)
2. **En un bucle, un `or_()` de métodos se dispara una sola vez.** El paso que vuelve atrás tiene que ser un `@router` que emita una etiqueta nueva. [§6](../../docs/trampas-conocidas.md#6-un-or_-de-métodos-no-se-vuelve-a-disparar-en-un-bucle)
3. **Sin acceso a pypi.org, `kickoff()` se cuelga**, por un chequeo de versión. `import comun` lo desactiva. [§9](../../docs/trampas-conocidas.md#9-un-flow-se-cuelga-sin-acceso-a-pypi)

## ¿Flow o Crew?

Ver la tabla en [docs/conceptos.md](../../docs/conceptos.md#crew-vs-flow-cuál-usar). En resumen: el Flow como esqueleto de la aplicación y los Crews en las etapas que necesitan autonomía.
