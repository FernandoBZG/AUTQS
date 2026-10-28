import unittest
import os
from src.skills.case_08_estabilidade_global.stability_analyzer import (
    TQSStabilityAnalyzer,
    RelatorioEstabilidadeResultado,
)
from src.skills.case_08_estabilidade_global.skill import EstabilidadeGlobalSkill
from src.agent.tools import ToolsRegistry


class TestEstabilidadeGlobal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edificio = "054"
        cls.analyzer = TQSStabilityAnalyzer(cls.edificio)

    def test_analise_estabilidade_edificio_054(self):
        """Testa a extração dos parâmetros de estabilidade do edifício 054."""
        res = self.analyzer.analisar()
        self.assertIsInstance(res, RelatorioEstabilidadeResultado)
        self.assertEqual(res.altura_edificio_m, 3.50)
        self.assertEqual(res.cota_inicial_m, 6.90)
        self.assertEqual(res.cota_final_m, 10.40)
        
        # Gama Z e FAVt
        self.assertGreater(res.gama_z_max, 1.0)
        self.assertLess(res.gama_z_max, 1.5)
        self.assertIn(res.classificacao_estrutura, ["NÓS FIXOS", "NÓS MÓVEIS", "CRÍTICO - INSTABILIDADE EXCESSIVA"])
        
        # Deslocamentos ELS
        self.assertTrue(len(res.deslocamentos_topo) > 0)
        self.assertTrue(len(res.deslocamentos_interpiso) > 0)
        self.assertGreater(res.drift_topo_max_cm, 0.0)
        self.assertGreater(res.drift_interpiso_max_cm, 0.0)

        # Dicionário e resumo
        d = res.para_dict()
        self.assertIn("gama_z_max", d)
        self.assertIn("drift_topo", d)
        self.assertIn("drift_interpiso", d)

        resumo = res.para_resumo_executivo()
        self.assertIn("AUDITORIA DE ESTABILIDADE GLOBAL", resumo)
        self.assertIn("Topo do Edifício", resumo)

    def test_skill_execucao(self):
        """Testa o comportamento da EstabilidadeGlobalSkill."""
        skill = EstabilidadeGlobalSkill()
        self.assertEqual(skill.nome, "auditar_estabilidade_global")
        
        ret = skill.executar(edificio_nome=self.edificio)
        self.assertEqual(ret["status"], "sucesso")
        self.assertTrue(skill.validar(ret))
        self.assertIn("resumo_executivo", ret)
        self.assertIn("gama_z_max", ret)


if __name__ == "__main__":
    unittest.main()
