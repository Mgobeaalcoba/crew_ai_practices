"""Tests de ejemplos/04_observabilidad."""

import unittest

from crewai.events import crewai_event_bus
from crewai.hooks import clear_all_global_hooks

from tests.utilidades import LLMGuionado, ejemplo, respuesta_final, usar_herramienta


class TestHooks(unittest.TestCase):
    m = ejemplo("04_observabilidad/01_hooks")

    def tearDown(self):
        clear_all_global_hooks()

    def test_bloquea_borrados_y_enmascara_el_dni(self):
        llm = LLMGuionado(respuestas=[
            usar_herramienta("buscar_cliente", '{"numero": "123"}'),
            usar_herramienta("borrar_cliente", '{"numero": "456"}'),
            respuesta_final("listo"),
        ])
        self.m.registrar_hooks()
        self.m.construir_agente(llm).kickoff("buscá 123 y borrá 456")
        self.assertIn("DNI ***", llm.texto_de_llamada(1))
        self.assertNotIn("30.456.789", llm.texto_de_llamada(1))
        self.assertIn("456", self.m.CLIENTES)  # el borrado no se ejecutó
        self.assertEqual(self.m.estadisticas["herramientas_bloqueadas"], 1)


class TestEventos(unittest.TestCase):
    def test_el_listener_registra_crew_y_tareas(self):
        m = ejemplo("04_observabilidad/02_eventos")
        with crewai_event_bus.scoped_handlers():
            metricas = m.Metricas()
            m.construir_crew(LLMGuionado(respuestas=[respuesta_final("haiku"), respuesta_final("lindo")])).kickoff()
            crewai_event_bus.flush()
        self.assertEqual(metricas.registro[0], "crew 'taller de poesía' iniciado")
        self.assertEqual(sum("tarea terminada" in r for r in metricas.registro), 2)
        self.assertTrue(metricas.registro[-1].startswith("crew terminado"))


class TestCallbacks(unittest.TestCase):
    def test_orden_de_los_callbacks(self):
        m = ejemplo("04_observabilidad/03_callbacks")
        bitacora: list[str] = []
        llm = LLMGuionado(respuestas=[respuesta_final("Zapallo al horno")])
        salida = m.construir_crew(bitacora, llm=llm).kickoff(inputs={"ingrediente": "  ZAPALLO "})
        etiquetas = [linea.split("]")[0] + "]" for linea in bitacora]
        self.assertEqual(etiquetas, ["[before_kickoff]", "[step_callback]", "[task.callback]",
                                     "[crew.task_callback]", "[after_kickoff]"])
        self.assertIn("con zapallo", llm.texto_de_llamada(0))  # before_kickoff normalizó el input
        self.assertTrue(salida.raw.endswith("Recetario del repo crew-practices"))


if __name__ == "__main__":
    unittest.main()
