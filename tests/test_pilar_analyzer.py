import unittest
import os

from src.skills.case_04_otimizacao_pilares.pilar_analyzer import TQSColumnAnalyzer, EdificioPilaresResumo
from src.skills.case_04_otimizacao_pilares.skill import OtimizacaoPilaresSkill
from src.agent.tools import ToolsRegistry

class TestPilarAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edificio = "054"
        cls.analyzer = TQSColumnAnalyzer(cls.edificio)

    def test_analise_completa_edificio_054(self):
        """Testa o processamento integral dos pilares do edificio 054."""
        resumo = self.analyzer.analisar()
        self.assertIsInstance(resumo, EdificioPilaresResumo)
        self.assertEqual(resumo.total_pilares, 69)
        self.assertEqual(resumo.total_lances, 138)
        self.assertGreaterEqual(resumo.total_nao_dimensionados, 1)

        # Verifica pilares criticos nao dimensionados
        pilares_nao_dim = {l.pilar for l in resumo.lances_nao_dimensionados}
        self.assertTrue("P66" in pilares_nao_dim)

        # Verifica identificacao de hiper-armados e superdimensionados
        self.assertGreaterEqual(resumo.total_hiper_armados, 5)
        self.assertGreaterEqual(resumo.total_superdimensionados, 20)
        self.assertGreater(resumo.economia_potencial_aco_kg, 100.0)
        self.assertGreater(resumo.economia_potencial_concreto_m3, 5.0)

    def test_filtro_pilar_individual(self):
        """Testa a analise filtrada para um unico pilar (P8)."""
        resumo = self.analyzer.analisar(pilar_filtro="P8")
        self.assertEqual(resumo.total_pilares, 1)
        self.assertEqual(resumo.total_lances, 2)
        self.assertEqual(resumo.total_calculados, 2)
        self.assertTrue(all(l.pilar == "P8" for l in resumo.todos_pilares["P8"].lances))

    def test_exportacao_dict_e_resumo_executivo(self):
        """Testa a geracao do dicionario serializavel e do texto executivo."""
        resumo = self.analyzer.analisar(pilar_filtro="P4")
        d = resumo.para_dict()
        self.assertIn("edificio_nome", d)
        self.assertIn("metricas", d)
        self.assertEqual(d["metricas"]["calculados"], 2)

        texto = resumo.para_resumo_executivo()
        self.assertIn("RELATORIO EXECUTIVO DE PILARES", texto)
        self.assertIn("P4", texto)

        terminal = resumo.para_tabela_terminal()
        self.assertIn("DIAGNOSTICO E OTIMIZACAO DE PILARES TQS", terminal)

    def test_skill_otimizacao_pilares(self):
        """Testa a execucao e validacao da OtimizacaoPilaresSkill."""
        skill = OtimizacaoPilaresSkill()
        self.assertEqual(skill.nome, "analisar_pilares_edificio")

        res = skill.executar(edificio_nome=self.edificio, formato="resumo")
        self.assertEqual(res["status"], "sucesso")
        self.assertTrue(skill.validar(res))
        self.assertIn("resumo_executivo", res)
        self.assertIn("metricas", res)

    def test_tools_registry_integration(self):
        """Testa a integracao da ferramenta no catálogo de Function Calling do Agente."""
        registry = ToolsRegistry()
        catalogo = registry.listar_ferramentas_para_llm()
        nomes = [f["function"]["name"] for f in catalogo]
        self.assertIn("analisar_pilares_edificio", nomes)

        res = registry.executar_ferramenta("analisar_pilares_edificio", {"edificio_nome": self.edificio})
        self.assertEqual(res["status"], "sucesso")
        self.assertEqual(res["metricas"]["total_pilares"], 69)

if __name__ == "__main__":
    unittest.main()
