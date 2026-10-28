import unittest
import os
import tempfile
import ezdxf

from src.skills.case_12_limpeza_arquitetura.arch_cleaner import (
    TQSArchCleaner,
    LimpezaArquiteturaResultado,
)
from src.skills.case_12_limpeza_arquitetura.skill import LimpezaArquiteturaSkill


class TestLimpezaArquitetura(unittest.TestCase):
    def setUp(self):
        # Cria arquivo DXF de arquitetura bruta para testes
        self.tmpdir = tempfile.mkdtemp()
        self.arq_bruto = os.path.join(self.tmpdir, "ARQ_PAV_TIPO.dxf")

        doc = ezdxf.new("R2010", setup=True)
        msp = doc.modelspace()

        # Camada de Paredes (deve ser preservada)
        doc.layers.add("ARQ_ALVENARIA", color=1)
        msp.add_line((0, 0), (10, 0), dxfattribs={"layer": "ARQ_ALVENARIA"})
        msp.add_line((10, 0), (10, 15), dxfattribs={"layer": "ARQ_ALVENARIA"})
        msp.add_line((10, 15), (0, 15), dxfattribs={"layer": "ARQ_ALVENARIA"})
        msp.add_line((0, 15), (0, 0), dxfattribs={"layer": "ARQ_ALVENARIA"})

        # Camada de Mobiliário (deve ser purgada)
        doc.layers.add("ARQ_MOBILIARIO", color=2)
        msp.add_line((2, 2), (4, 2), dxfattribs={"layer": "ARQ_MOBILIARIO"})
        msp.add_line((4, 2), (4, 4), dxfattribs={"layer": "ARQ_MOBILIARIO"})

        # Camada de Vegetação (deve ser purgada)
        doc.layers.add("ARQ_PAISAGISMO", color=3)
        msp.add_circle((7, 7), radius=1.0, dxfattribs={"layer": "ARQ_PAISAGISMO"})

        # Hachura (deve ser eliminada)
        doc.layers.add("ARQ_HACHURA", color=8)
        hatch = msp.add_hatch(color=8, dxfattribs={"layer": "ARQ_HACHURA"})
        hatch.paths.add_polyline_path([(0, 0), (2, 0), (2, 2), (0, 2)], is_closed=True)

        doc.saveas(self.arq_bruto)

    def test_limpeza_e_conversao_escala(self):
        """Testa a purga de camadas parasitas e a conversão de escala metros -> cm."""
        cleaner = TQSArchCleaner()
        saida = os.path.join(self.tmpdir, "Geo_PAV_TIPO.dxf")

        res = cleaner.limpar_e_padronizar(
            caminho_entrada=self.arq_bruto,
            caminho_saida=saida,
            fator_escala="auto",
        )

        self.assertIsInstance(res, LimpezaArquiteturaResultado)
        self.assertTrue(os.path.exists(saida))
        self.assertEqual(res.fator_escala_aplicado, 100.0)
        self.assertEqual(res.hachuras_removidas, 1)
        self.assertEqual(res.blocos_parasitas_removidos, 3)  # 2 linhas de mob + 1 circulo veg
        self.assertEqual(res.entidades_mantidas, 4)  # 4 linhas de alvenaria

        # Verifica escala final em cm (0 a 10m virou 0 a 1000cm, 0 a 15m virou 0 a 1500cm)
        self.assertEqual(res.bounds_finais[2], 1000.0)
        self.assertEqual(res.bounds_finais[3], 1500.0)

        # Dicionário e resumo
        d = res.para_dict()
        self.assertIn("bounds_finais_cm", d)
        self.assertEqual(d["bounds_finais_cm"]["largura"], 1000.0)

        resumo = res.para_resumo_executivo()
        self.assertIn("LIMPEZA E PADRONIZAÇÃO DE ARQUITETURA", resumo)
        self.assertIn("Geo_PAV_TIPO.dxf", resumo)

    def test_skill_limpeza_arquitetura(self):
        """Testa a execução via LimpezaArquiteturaSkill."""
        skill = LimpezaArquiteturaSkill()
        self.assertEqual(skill.nome, "padronizar_arquitetura_tqs")

        saida = os.path.join(self.tmpdir, "Geo_TESTE.dxf")
        ret = skill.executar(
            caminho_arquivo=self.arq_bruto,
            caminho_saida=saida,
        )

        self.assertEqual(ret["status"], "sucesso")
        self.assertTrue(skill.validar(ret))
        self.assertTrue(os.path.exists(ret["arquivo_gerado"]))
        self.assertEqual(ret["entidades_mantidas"], 4)


if __name__ == "__main__":
    unittest.main()
