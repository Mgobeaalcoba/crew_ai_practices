"""Tests de las piezas compartidas: fábrica de LLMs, embeddings, LLM falso, herramientas y lanzador."""

import os
import unittest
from unittest import mock

from crewai import Agent

from comun import PROVEEDORES, config_embedder, contar, contar_palabras, crear_llm
from comun.llm import resolver
from tests.utilidades import LLMGuionado, respuesta_final, usar_herramienta

import main as lanzador


class TestResolverProveedor(unittest.TestCase):
    def test_groq_es_el_proveedor_por_defecto(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            nombre, config, modelo, max_tokens = resolver()
        self.assertEqual(nombre, "groq")
        self.assertEqual(modelo, "qwen/qwen3.8-27b")
        self.assertEqual(max_tokens, 900)  # sin tope, Groq responde 429 por OTPM

    def test_acepta_los_nombres_viejos_de_groq(self):
        with mock.patch.dict(os.environ, {"GROQ_MODEL": "otro/modelo", "GROQ_MAX_TOKENS": "500"}, clear=True):
            _, _, modelo, max_tokens = resolver()
        self.assertEqual((modelo, max_tokens), ("otro/modelo", 500))

    def test_las_variables_nuevas_ganan(self):
        entorno = {"LLM_PROVEEDOR": "ollama", "LLM_MODELO": "llama3.2", "LLM_MAX_TOKENS": "256"}
        with mock.patch.dict(os.environ, entorno, clear=True):
            self.assertEqual(resolver()[0::2], ("ollama", "llama3.2"))
            self.assertEqual(resolver()[3], 256)

    def test_proveedor_desconocido(self):
        with self.assertRaisesRegex(ValueError, "Proveedor desconocido"):
            resolver("inventado")

    def test_proveedor_sin_modelo_por_defecto_exige_llm_modelo(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, "LLM_MODELO"):
            resolver("openai")

    def test_falta_la_key(self):
        with mock.patch.dict(os.environ, {}, clear=True), self.assertRaisesRegex(ValueError, "ANTHROPIC_API_KEY"):
            crear_llm(proveedor="anthropic")

    def test_crea_el_llm_con_el_proveedor_nativo_openai(self):
        with mock.patch.dict(os.environ, {"GROQ_API_KEY": "x"}, clear=True):
            llm = crear_llm(0.3)
        # "openai/" es el proveedor; el resto es el id de Groq. Con "groq/..." Groq responde 400.
        self.assertEqual(llm.model, "qwen/qwen3.8-27b")
        self.assertEqual(llm.base_url, PROVEEDORES["groq"].base_url)
        self.assertEqual((llm.temperature, llm.max_tokens), (0.3, 900))

    def test_los_locales_no_piden_key(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            llm = crear_llm(proveedor="ollama")
        self.assertEqual(llm.base_url, "http://localhost:11434/v1")


class TestEmbeddings(unittest.TestCase):
    def test_por_defecto_lm_studio_via_protocolo_openai(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            config = config_embedder()
        self.assertEqual(config["provider"], "openai")
        self.assertEqual(config["config"]["api_base"], "http://localhost:1234/v1")
        self.assertEqual(config["config"]["model_name"], "text-embedding-nomic-embed-text-v1.5")

    def test_desconocido(self):
        with self.assertRaises(ValueError):
            config_embedder("inventado")


class TestLLMGuionado(unittest.TestCase):
    def test_responde_en_orden_y_repite_la_ultima(self):
        llm = LLMGuionado(respuestas=["a", "b"])
        self.assertEqual([llm.call("x") for _ in range(3)], ["a", "b", "b"])
        self.assertEqual(len(llm.llamadas), 3)

    def test_un_agente_usa_herramientas_con_el_llm_falso(self):
        llm = LLMGuionado(respuestas=[
            usar_herramienta("contar_palabras", '{"texto": "uno dos tres"}'),
            respuesta_final("Son 3 palabras"),
        ])
        agente = Agent(role="Contador", goal="Contar", backstory="Preciso.", llm=llm, tools=[contar_palabras])
        self.assertEqual(agente.kickoff("¿Cuántas palabras?").raw, "Son 3 palabras")
        self.assertIn("3 palabras", llm.texto_de_llamada(1))  # el resultado de la herramienta volvió al LLM


class TestHerramientas(unittest.TestCase):
    def test_contar(self):
        self.assertEqual(contar("  hola   mundo \n lindo "), 3)
        self.assertEqual(contar_palabras.run(texto="a b"), "2 palabras")


class TestLanzador(unittest.TestCase):
    def test_encuentra_todos_los_ejemplos(self):
        nombres = [d.name for d in lanzador.listar()]
        self.assertIn("01_agente_solo", nombres)
        self.assertIn("01_redactor_editor", nombres)
        self.assertGreaterEqual(len(nombres), 30)

    def test_busqueda_parcial(self):
        self.assertEqual([d.name for d in lanzador.buscar("agente_solo")], ["01_agente_solo"])
        self.assertGreater(len(lanzador.buscar("01_")), 1)  # ambiguo: el lanzador lista las opciones


if __name__ == "__main__":
    unittest.main()
