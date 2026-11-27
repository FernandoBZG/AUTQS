"""
Testes dos módulos comuns do grupo 5 (pavimentos, roteador, moldura) e de parsers com
arquivos de exemplo em pasta temporária. Não dependem de C:\\TQS.
"""
import os
import shutil
import tempfile
import unittest

from src.agent.roteador import intencoes
from src.drawing import moldura
from src.skills.case_10_quantitativo_materiais.material_quantifier import TQSMaterialQuantifier
from src.tqs_adapter.pavimentos import filtrar_pavimentos, listar_pastas_pavimento


class TestPavimentos(unittest.TestCase):
    ITENS = [(n, n) for n in ["2 PAVIMENTO", "12 PAVIMENTO", "PISO DO PAVIMENTO TÉRREO", "TIPO A", "COBERTURA", "1 SUBSOLO"]]

    def _nomes(self, filtro):
        return [n for n, _ in filtrar_pavimentos(self.ITENS, filtro)]

    def test_numero_nao_casa_por_substring(self):
        self.assertEqual(self._nomes("2"), ["2 PAVIMENTO"])
        self.assertEqual(self._nomes("12"), ["12 PAVIMENTO"])
        self.assertEqual(self._nomes("2 pavimento"), ["2 PAVIMENTO"])

    def test_acentos_e_prefixos(self):
        self.assertEqual(self._nomes("no térreo"), ["PISO DO PAVIMENTO TÉRREO"])
        self.assertEqual(self._nomes("terreo"), ["PISO DO PAVIMENTO TÉRREO"])

    def test_sem_correspondencia_nao_vira_todos(self):
        self.assertEqual(self._nomes("xyz"), [])
        self.assertEqual(len(self._nomes("todos")), len(self.ITENS))
        self.assertEqual(len(self._nomes(None)), len(self.ITENS))

    def test_pastas_tecnicas_ignoradas_sem_diferenciar_maiusculas(self):
        tmp = tempfile.mkdtemp(prefix="autqs_pav_")
        try:
            for d in ["ESPACIAL", "Alvest", "backup_claude", "TERREO", "TERREO_BKP_20260101", "FUNDAÇÃO"]:
                os.makedirs(os.path.join(tmp, d))
            self.assertEqual([n for n, _ in listar_pastas_pavimento(tmp)], ["FUNDAÇÃO", "TERREO"])
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestRoteador(unittest.TestCase):
    def test_carga_sozinha_nao_gera_planta(self):
        self.assertNotIn("planta_cargas", intencoes("carga no pilar P1"))
        self.assertIn("planta_cargas", intencoes("gere a planta de cargas"))
        self.assertIn("planta_cargas", intencoes("1500, -300"))

    def test_forma_sozinha_nao_gera_alvenaria(self):
        self.assertNotIn("formas_alvenaria", intencoes("forma do pavimento"))
        self.assertIn("formas_alvenaria", intencoes("gerar planta de formas de alvenaria do tipo A"))

    def test_memorial_nao_dispara_processamento(self):
        r = intencoes("rodar o memorial de cálculo do edifício")
        self.assertIn("memorial", r)
        self.assertNotIn("processamento", r)

    def test_verificar_nao_e_listagem(self):
        self.assertNotIn("listar_pavimentos", intencoes("verificar consistência da planta de formas"))
        self.assertNotIn("listar_elementos", intencoes("verificar as vigas do terreo"))
        self.assertIn("listar_elementos", intencoes("liste as vigas do terreo"))

    def test_rotas_de_analise(self):
        self.assertIn("vigas", intencoes("analise as vigas do terreo"))
        self.assertIn("estabilidade", intencoes("verificar estabilidade global e gamaz no edificio 054"))
        self.assertIn("lajes", intencoes("auditar lajes e grelha no pavimento 2"))
        self.assertIn("materiais", intencoes("extrair quantitativo de materiais do edificio 054"))


