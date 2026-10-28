import unittest
import os
from src.skills.case_09_auditoria_lajes.slab_analyzer import (
    TQSSlabAnalyzer,
    EdificioLajesResultado,
)
from src.skills.case_09_auditoria_lajes.skill import AuditoriaLajesSkill


class TestAuditoriaLajes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.edificio = "054"
        cls.analyzer = TQSSlabAnalyzer(cls.edificio)

    def test_analise_lajes_edificio_054(self):
        """Testa a extração e consolidação de lajes do edifício 054."""
        res = self.analyzer.analisar()
        self.assertIsInstance(res, EdificioLajesResultado)
        self.assertGreater(res.total_lajes_edificio, 30)
        self.assertGreater(res.area_total_edificio_m2, 100.0)
        self.assertGreater(res.volume_total_edificio_m3, 10.0)

        # Verifica pavimento PISO DO 2^PAVIMENTO
        pav_2 = next((p for nome, p in res.pavimentos.items() if "2" in nome), None)
        self.assertIsNotNone(pav_2)
        self.assertIn("L1", pav_2.lajes)
        self.assertGreater(pav_2.lajes["L1"].area_m2, 5.0)

        # Avisos de grelha / balanços
        self.assertTrue(len(pav_2.balancos_detectados) > 0 or len(pav_2.alertas_grelha) > 0)

        # Serialização e relatório executivo
        d = res.para_dict()
        self.assertIn("total_lajes_edificio", d)
        self.assertIn("pavimentos", d)

        resumo = res.para_resumo_executivo()
        self.assertIn("AUDITORIA DE LAJES, GRELHA E FLECHAS", resumo)
        self.assertIn("Resumo por Pavimento", resumo)

    def test_filtro_pavimento_especifico(self):
        """Testa o filtro por pavimento específico."""
        res = self.analyzer.analisar(pavimento_filtro="2")
        self.assertEqual(len(res.pavimentos), 1)
        nome_pav = list(res.pavimentos.keys())[0]
        self.assertIn("2", nome_pav)

    def test_skill_auditoria_lajes(self):
        """Testa a execução via AuditoriaLajesSkill."""
        skill = AuditoriaLajesSkill()
        self.assertEqual(skill.nome, "auditar_lajes_edificio")

        ret = skill.executar(edificio_nome=self.edificio, pavimento="2")
        self.assertEqual(ret["status"], "sucesso")
        self.assertTrue(skill.validar(ret))
        self.assertGreater(ret["total_lajes"], 30)
        self.assertIn("resumo_executivo", ret)


if __name__ == "__main__":
    unittest.main()
