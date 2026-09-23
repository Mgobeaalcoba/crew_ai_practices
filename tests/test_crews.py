"""Tests offline de ejemplos/02_crews."""

import asyncio
import unittest
from unittest import mock

from crewai import Process

from tests.utilidades import LLMGuionado, ejemplo, json_final, respuesta_final, responder_segun


class TestSecuencial(unittest.TestCase):
    m = ejemplo("02_crews/01_secuencial")

    def test_cada_tarea_recibe_las_anteriores(self):
        llm = LLMGuionado(respuestas=[respuesta_final("IDEA-X"), respuesta_final("GUION-Y"), respuesta_final("1. Título")])
        salida = self.m.construir_crew("agua", llm=llm).kickoff()
        self.assertEqual([t.raw for t in salida.tasks_output], ["IDEA-X", "GUION-Y", "1. Título"])
        self.assertIn("GUION-Y", llm.texto_de_llamada(2))  # context=[idea, guion]
        self.assertIn("IDEA-X", llm.texto_de_llamada(2))


class TestJerarquico(unittest.TestCase):
    m = ejemplo("02_crews/02_jerarquico")

    def test_manager_generico_y_propio(self):
        generico = self.m.construir_crew(llm=LLMGuionado(), llm_manager=LLMGuionado())
        self.assertEqual(generico.process, Process.hierarchical)
        self.assertIsNotNone(generico.manager_llm)
        self.assertTrue(all(t.agent is None for t in generico.tasks))  # las asigna el manager

        propio = self.m.construir_crew(manager_propio=True, llm=LLMGuionado(), llm_manager=LLMGuionado())
        self.assertEqual(propio.manager_agent.role, "Coordinador de consultas")

    def test_el_manager_delega_en_un_trabajador(self):
        delegar = ('Thought: le pregunto al contador\nAction: ask_question_to_coworker\n'
                   'Action Input: {"question": "¿Cuánto es el SAC?", "context": "Mejor sueldo $900.000", "coworker": "Contador"}')
        llm = LLMGuionado(respuestas=responder_segun(
            [("You are Contador", respuesta_final("La mitad de 900.000: $450.000")),  # el contador responde
             ("La mitad de 900.000", respuesta_final("SAC: $450.000"))],  # el manager ya tiene la respuesta
            por_defecto=delegar,
        ))
        salida = self.m.construir_crew(llm=llm, llm_manager=llm).kickoff()
        self.assertEqual(salida.raw, "SAC: $450.000")
        textos = ["\n".join(str(m["content"]) for m in llamada) for llamada in llm.llamadas]
        self.assertTrue(any("You are Contador" in t for t in textos))  # el trabajador fue consultado


class TestDelegacion(unittest.TestCase):
    m = ejemplo("02_crews/03_delegacion")

    def test_solo_el_responsable_puede_delegar(self):
        crew = self.m.construir_crew(llm=LLMGuionado())
        responsable, nutricionista = crew.agents
        self.assertTrue(responsable.allow_delegation)
        self.assertFalse(nutricionista.allow_delegation)


class TestCondicionales(unittest.TestCase):
    m = ejemplo("02_crews/04_tareas_condicionales")

    def _correr(self, urgente: bool):
        llm = LLMGuionado(respuestas=[
            json_final({"categoria": "corte", "urgente": urgente, "motivo": "x"}),
            respuesta_final("PRIORIDAD: URGENTE"),
        ])
        return self.m.construir_crew("reclamo", llm=llm).kickoff(), llm

    def test_urgente_escala(self):
        salida, llm = self._correr(urgente=True)
        self.assertEqual(salida.tasks_output[1].raw, "PRIORIDAD: URGENTE")
        self.assertEqual(len(llm.llamadas), 2)

    def test_no_urgente_saltea_la_tarea(self):
        salida, llm = self._correr(urgente=False)
        self.assertEqual(salida.tasks_output[1].raw, "")
        self.assertEqual(len(llm.llamadas), 1)  # el supervisor nunca se llamó


