"""Tests de ejemplos/03_flows. Los cinco primeros no usan LLM: se prueban tal cual."""

import unittest

from tests.utilidades import LLMGuionado, ejemplo, json_final, respuesta_final, responder_segun


class TestFlowBasico(unittest.TestCase):
    def test_encadena_los_pasos(self):
        m = ejemplo("03_flows/01_basico")
        self.assertEqual(m.FlowPedido().kickoff(), "Total a pagar: $7.700")


class TestEstado(unittest.TestCase):
    m = ejemplo("03_flows/02_estado")

    def test_no_estructurado(self):
        self.assertEqual(self.m.FlowContadorLibre().kickoff(), 3)

    def test_estructurado_con_inputs(self):
        flow = self.m.FlowCarrito()
        flow.kickoff(inputs={"cliente": "Marta"})
        self.assertEqual(flow.state.cliente, "Marta")
        self.assertTrue(flow.state.descuento_aplicado)
        self.assertAlmostEqual(flow.state.total, 11_070)
        self.assertTrue(flow.state.id)  # todo estado tiene un id automático


class TestRouter(unittest.TestCase):
    def test_las_tres_ramas(self):
        m = ejemplo("03_flows/03_router")
        self.assertEqual(m.decidir(820), "Crédito aprobado automáticamente")
        self.assertEqual(m.decidir(610), "Pasa a revisión manual de un analista")
        self.assertEqual(m.decidir(300), "Crédito rechazado")


class TestParaleloAndOr(unittest.TestCase):
    def test_or_con_el_primero_y_and_con_todos(self):
        m = ejemplo("03_flows/04_paralelo_and_or")
        flow = m.FlowCotizacion()
        resultado = flow.kickoff()
        self.assertEqual(flow.state.primera_respuesta, "B")  # B tarda menos
        self.assertEqual(flow.state.eventos[-1], "comparación hecha")  # and_ esperó a los dos
        self.assertIn("proveedor A", resultado)
        self.assertLess(flow.state.duracion, 0.49)  # en serie serían ≥ 0.5 s


class TestPersistencia(unittest.TestCase):
    def test_retoma_el_estado_por_id(self):
        m = ejemplo("03_flows/05_persistencia")
        primero = m.ejecutar()
        segundo = m.ejecutar(primero.id)
        self.assertEqual(segundo.id, primero.id)
        self.assertEqual(segundo.renovaciones, 2)
        self.assertEqual(segundo.historial, ["renovación #1", "renovación #2"])


class TestHumanFeedback(unittest.TestCase):
    m = ejemplo("03_flows/06_human_feedback")

    def _correr(self, respuesta_humana: str, etiqueta: str):
        # El LLM falso hace de clasificador de la respuesta libre: devuelve la etiqueta directamente
        flow = self.m.crear_flow(self.m.RespuestaFija(respuesta_humana), llm=LLMGuionado(respuestas=[etiqueta]))
        return flow, flow.kickoff()

    def test_aprobado(self):
        flow, resultado = self._correr("dale", "aprobado")
        self.assertEqual(flow.state.estado, "publicada")
        self.assertIn("'dale'", resultado)

    def test_rechazado(self):
        flow, _ = self._correr("ni loco", "rechazado")
        self.assertEqual(flow.state.estado, "descartada")


class TestFlowConAgentes(unittest.TestCase):
    m = ejemplo("03_flows/07_flow_con_agentes")

    def _correr(self, categoria: str):
        llm = LLMGuionado(respuestas=responder_segun(
            [("Clasificador", json_final({"categoria": categoria, "resumen": "x"}))],
            por_defecto=respuesta_final(f"RESPUESTA-{categoria}"),
        ))
        flow = self.m.crear_flow(llm)
        flow.kickoff(inputs={"mail": "hola"})
        return flow.state

    def test_rutea_al_especialista(self):
        self.assertEqual(self._correr("facturacion").respuesta, "RESPUESTA-facturacion")
        self.assertEqual(self._correr("tecnico").respuesta, "RESPUESTA-tecnico")

    def test_otro_no_llama_a_ningun_especialista(self):
        self.assertIn("derivada a una persona", self._correr("otro").respuesta)


class TestFlowConCrews(unittest.TestCase):
    def test_reintenta_si_es_muy_largo(self):
        m = ejemplo("03_flows/08_flow_con_crews")
        llm = LLMGuionado(respuestas=[
            respuesta_final("1. a\n2. b\n3. c"),  # esquema
            respuesta_final("palabra " * 200),  # 1er artículo: demasiado largo
            respuesta_final("Un artículo corto."),  # 2º: cumple
        ])
        flow = m.crear_flow(llm)
        self.assertEqual(flow.kickoff(inputs={"tema": "mate"}), "Un artículo corto.")
        self.assertEqual(flow.state.intentos, 2)
        self.assertIn("Tiene 200 palabras", llm.texto_de_llamada(2))  # la corrección llegó al redactor


if __name__ == "__main__":
    unittest.main()
