"""Tests offline de ejemplos/01_agentes: sin red ni tokens, con LLMGuionado."""

import json
import sys
import unittest
from unittest import mock

from crewai.tools import ToolFailure

from tests.utilidades import (
    LLMGuionado,
    ejemplo,
    json_final,
    requiere_docker,
    requiere_embeddings,
    respuesta_final,
    usar_herramienta,
)


class TestAgenteSolo(unittest.TestCase):
    m = ejemplo("01_agentes/01_agente_solo")

    def test_pregunta_libre(self):
        llm = LLMGuionado(respuestas=[respuesta_final("Una API es un contrato entre programas.")])
        self.assertIn("contrato", self.m.preguntar(self.m.construir_agente(llm), "¿Qué es una API?"))

    def test_respuesta_estructurada(self):
        llm = LLMGuionado(respuestas=[json_final({"termino": "API", "definicion": "Un contrato.", "ejemplo": "El mozo."})])
        definicion = self.m.definir(self.m.construir_agente(llm), "API")
        self.assertIsInstance(definicion, self.m.Definicion)
        self.assertEqual(definicion.ejemplo, "El mozo.")

    def test_inyecta_la_fecha(self):
        llm = LLMGuionado(respuestas=[respuesta_final("ok")])
        self.m.preguntar(self.m.construir_agente(llm), "hola")
        self.assertRegex(llm.texto_de_llamada(0), r"\d{4}-\d{2}-\d{2}")  # inject_date=True


class TestHerramientas(unittest.TestCase):
    m = ejemplo("01_agentes/02_herramientas")

    def test_consultar_producto(self):
        self.assertIn("25,000", self.m.consultar_producto.run(producto="Teclado"))
        self.assertIsInstance(self.m.consultar_producto.run(producto="parlante"), ToolFailure)

    def test_calcular_envio_valida_argumentos(self):
        herramienta = self.m.CalcularEnvio()
        self.assertIn("4,480", herramienta.run(peso_kg=1.6, provincia="Córdoba"))
        self.assertIsInstance(herramienta.run(peso_kg=1, provincia="Marte"), ToolFailure)

    def test_el_agente_encadena_las_dos_herramientas(self):
        llm = LLMGuionado(respuestas=[
            usar_herramienta("consultar_producto", '{"producto": "teclado"}'),
            usar_herramienta("calcular_envio", '{"peso_kg": 1.6, "provincia": "Córdoba"}'),
            respuesta_final("Total: $54.480"),
        ])
        self.assertEqual(self.m.construir_agente(llm).kickoff("2 teclados a Córdoba").raw, "Total: $54.480")
        self.assertIn("precio unitario $25,000", llm.texto_de_llamada(1))
        self.assertIn("$4,480", llm.texto_de_llamada(2))


class TestMCP(unittest.TestCase):
    m = ejemplo("01_agentes/03_mcp")

    def test_servidor_devuelve_un_solo_bloque_json(self):
        import importlib

        servidor = importlib.import_module("ejemplos.01_agentes.03_mcp.servidor")
        libros = json.loads(servidor.buscar_por_autor("borges"))
        self.assertEqual({l["titulo"] for l in libros}, {"Ficciones", "El Aleph"})

    def test_los_nombres_de_herramienta_entran_en_64_caracteres(self):
        # CrewAI antepone "<comando>_<args>_" y trunca a 64: si se pasa, el nombre real se pierde
        config = self.m.configurar_servidor(permitir_reservas=True)
        prefijo = f"{config.command}_{'_'.join(config.args)}"
        for herramienta in ("buscar_por_autor", "consultar_libro", "reservar"):
            self.assertLessEqual(len(f"{prefijo}_{herramienta}"), 64)

    def test_agente_con_servidor_mcp_real(self):
        # Lanza el servidor MCP de verdad (subproceso local); solo el LLM es falso
        herramienta = "python_ejemplos_01_agentes_03_mcp_servidor_py_buscar_por_autor"
        llm = LLMGuionado(respuestas=[
            usar_herramienta(herramienta, '{"autor": "Borges"}'),
            respuesta_final("El Aleph está disponible."),
        ])
        # el cliente stdio de MCP necesita un stderr real (con fileno); `unittest -b` lo reemplaza por un buffer
        with mock.patch("sys.stderr", sys.__stderr__):
            respuesta = self.m.construir_agente(llm).kickoff("¿Qué hay de Borges?")
        self.assertEqual(respuesta.raw, "El Aleph está disponible.")
        self.assertIn("El Aleph", llm.texto_de_llamada(1))
        self.assertNotIn("reservar", llm.texto_de_llamada(0))  # filtrada por tool_filter


