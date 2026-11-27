"""
Testes das correções de engenharia (grupo 3) com arquivos de exemplo em pasta
temporária: não dependem de um edifício real em C:\\TQS.
"""
import os
import shutil
import tempfile
import unittest

from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill
from src.skills.case_04_otimizacao_pilares.pilar_analyzer import (
    COMPRIMENTO_LANCE_PADRAO_M, LanceAnalise, TQSColumnAnalyzer,
)
from src.skills.case_08_estabilidade_global.stability_analyzer import TQSStabilityAnalyzer
from src.skills.case_15_revisao_plantas import diff_emissao as de


INICIA_LST = """\
 PILAR :P1                                                                      num.  1
 ------------------------------------------------------------------------------------
 LANC  B[cm]  H[cm] dx[cm] dy[cm]   ANG SECAO     JX[m4] DFSP[cm]  PD[m] HVx[cm]
  L 1  19.00  30.00   0.00   0.00 90.00  RETG  0.000427   -15.000  3.500   50.00  -15.00     2.95
  L 2  19.00  30.00   0.00   0.00 90.00  RETG  0.000427     0.000  2.800   50.00    0.00    28.80
 PILAR :P2                                                                      num.  2
  L 1  19.00  45.00   0.00   0.00 90.00  RETG  0.001443     0.000  3.600   50.00    0.00     5.56
"""

PORALF_TEMPLATE = """\
Parâmetro de estabilidade (GamaZ) para os carregamentos simples de vento
========================================================================
Caso   Ang     CTot       M2     CHor       M1      Mig   GamaZ   Alfa  Obs
   5   90.  17320.9      6.1      0.0      0.0    419.3   {gz}   0.400        {obs}
   6  270.  17320.9      6.1      0.0      0.0    419.3   {gz}   0.400        {obs}

Parâmetro de estabilidade (FAVt ) para combinações de ELU - vigas e lajes
=========================================================================
Caso   Ang     CTot       M2     CHor       M1    MultH   FAVt   Alfa  Obs
  17   90.  17320.9      3.4      0.0      0.0    1.183   1.183 0.400     D

Fim
"""


class TestAlertasPlantaDeCargas(unittest.TestCase):
    def _pilar(self, nome, nk_max, nk_min, sem_reacao=False):
        return {"pilar": nome, "nk_max_tf": nk_max, "nk_min_tf": nk_min, "sem_reacao": sem_reacao}

    def test_tracao_no_caso_fz_min_gera_alerta(self):
        res = {"pilares": [self._pilar("P1", 97.0, -63.0), self._pilar("P2", 50.0, 10.0)]}
        alertas = PlantaDeCargasSkill.verificar_alertas(res)
        self.assertTrue(any("P1" in a and "-63.0" in a for a in alertas))
        self.assertFalse(any("P2" in a for a in alertas))

    def test_sem_fz_min_avisa_que_tracao_nao_foi_verificada(self):
        res = {"pilares": [self._pilar("P1", 97.0, None)]}
        alertas = PlantaDeCargasSkill.verificar_alertas(res)
        self.assertTrue(any("FZ MIN" in a for a in alertas))

    def test_pilar_sem_reacao_nao_vira_zero(self):
        res = {"pilares": [self._pilar("P1", 0.0, None, sem_reacao=True), self._pilar("P2", 40.0, 5.0)]}
        alertas = PlantaDeCargasSkill.verificar_alertas(res)
        self.assertTrue(any("sem reação" in a and "P1" in a for a in alertas))
        self.assertFalse(PlantaDeCargasSkill().validar(res))


class TestPeDireitoLances(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="autqs_pd_")
        with open(os.path.join(self.tmp, "INICIA.LST"), "w", encoding="latin1") as f:
            f.write(INICIA_LST)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_le_pd_de_cada_lance(self):
        an = TQSColumnAnalyzer.__new__(TQSColumnAnalyzer)
        an.pasta_pilar = self.tmp
        pds = an._parse_inicia_lst()
        self.assertEqual(pds, {("P1", 1): 3.5, ("P1", 2): 2.8, ("P2", 1): 3.6})

    def test_comprimento_usa_pd_e_cai_no_padrao_sem_ele(self):
        lance = LanceAnalise(pilar="P1", lance=1, pavimento="T", b_cm=19, h_cm=30, area_cm2=570, status="CALCULADO")
        self.assertEqual(lance.comprimento_m, COMPRIMENTO_LANCE_PADRAO_M)
        lance.pe_direito_m = 3.5
        self.assertEqual(lance.comprimento_m, 3.5)


class TestGamaZSeparadoDeFAVt(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="autqs_gz_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _analisar(self, gz, obs=""):
        with open(os.path.join(self.tmp, "PORALF.LST"), "w", encoding="latin1") as f:
            f.write(PORALF_TEMPLATE.format(gz=gz, obs=obs))
        an = TQSStabilityAnalyzer.__new__(TQSStabilityAnalyzer)
        an.caminho_edificio = self.tmp
        an.nome_edificio = "TESTE"
        an.pasta_espacial = self.tmp
        return an.analisar()

    def test_gama_z_vem_dos_casos_simples(self):
        r = self._analisar("1.090")
        self.assertAlmostEqual(r.gama_z_max, 1.090)
        self.assertAlmostEqual(r.fav_t_max, 1.183)
        self.assertEqual(r.classificacao_estrutura, "NÓS FIXOS")
        self.assertIsNone(r.combinacoes_elu[0].gama_z)

    def test_gama_z_zero_e_tratado_como_nao_calculado(self):
        r = self._analisar("0.000", obs="G")
        self.assertAlmostEqual(r.gama_z_max, 1.183)
        self.assertTrue(any("FAVt" in a for a in r.alertas_normativos))


class TestAreaDoSelo(unittest.TestCase):
    def test_selo_medido_a_partir_da_borda_direita(self):
        # A0 (118,9 cm): mesmo limite de antes (x > 100,3)
        self.assertTrue(de._excluido(110.0, 10.0, 118.9, 84.1))
        self.assertFalse(de._excluido(95.0, 10.0, 118.9, 84.1))
        # A1 (84,1 cm): o selo acompanha a borda direita
        self.assertTrue(de._excluido(75.0, 10.0, 84.1, 59.4))
        self.assertFalse(de._excluido(60.0, 10.0, 84.1, 59.4))


if __name__ == "__main__":
    unittest.main()