class _DrawFalso:
    def __init__(self):
        self.linhas = []
        self.textos = []

    def Line(self, *a):
        self.linhas.append(a)

    def Text(self, *a):
        self.textos.append(a)


class _DwgFalso:
    def __init__(self):
        self.draw = _DrawFalso()


class TestMoldura(unittest.TestCase):
    def test_menor_formato_que_cabe(self):
        sel = moldura.selecionar_formato((0, 3000, 0, 2000), 50, folga_cm=4.0)
        self.assertEqual(sel[0], "95-50")
        self.assertIsNone(moldura.selecionar_formato((0, 20000, 0, 9000), 50, folga_cm=4.0))

    def test_linha_do_selo_desde_a_borda_ou_da_margem(self):
        for desde_borda, y_esperado in [(True, 0.0), (False, moldura.MARGEM_CM * 50)]:
            dwg = _DwgFalso()
            moldura.desenhar_moldura(dwg, "A1", 84.1, 59.4, 50, selo_desde_borda=desde_borda)
            sx0 = (84.1 - moldura.MARGEM_CM - moldura.SELO_LARGURA_CM) * 50
            verticais_selo = [l for l in dwg.draw.linhas if abs(l[0] - sx0) < 1e-6 and abs(l[2] - sx0) < 1e-6]
            self.assertEqual(len(verticais_selo), 1)
            self.assertAlmostEqual(verticais_selo[0][1], y_esperado)
            self.assertEqual(dwg.draw.textos[-1][-1], "A1")


RESEST3 = (
    "\r\nResumo de materiais\t\r\n"
    "Bitola\t3.8\t4.2\t5\t6.3\t8\t10\t12.5\t16\t20\t25\t32\t40\tAço\tConcreto\tForma\tÁrea\t\r\n"
    "\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tkgf\tm3\tm2\tm2\t\r\n"
    "Piso 1: PISO DO 2^PAVIMENTO\t\t\t\t\t\t\t\t\t\t\t\t\t\t212.60\t1532.19\t573.56\t\r\n"
    "Piso 0: PISO DO PAVIMENTO TÉRREO\t\t\t\t\t\t\t\t\t\t\t\t\t\t30.74\t385.97\t61.49\t\r\n"
    "Totais\t\t\t\t\t\t\t\t\t\t\t\t\t\t243.34\t1918.16\t635.05\t\r\n"
)
RESEST8_SEM_TOTAL = (
    "Carbono incorporado na estrutura\t\r\n"
    "Pisos\tInsumo\tTipo\tVolume\tPeso\tCarbono\t\r\n"
    "Piso 1: PISO DO 2^PAVIMENTO\tConcreto\tC40\t212.60\t531494.58\t95669.02\t\r\n"
    "Piso 0: PISO DO PAVIMENTO TÉRREO\tConcreto\tC40\t30.74\t76859.86\t13834.78\t\r\n"
)


class TestCarbonoCase10(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="autqs_resest_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _quantificar(self, resest8):
        with open(os.path.join(self.tmp, "RESEST3.TXT"), "w", encoding="latin1", newline="") as f:
            f.write(RESEST3)
        with open(os.path.join(self.tmp, "RESEST8.TXT"), "w", encoding="latin1", newline="") as f:
            f.write(resest8)
        q = TQSMaterialQuantifier.__new__(TQSMaterialQuantifier)
        q.caminho_edificio = self.tmp
        q.nome_edificio = "TESTE"
        q.pasta_espacial = self.tmp
        return q.quantificar()

    def test_sem_total_geral_soma_todos_os_pisos(self):
        r = self._quantificar(RESEST8_SEM_TOTAL)
        self.assertAlmostEqual(r.carbono_total_kgco2, 95669.02 + 13834.78, places=2)

    def test_total_geral_prevalece(self):
        r = self._quantificar(RESEST8_SEM_TOTAL + "Total geral\t\t\t\t\t109503.80\t\r\n")
        self.assertAlmostEqual(r.carbono_total_kgco2, 109503.80, places=2)


if __name__ == "__main__":
    unittest.main()
