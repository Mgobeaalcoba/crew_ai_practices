"""Tests contra un LLM real (el de LLM_PROVEEDOR, Groq por defecto). Gastan tokens: se activan con CREW_VIVO=1.

    CREW_VIVO=1 uv run python -m unittest -b tests.test_vivo

Verifican propiedades que no dependen de la redacción exacta (números, categorías, formato), porque un LLM
real no responde dos veces igual.
"""

import sys
import unittest
from unittest import mock

from tests.utilidades import ejemplo, requiere_embeddings, requiere_vivo


@requiere_vivo
class TestVivo(unittest.TestCase):
    def test_agente_solo_con_salida_estructurada(self):
        m = ejemplo("01_agentes/01_agente_solo")
        definicion = m.definir(m.construir_agente(), "API")
        self.assertTrue(definicion.definicion and definicion.ejemplo)

    def test_herramientas_calculan_el_presupuesto_exacto(self):
        m = ejemplo("01_agentes/02_herramientas")
        respuesta = m.construir_agente().kickoff("¿Cuánto sale en total comprar 2 teclados y mandarlos a Córdoba?").raw
        self.assertRegex(respuesta.replace(".", "").replace(",", ""), r"54480")

    def test_mcp_ve_todos_los_libros(self):
        m = ejemplo("01_agentes/03_mcp")
        with mock.patch("sys.stderr", sys.__stderr__):
            respuesta = m.construir_agente().kickoff("¿Qué libros de Borges hay disponibles?").raw
        self.assertIn("Aleph", respuesta)

    def test_salida_estructurada(self):
        m = ejemplo("01_agentes/08_salida_estructurada")
        aviso = m.extraer_con_output_pydantic("Vendo bici rodado 29, $350.000, Palermo")
        self.assertEqual(aviso.precio, 350000)

    def test_guardrails_cumplen(self):
        m = ejemplo("01_agentes/07_guardrails")
        post = m.construir_crew("una feria de libros usados en La Plata").kickoff().raw
        self.assertLessEqual(len(post), m.MAX_CARACTERES)
        self.assertNotRegex(post, r"#\w+")

    def test_flow_clasifica_y_rutea(self):
        m = ejemplo("03_flows/07_flow_con_agentes")
        flow = m.crear_flow()
        flow.kickoff(inputs={"mail": "Me cobraron dos veces la factura de septiembre"})
        self.assertEqual(flow.state.clasificacion.categoria, "facturacion")

    @requiere_embeddings
    def test_knowledge_cita_la_politica(self):
        m = ejemplo("01_agentes/04_knowledge")
        respuesta = m.responder("¿Cuántos meses de garantía tiene una amoladora si soy Socio Tuerca?").lower()
        self.assertIn("18", respuesta)


if __name__ == "__main__":
    unittest.main()
