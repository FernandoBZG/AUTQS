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

            # Valida que todos os textos de vãos (239) e lajes (10, 13) estão estritamente no edifício
            # e que o contorno das lajes externas (Nível 237) está desenhado ao redor do edifício
            from TQS import TQSDwg
            dwg = TQSDwg.Dwg(pedmv=0)
            dwg.file.Open(saida_teste)
            it = dwg.iterator
            it.Begin()
            linhas_237 = 0
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    lvl = it.level
                    if it.elementName == "Texto":
                        if lvl in [10, 13, 239]:
                            self.assertGreaterEqual(it.x1, -1200.0, f"Texto nível {lvl} com X={it.x1} fora do edifício!")
                            self.assertLessEqual(it.x1, 2300.0, f"Texto nível {lvl} com X={it.x1} fora do edifício!")
                            self.assertGreaterEqual(it.y1, -1600.0, f"Texto nível {lvl} com Y={it.y1} fora do edifício!")
                            self.assertLessEqual(it.y1, 100.0, f"Texto nível {lvl} com Y={it.y1} fora do edifício!")
                        self.assertLessEqual(it.x1, 5000.0, f"Texto disperso em X={it.x1}!")
                    elif lvl == 237 and it.elementName in ["Linha", "Polyline"]:
                        linhas_237 += 1
                        self.assertGreaterEqual(it.x1, -1200.0, f"Linha 237 com X={it.x1} fora do edifício!")
                        self.assertLessEqual(it.x1, 2300.0, f"Linha 237 com X={it.x1} fora do edifício!")
                if not it.Next():
                    break
            dwg.file.Close()

            # Assegura que todas as lajes externas estão desenhadas (não apenas uma linha isolada à direita)
            self.assertGreaterEqual(linhas_237, 100, f"Contorno de lajes externas incompleto: {linhas_237} linhas!")

        finally:
            if os.path.exists(saida_teste):
                try:
                    os.remove(saida_teste)
                except Exception:
                    pass

if __name__ == "__main__":
    unittest.main()
