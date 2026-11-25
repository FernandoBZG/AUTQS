import os
import unittest
from src.skills.case_13_geometria_ca.skill import GeometriaCASkill

class TestGeometriaCASkill(unittest.TestCase):
    def test_geometria_ca_skill_metadata(self):
        skill = GeometriaCASkill()
        self.assertEqual(skill.nome, "gerar_geometria_concreto_armado")
        self.assertIn("concreto armado", skill.descricao.lower())
        self.assertIn("geo_", skill.descricao.lower())

    def test_geometria_ca_executar_055_subsolo1(self):
        skill = GeometriaCASkill()
        edificio_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA"
        if not os.path.exists(edificio_dir):
            self.skipTest("Edifício 055 CA não disponível neste ambiente.")

        resultado = skill.executar(
            edificio_nome="055",
            pavimento="PISO DO SUBSOLO 1",
            escala=50
        )

        self.assertEqual(resultado["status"], "sucesso")
        self.assertTrue(resultado["sucesso"])
        self.assertTrue(skill.validar(resultado))

        # Validações de auditoria
        aud = resultado["auditoria"]
        self.assertIn(aud["total_vigas"], [58, 60])
        self.assertGreater(aud["total_elementos"], 4000)
        self.assertEqual(aud["moldura_elementos"], 32)
        self.assertGreater(aud["notas_elementos"], 500)
        self.assertTrue(os.path.exists(resultado["caminho_geo"]))

    def test_geometria_ca_executar_055_terreo(self):
        skill = GeometriaCASkill()
        edificio_dir = r"C:\TQS\Flexinc - [055] Jardim Europa CA"
        if not os.path.exists(edificio_dir):
            self.skipTest("Edifício 055 CA não disponível neste ambiente.")

        resultado = skill.executar(
            edificio_nome="055 CA",
            pavimento="térreo",
            escala=50
        )

        self.assertEqual(resultado["status"], "sucesso")
        self.assertTrue(resultado["sucesso"])
        self.assertTrue(skill.validar(resultado))

        # Validações de auditoria do Térreo (modelo atualizado pelo usuário)
        aud = resultado["auditoria"]
        self.assertIn(aud["total_vigas"], [124, 130])
        self.assertGreater(aud["total_elementos"], 4000)
        self.assertEqual(aud["moldura_elementos"], 32)
        self.assertGreater(aud["notas_elementos"], 500)
        self.assertTrue(os.path.exists(resultado["caminho_geo"]))

if __name__ == "__main__":
    unittest.main()