class TestKnowledge(unittest.TestCase):
    m = ejemplo("01_agentes/04_knowledge")

    def test_las_fuentes_apuntan_a_archivos_existentes(self):
        archivo, texto = self.m.fuentes()
        self.assertTrue(all(p.exists() for p in archivo.file_paths))
        self.assertIn("0800", texto.content)

    @requiere_embeddings
    def test_el_crew_inyecta_los_fragmentos_relevantes_en_el_prompt(self):
        llm = LLMGuionado(respuestas=[respuesta_final("No, las herramientas eléctricas usadas no se aceptan.")])
        self.m.responder("¿Puedo devolver un taladro usado?", llm=llm)
        self.assertIn("herramientas eléctricas usadas no se aceptan", llm.texto_de_llamada(-1))


class TestMemoria(unittest.TestCase):
    m = ejemplo("01_agentes/05_memoria")

    @requiere_embeddings
    def test_recuerda_y_recupera(self):
        # El LLM falso también hace el análisis de cada recuerdo; con importancia y scope explícitos
        # la memoria no necesita que el LLM devuelva un análisis válido.
        memoria = self.m.crear_memoria(llm=LLMGuionado(respuestas=[respuesta_final("{}")]))
        memoria.reset()
        memoria.remember("A Juan hay que escribirle por WhatsApp.", scope="/test", categories=["contacto"], importance=0.8)
        memoria.remember("El depósito cierra en diciembre.", scope="/test", categories=["operacion"], importance=0.5)
        resultados = memoria.recall("¿cómo contacto a Juan?", limit=1, depth="shallow")
        self.assertIn("WhatsApp", resultados[0].record.content)
        memoria.reset()


class TestPlanificacion(unittest.TestCase):
    m = ejemplo("01_agentes/06_planificacion")

    def test_configuracion(self):
        agente = self.m.construir_agente(LLMGuionado(), esfuerzo="high")
        self.assertEqual(agente.planning_config.reasoning_effort, "high")
        self.assertEqual(self.m.temperatura_maxima.run(dia="Martes"), "Martes: 22 °C")


class TestGuardrails(unittest.TestCase):
    m = ejemplo("01_agentes/07_guardrails")

    def test_el_guardrail_rechaza_y_el_agente_corrige(self):
        largo = "Llegó la app " + "muy " * 100
        llm = LLMGuionado(respuestas=[
            respuesta_final(largo),  # 1º intento: demasiado largo
            respuesta_final("Nueva app de delivery en bici #Rosario"),  # 2º: tiene hashtag
            respuesta_final("Nueva app de delivery en bici en Rosario."),  # 3º: cumple las funciones
            json_final({"valid": True, "feedback": None}),  # el LLMGuardrail aprueba
        ])
        salida = self.m.construir_crew("delivery", llm=llm).kickoff()
        self.assertEqual(salida.raw, "Nueva app de delivery en bici en Rosario.")
        self.assertIn("caracteres y el máximo es 280", llm.texto_de_llamada(1))  # el motivo volvió al agente
        self.assertIn("No uses hashtags", llm.texto_de_llamada(2))


class TestSalidaEstructurada(unittest.TestCase):
    m = ejemplo("01_agentes/08_salida_estructurada")
    aviso = {"producto": "bici", "precio": 350000, "estado": "usado", "ubicacion": "Palermo", "etiquetas": ["bici", "r29"]}

    def test_output_pydantic(self):
        llm = LLMGuionado(respuestas=[json_final(self.aviso)])
        self.assertEqual(self.m.extraer_con_output_pydantic("Vendo bici", llm=llm).precio, 350000)

    def test_json_en_texto_tolera_texto_alrededor(self):
        llm = LLMGuionado(respuestas=[respuesta_final("Acá va:\n```json\n" + json.dumps(self.aviso) + "\n```")])
        self.assertEqual(self.m.extraer_con_json_en_texto("Vendo bici", llm=llm).ubicacion, "Palermo")

    def test_json_invalido_devuelve_none(self):
        llm = LLMGuionado(respuestas=[respuesta_final("No encontré datos")])
        self.assertIsNone(self.m.extraer_con_json_en_texto("???", llm=llm))


class TestEjecucionDeCodigo(unittest.TestCase):
    m = ejemplo("01_agentes/09_ejecucion_de_codigo")

    def test_el_fallo_de_docker_se_informa_como_toolfailure(self):
        with mock.patch.object(self.m, "ejecutar_en_docker", return_value=(1, "NameError")):
            self.assertIsInstance(self.m.ejecutar_python.run(codigo="x"), ToolFailure)

    @requiere_docker
    def test_ejecuta_en_el_contenedor_sin_red(self):
        codigo = "import urllib.request\ntry:\n urllib.request.urlopen('http://example.com', timeout=3)\nexcept OSError:\n print('sin red')\nprint(2**10)"
        self.assertEqual(self.m.ejecutar_python.run(codigo=codigo), "sin red\n1024")


class TestA2A(unittest.TestCase):
    m = ejemplo("01_agentes/10_a2a")

    def test_sin_el_extra_avisa_y_sale_con_2(self):
        if self.m.a2a_disponible():
            self.skipTest("a2a-sdk instalado")
        with mock.patch("sys.argv", ["main.py"]):
            self.assertEqual(self.m.main(), 2)


if __name__ == "__main__":
    unittest.main()
