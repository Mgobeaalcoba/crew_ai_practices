"""Tests de ejemplos/06_integrador y ejemplos/05_proveedores_llm."""

import json
import unittest
from unittest import mock

from tests.utilidades import LLMGuionado, ejemplo, respuesta_final, responder_segun

base = ejemplo("06_integrador/01_redactor_editor")


def veredicto(aprobado: bool, palabras: int = 180, correcciones: str = "") -> str:
    return respuesta_final(json.dumps({"datos_concretos": ["2025"], "palabras": palabras,
                                       "aprobado": aprobado, "correcciones": correcciones}))


class TestGuardaYVeredicto(unittest.TestCase):
    def test_leer_veredicto_con_texto_alrededor(self):
        texto = 'Mi veredicto: {"datos_concretos": [], "palabras": 10, "aprobado": true, "correcciones": ""} fin'
        self.assertTrue(base.leer_veredicto(texto).aprobado)
        self.assertIsNone(base.leer_veredicto("sin json"))

    def test_la_guarda_corrige_al_editor_que_cuenta_mal(self):
        largo = "palabra " * (base.MAX_PALABRAS + 31)
        v = base.Veredicto(datos_concretos=[], palabras=250, aprobado=True, correcciones="")
        aprobado, correcciones = base.evaluar(v, largo)
        self.assertFalse(aprobado)
        self.assertIn(f"Conteo real: {base.MAX_PALABRAS + 31}", correcciones)

    def test_veredicto_invalido_es_rechazo(self):
        self.assertFalse(base.evaluar(None, "texto")[0])


def llm_redaccion(veredictos: list[str]) -> LLMGuionado:
    """LLM falso para todo el equipo: cada agente se reconoce por su rol en el prompt de sistema."""
    pendientes = iter(veredictos)
    reglas = responder_segun(
        [("You are Investigador", respuesta_final("- Dato 2025 (https://ejemplo.com)")),
         ("You are Redactor", respuesta_final("Borrador corto con el dato 2025."))],
        por_defecto="",
    )
    return LLMGuionado(respuestas=lambda mensajes: reglas(mensajes) or next(pendientes))


class TestRedactorEditor(unittest.TestCase):
    def test_aprueba_en_la_primera_ronda(self):
        aprobado, borrador, rondas = base.revisar("tema", llm=llm_redaccion([veredicto(True)]))
        self.assertTrue(aprobado)
        self.assertEqual((borrador, rondas), ("Borrador corto con el dato 2025.", 1))

    def test_rechaza_reescribe_y_aprueba(self):
        llm = llm_redaccion([veredicto(False, correcciones="Agregá otro dato"), veredicto(True)])
        aprobado, _, rondas = base.revisar("tema", llm=llm)
        self.assertTrue(aprobado)
        self.assertEqual(rondas, 2)

    def test_se_rinde_tras_max_rondas(self):
        llm = llm_redaccion([veredicto(False, correcciones="no")] * base.MAX_RONDAS)
        aprobado, _, rondas = base.revisar("tema", llm=llm)
        self.assertFalse(aprobado)
        self.assertEqual(rondas, base.MAX_RONDAS)


class TestRedactorEditorFlow(unittest.TestCase):
    m = ejemplo("06_integrador/02_redactor_editor_flow")

    def test_mismo_comportamiento_con_flow(self):
        flow = self.m.crear_flow(llm_redaccion([veredicto(False, correcciones="más datos"), veredicto(True)]))
        self.assertEqual(flow.kickoff(inputs={"tema": "tema"}), "Borrador corto con el dato 2025.")
        self.assertTrue(flow.state.aprobado)
        self.assertEqual(flow.state.ronda, 2)


class TestComparadorDeProveedores(unittest.TestCase):
    m = ejemplo("05_proveedores_llm/01_comparar_proveedores")

    def test_omite_proveedores_sin_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            disponible, motivo, _ = self.m.disponibilidad("anthropic")
        self.assertFalse(disponible)
        self.assertIn("ANTHROPIC_API_KEY", motivo)

    def test_local_elige_un_modelo_de_chat(self):
        with mock.patch.object(self.m, "modelos_locales", return_value=["text-embedding-x", "qwen3-4b"]):
            self.assertEqual(self.m.disponibilidad("lmstudio"), (True, "", "qwen3-4b"))

    def test_pregunta_con_cualquier_llm(self):
        respuesta, _ = self.m.preguntar("groq", "x", llm=LLMGuionado(respuestas=[respuesta_final("Un programa.")]))
        self.assertEqual(respuesta, "Un programa.")


if __name__ == "__main__":
    unittest.main()
