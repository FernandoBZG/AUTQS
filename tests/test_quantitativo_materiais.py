import unittest
import os
from src.skills.case_10_quantitativo_materiais.material_quantifier import (
    TQSMaterialQuantifier,
    EdificioMateriaisResultado,
)
from src.skills.case_10_quantitativo_materiais.skill import QuantitativoMateriaisSkill


class TestQuantitativoMateriais(unittest.TestCase):
    def test_quantitativo_edificio_054(self):
        """Testa a extração dos quantitativos de materiais do edifício 054."""
        quantifier = TQSMaterialQuantifier("054")
        res = quantifier.quantificar()

        self.assertIsInstance(res, EdificioMateriaisResultado)
        self.assertGreater(res.volume_concreto_total_m3, 200.0)
        self.assertGreater(res.area_formas_total_m2, 1000.0)
        self.assertGreater(res.area_total_m2, 500.0)
        self.assertGreater(res.carbono_total_kgco2, 10000.0)
        self.assertGreater(res.espessura_media_m, 0.10)
        self.assertGreater(res.taxa_formas_m2_m2, 1.0)

        # Pisos
        self.assertGreaterEqual(len(res.pisos), 2)
        piso1 = res.pisos[0]
        self.assertGreater(piso1.volume_concreto_m3, 50.0)

        # Dicionário e Resumo Executivo
        d = res.para_dict()
        self.assertIn("totais", d)
        self.assertIn("indices_consumo", d)

        resumo = res.para_resumo_executivo()
        self.assertIn("QUANTITATIVO GLOBAL E ÍNDICES DE CONSUMO", resumo)
        self.assertIn("Volume Total de Concreto", resumo)

    def test_skill_quantitativo_materiais(self):
        """Testa a execução via QuantitativoMateriaisSkill."""
        skill = QuantitativoMateriaisSkill()
        self.assertEqual(skill.nome, "extrair_quantitativo_materiais")

        ret = skill.executar(edificio_nome="054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertTrue(skill.validar(ret))
        self.assertGreater(ret["volume_concreto_total_m3"], 200.0)
        self.assertIn("resumo_executivo", ret)


if __name__ == "__main__":
    unittest.main()
