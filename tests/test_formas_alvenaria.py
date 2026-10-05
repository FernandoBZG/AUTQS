import os
import unittest
from src.skills.case_03_formas_alvenaria.skill import FormasAlvenariaSkill
from src.drawing.alvenaria_dwg_builder import AlvenariaDwgBuilder

class TestFormasAlvenaria(unittest.TestCase):
    def test_formas_alvenaria_skill_metadata(self):
        skill = FormasAlvenariaSkill()
        self.assertEqual(skill.nome, "gerar_planta_formas_alvenaria")
        self.assertIn("alvenaria estrutural", skill.descricao.lower())
        self.assertIn("desfiad1", skill.descricao.lower())

    def test_formas_alvenaria_executar_054(self):
        skill = FormasAlvenariaSkill()
        pasta_ed = r"C:\TQS\Flexinc - [054] Visconde do Herval AE"
        if not os.path.exists(pasta_ed):
            self.skipTest("Edifício 054 não disponível neste ambiente.")

        saida_teste = os.path.join(pasta_ed, "TIPO A", "PRE_FOR_1aFIADA_TEST_UNIT.DWG")
        try:
            resultado = skill.executar(
                edificio_nome="054",
                pavimento="TIPO A",
                caminho_saida_dwg=saida_teste,
                escala=50,
            )

            self.assertEqual(resultado["status"], "sucesso")
            self.assertTrue(resultado["sucesso"])
            self.assertTrue(os.path.exists(saida_teste))
            self.assertGreater(os.path.getsize(saida_teste), 10000)

            # Valida lajes e vãos
            self.assertGreaterEqual(resultado["total_lajes"], 20)
            self.assertGreaterEqual(resultado["total_vaos"], 40)

            # Valida auditoria DWG
            aud = resultado["auditoria"]
            self.assertEqual(aud["escala"], 50.0)
            self.assertGreater(aud["total_textos"], 300)
            niveis = aud["niveis_utilizados"]
            for lvl in [10, 13, 222, 230, 239, 247]:
                self.assertIn(lvl, niveis)

        finally:
            if os.path.exists(saida_teste):
                try:
                    os.remove(saida_teste)
                except Exception:
                    pass

if __name__ == "__main__":
    unittest.main()
