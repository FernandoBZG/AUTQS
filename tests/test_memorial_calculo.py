import unittest
import os
import tempfile
from src.skills.case_11_memorial_calculo.memorial_generator import TQSMemorialGenerator
from src.skills.case_11_memorial_calculo.skill import MemorialCalculoSkill


class TestMemorialCalculo(unittest.TestCase):
    def test_geracao_memorial_edificio_054(self):
        """Testa a geração consolidada do memorial em markdown e html para o edifício 054."""
        gerador = TQSMemorialGenerator("054")
        with tempfile.TemporaryDirectory() as tmpdir:
            p_md = os.path.join(tmpdir, "memorial.md")
            p_html = os.path.join(tmpdir, "memorial.html")

            ret = gerador.gerar(caminho_saida_md=p_md, caminho_saida_html=p_html)

            self.assertIn("054", ret["edificio_nome"])
            self.assertTrue(os.path.exists(p_md))
            self.assertTrue(os.path.exists(p_html))

            md = ret["conteudo_markdown"]
            self.assertIn("MEMORIAL DESCRITIVO E JUSTIFICATIVO DE CÁLCULO ESTRUTURAL", md)
            self.assertIn("ABNT NBR 6118:2023", md)
            self.assertIn("Análise de Estabilidade Global", md)
            self.assertIn("Quantitativos de Materiais", md)

            html = ret["conteudo_html"]
            self.assertIn("<!DOCTYPE html>", html)
            self.assertIn("Memorial Descritivo", html)

    def test_skill_memorial_calculo(self):
        """Testa a execução via MemorialCalculoSkill."""
        skill = MemorialCalculoSkill()
        self.assertEqual(skill.nome, "gerar_memorial_descritivo")

        ret = skill.executar(edificio_nome="054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertTrue(skill.validar(ret))
        self.assertIn("resumo_executivo", ret)


if __name__ == "__main__":
    unittest.main()