class TestAsincronas(unittest.TestCase):
    m = ejemplo("02_crews/05_tareas_asincronas")

    def test_la_recomendacion_ve_ventajas_y_riesgos(self):
        llm = LLMGuionado(respuestas=responder_segun(
            [("3 ventajas", respuesta_final("VENTAJA-1")), ("3 riesgos", respuesta_final("RIESGO-1"))],
            por_defecto=respuesta_final("Avanzar por etapas"),
        ))
        crew = self.m.construir_crew("migrar", llm=llm)
        self.assertEqual([t.async_execution for t in crew.tasks], [True, True, False])
        salida = crew.kickoff()
        self.assertEqual(salida.raw, "Avanzar por etapas")
        final = llm.texto_de_llamada(-1)
        self.assertIn("VENTAJA-1", final)
        self.assertIn("RIESGO-1", final)


class TestPlanificacionDelCrew(unittest.TestCase):
    m = ejemplo("02_crews/06_planificacion")

    def test_el_plan_se_agrega_a_las_tareas(self):
        plan = {"list_of_plans_per_task": [
            {"task_number": 1, "task": "temario", "plan": "PLAN-TEMARIO"},
            {"task_number": 2, "task": "ejercicio", "plan": "PLAN-EJERCICIO"},
        ]}
        crew = self.m.construir_crew(llm=LLMGuionado(respuestas=[respuesta_final("hecho")]),
                                     llm_planificador=LLMGuionado(respuestas=[json_final(plan)]))
        crew.kickoff()
        self.assertIn("PLAN-TEMARIO", crew.tasks[0].description)
        self.assertIn("PLAN-EJERCICIO", crew.tasks[1].description)


class TestHumanoEnElBucle(unittest.TestCase):
    m = ejemplo("02_crews/07_humano_en_el_bucle")

    def test_el_comentario_humano_hace_rehacer_la_respuesta(self):
        llm = LLMGuionado(respuestas=[respuesta_final("Asado el viernes"), respuesta_final("¡Asado el viernes 12/12 a las 20! 🥩")])
        # 1ª respuesta del humano: una corrección; 2ª: Enter vacío = aprobar
        with mock.patch("builtins.input", side_effect=["Agregá fecha y hora", ""]):
            salida = self.m.construir_crew("asado", llm=llm).kickoff()
        self.assertEqual(salida.raw, "¡Asado el viernes 12/12 a las 20! 🥩")
        self.assertIn("Agregá fecha y hora", llm.texto_de_llamada(1))


class TestProyectoYaml(unittest.TestCase):
    def test_arma_el_crew_desde_los_yaml(self):
        import importlib

        crew_mod = importlib.import_module("ejemplos.02_crews.08_proyecto_yaml.crew")
        llm = LLMGuionado(respuestas=[respuesta_final("ANALISIS"), respuesta_final("1. Slogan")])
        proyecto = crew_mod.CrewSlogans(llm=llm)
        crew = proyecto.crew()
        self.assertEqual([a.role for a in crew.agents], ["Investigador de {producto}", "Publicista"])
        salida = crew.kickoff(inputs={"producto": "  "})
        self.assertIn("un mate térmico", llm.texto_de_llamada(0))  # before_kickoff completó el input vacío
        self.assertTrue(salida.raw.endswith("(generado por CrewSlogans)"))  # after_kickoff


class TestEjecucionMultiple(unittest.TestCase):
    m = ejemplo("02_crews/09_ejecucion_multiple")

    def _llm(self):
        return LLMGuionado(respuestas=lambda mensajes: respuesta_final(
            next(c for c in ("Salta", "Ushuaia", "Mendoza", "Córdoba") if c in str(mensajes))))

    def test_kickoff_for_each_interpola_cada_input(self):
        salidas = self.m.construir_crew(self._llm()).kickoff_for_each(inputs=self.m.CIUDADES)
        self.assertEqual([s.raw for s in salidas], ["Salta", "Ushuaia", "Mendoza"])

    def test_en_paralelo(self):
        salidas = asyncio.run(self.m.en_paralelo(self._llm()))
        self.assertEqual(sorted(s.raw for s in salidas), ["Mendoza", "Salta", "Ushuaia"])


if __name__ == "__main__":
    unittest.main()
