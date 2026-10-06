import os
import unittest
from src.skills.case_05_consistencia_planta.skill import ConsistenciaPlantaSkill
from src.skills.case_05_consistencia_planta.consistency_analyzer import (
    TQSConsistencyAnalyzer,
    InconsistenciaItem,
    ConsistenciaPavimentoResultado,
)
from src.agent.tools import ToolsRegistry


class TestConsistenciaPlanta(unittest.TestCase):
    def setUp(self):
        self.skill = ConsistenciaPlantaSkill()

    def test_skill_metadata(self):
        self.assertEqual(self.skill.nome, "verificar_consistencia_planta")
        self.assertIn("consistência", self.skill.descricao.lower())
        self.assertIn("tqs", self.skill.descricao.lower())
        self.assertIn("menavi", self.skill.descricao.lower())

    def test_interpretar_linhas_menavi(self):
        analyzer = TQSConsistencyAnalyzer("054")

        # 1. Viga sem apoio (Crítico)
        it1 = analyzer._interpretar_linha_menavi("***167 AVISO: Viga V 21 sem apoios, não transferida p/o TQS Vigas")
        self.assertIsNotNone(it1)
        self.assertEqual(it1.elemento, "Viga 21")
        self.assertEqual(it1.tipo, "sem_apoio")
        self.assertEqual(it1.severidade, "CRITICO")
        self.assertIn("mecanismo", it1.sugestao)

        # 2. Apoio nulo
        it2 = analyzer._interpretar_linha_menavi("***001 AVISO: Viga 4 com apoio final nulo no vão 1")
        self.assertIsNotNone(it2)
        self.assertEqual(it2.elemento, "Viga 4")
        self.assertEqual(it2.tipo, "apoio_nulo")
        self.assertEqual(it2.severidade, "IMPORTANTE")

        # 3. Nó fora do pilar
        it3 = analyzer._interpretar_linha_menavi("***111 AVISO: Nó 101 na viga 1 não cai sobre o pilar P 3 Seção 1")
        self.assertIsNotNone(it3)
        self.assertEqual(it3.elemento, "Viga 1")
        self.assertEqual(it3.tipo, "fora_do_pilar")
        self.assertEqual(it3.severidade, "IMPORTANTE")
        self.assertIn("P3", it3.sugestao)

        # 4. Barra em balanço
        it4 = analyzer._interpretar_linha_menavi("***020 AVISO: Barra 44 em balanço, viga V 5 trecho 1")
        self.assertIsNotNone(it4)
        self.assertEqual(it4.elemento, "Viga 5")
        self.assertEqual(it4.tipo, "balanco")
        self.assertEqual(it4.severidade, "IMPORTANTE")

        # 5. Interferência entre apoios
        it5 = analyzer._interpretar_linha_menavi("***052 AVISO: Viga 4 tem interferência entre apoios nos nós, 7 8")
        self.assertIsNotNone(it5)
        self.assertEqual(it5.elemento, "Viga 4")
        self.assertEqual(it5.tipo, "interferencia")
        self.assertEqual(it5.severidade, "IMPORTANTE")

        # 6. Alerta normativo NBR 6118
        it6 = analyzer._interpretar_linha_menavi("***040 AVISO: Viga V 1 vão 1 tem largura 25 menor que 40 definida no item 15.10 da NBR-6118")
        self.assertIsNotNone(it6)
        self.assertEqual(it6.elemento, "Viga 1")
        self.assertEqual(it6.tipo, "normativo")
        self.assertEqual(it6.severidade, "NORMATIVO")

    def test_guardrail_validacao(self):
        # Caso com erros críticos (deve reprovar)
        res_invalido = {
            "status": "inconsistente",
            "metricas": {"erros_criticos": 2}
        }
        self.assertFalse(self.skill.validar(res_invalido))

        # Caso consistente com avisos importantes (deve passar guardrail)
        res_com_avisos = {
            "status": "com_avisos",
            "metricas": {"erros_criticos": 0, "avisos_importantes": 5}
        }
        self.assertTrue(self.skill.validar(res_com_avisos))

        # Caso perfeito (consistente)
        res_ok = {
            "status": "consistente",
            "metricas": {"erros_criticos": 0}
        }
        self.assertTrue(self.skill.validar(res_ok))

    def test_execucao_leitura_existente_054(self):
        pasta_ed = r"C:\TQS\Flexinc - [054] Visconde do Herval CA"
        if not os.path.exists(pasta_ed):
            self.skipTest("Edifício 054 não disponível neste ambiente.")

        res = self.skill.executar(
            edificio_nome="054",
            pavimento="terreo",
            executar_tqs=False,
            formato="terminal"
        )

        self.assertIn(res["status"], ["consistente", "com_avisos", "inconsistente"])
        self.assertIn("edificio", res)
        self.assertIn("metricas", res)
        self.assertGreater(res["metricas"]["total_pavimentos"], 0)
        self.assertIn("resumo_executivo", res)

    def test_tools_registry_integration(self):
        registry = ToolsRegistry()
        ferramentas = registry.listar_ferramentas_para_llm()
        nomes = [f["function"]["name"] for f in ferramentas]
        self.assertIn("verificar_consistencia_planta", nomes)

        # Executa através do registro
        res = registry.executar_ferramenta("verificar_consistencia_planta", {
            "edificio_nome": "054",
            "pavimento": "terreo",
            "executar_tqs": False,
            "formato": "resumo"
        })
        self.assertIn(res["status"], ["consistente", "com_avisos", "inconsistente"])


if __name__ == "__main__":
    unittest.main()
