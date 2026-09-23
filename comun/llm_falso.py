"""Un LLM falso para probar agentes, crews y flows sin red y sin gastar tokens.

CrewAI acepta cualquier subclase de `BaseLLM`. `LLMGuionado` devuelve, en orden, las respuestas que le
pasás, y guarda los mensajes que recibió en cada llamada para que el test pueda inspeccionar el prompt.

Como no declara soporte de *function calling*, los agentes le hablan en formato ReAct (texto). Para que
use una herramienta, la respuesta guionada tiene que tener esta forma:

    Thought: necesito contar las palabras
    Action: contar_palabras
    Action Input: {"texto": "hola mundo"}

y para terminar:

    Thought: ya tengo la respuesta
    Final Answer: <respuesta>
"""

from collections.abc import Callable
from typing import Any

from crewai.llms.base_llm import BaseLLM
from pydantic import Field


def respuesta_final(texto: str) -> str:
    return f"Thought: ya tengo la respuesta\nFinal Answer: {texto}"


def usar_herramienta(nombre: str, argumentos: str) -> str:
    return f"Thought: necesito usar {nombre}\nAction: {nombre}\nAction Input: {argumentos}"


class LLMGuionado(BaseLLM):
    model: str = "guionado"
    respuestas: list[str] | Callable[[list[dict[str, Any]]], str] = Field(default_factory=list)
    repetir_ultima: bool = True
    llamadas: list[list[dict[str, Any]]] = Field(default_factory=list)

    def __init__(self, **datos: Any) -> None:
        datos.setdefault("model", "guionado")  # BaseLLM valida el nombre antes de aplicar defaults
        super().__init__(**datos)

    def call(self, messages, tools=None, callbacks=None, available_functions=None, from_task=None,
             from_agent=None, response_model=None, **kwargs) -> str:
        mensajes = [{"role": "user", "content": messages}] if isinstance(messages, str) else list(messages)
        self.llamadas.append(mensajes)
        if callable(self.respuestas):
            return self.respuestas(mensajes)
        indice = len(self.llamadas) - 1
        if indice >= len(self.respuestas):
            if not (self.repetir_ultima and self.respuestas):
                raise AssertionError(f"LLMGuionado: se pidió la respuesta #{indice + 1} y solo hay {len(self.respuestas)}")
            indice = len(self.respuestas) - 1
        return self.respuestas[indice]

    async def acall(self, messages, *args, **kwargs) -> str:
        return self.call(messages, *args, **kwargs)

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 32_000

    def texto_de_llamada(self, indice: int = -1) -> str:
        """Todo el texto que recibió el LLM en una llamada (por defecto, la última)."""
        return "\n".join(str(m.get("content", "")) for m in self.llamadas[indice])
