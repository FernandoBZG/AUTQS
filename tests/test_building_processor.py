import os
import tempfile
import time
import unittest
from types import SimpleNamespace
from unittest import mock

from src.tqs_adapter import building_processor as bp


def _gravar(caminho: str, conteudo: str = "x", idade_s: float = 0.0) -> None:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="latin-1") as f:
        f.write(conteudo)
    if idade_s:
        t = time.time() - idade_s
        os.utime(caminho, (t, t))


class TestDeteccaoErrosTQS(unittest.TestCase):
    def test_extrai_tarefas_do_log(self):
        log = (
            " Dimensionando pilar: P44\n"
            "-CMD: Erro executando [PORLID]\n"
            "Erro executando [GERENCIADOR.DAT]\n"
        )
        self.assertEqual(bp.extrair_erros_tqs(log, None), ["PORLID", "GERENCIADOR.DAT"])

    def test_sem_erros(self):
        self.assertEqual(bp.extrair_erros_tqs("Todas as vigas foram gravadas", ""), [])


class TestVerificacaoArtefatos(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ed = self.tmp.name
        self.inicio = time.time()

    def tearDown(self):
        self.tmp.cleanup()

    def test_artefato_antigo_nao_confirma_tarefa(self):
        _gravar(os.path.join(self.ed, "ESPACIAL", "PORLID.DWG"), idade_s=3600)
        _gravar(os.path.join(self.ed, "ESPACIAL", "CARDWG2.LST"))
        falhas = bp.verificar_artefatos(
            self.ed,
            {"PROC (pórtico espacial)": [r"ESPACIAL\CARDWG2.LST"], "PORLID": [r"ESPACIAL\PORLID.DWG"]},
            self.inicio,
        )
        self.assertEqual(falhas, ["PORLID"])

    def test_qualquer_arquivo_da_lista_confirma(self):
        _gravar(os.path.join(self.ed, "ESPACIAL", "RESEST2.TXT"))
        falhas = bp.verificar_artefatos(
            self.ed, {"RESEST": [r"ESPACIAL\RESEST1.TXT", r"ESPACIAL\RESEST2.TXT"]}, self.inicio
        )
        self.assertEqual(falhas, [])

    def test_relger_vazio_em_pavimento_processado(self):
        # ROOFTOP: vigas processadas (ORDCON novo) mas RELGER vazio -> falha
        _gravar(os.path.join(self.ed, "ROOFTOP", "VIGAS", "ORDCON.LST"))
        _gravar(os.path.join(self.ed, "ROOFTOP", "VIGAS", "RELGER.LST"), conteudo="")
        # COBERTURA: dimensionado normalmente
        _gravar(os.path.join(self.ed, "COBERTURA", "VIGAS", "ORDCON.LST"))
        _gravar(os.path.join(self.ed, "COBERTURA", "VIGAS", "RELGER.LST"), conteudo="Viga= 1 V1")
        # ANTIGO: vigas não processadas nesta execução -> ignorado
        _gravar(os.path.join(self.ed, "ANTIGO", "VIGAS", "ORDCON.LST"), idade_s=3600)
        _gravar(os.path.join(self.ed, "ANTIGO", "VIGAS", "RELGER.LST"), conteudo="", idade_s=3600)

        self.assertEqual(bp.verificar_vigas_dimensionadas(self.ed, self.inicio), ["ROOFTOP"])


class TestExecutarBatch(unittest.TestCase):
    """Simula o TQS.EXE retornando código 0 com falha no PORLID (caso real do edifício 055)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.ed = self.tmp.name
        self.proc = bp.TQSBuildingProcessor.__new__(bp.TQSBuildingProcessor)
        self.proc.tqs_exe = "TQS.EXE"
        self.proc.caminho_edificio = self.ed
        self.proc.nome_edificio = "TESTE"
        self.proc.pasta_raiz = os.path.dirname(self.ed)
        _gravar(os.path.join(self.ed, "ESPACIAL", "PORLID.DWG"), idade_s=3600)

    def tearDown(self):
        self.tmp.cleanup()

    def _rodar(self, stdout: str):
        def fake_run(*args, **kwargs):
            # O "TQS" grava as saídas do PROC, mas não as do PORLID/RESEST
            _gravar(os.path.join(self.ed, "ESPACIAL", "CARDWG2.LST"))
            _gravar(os.path.join(self.ed, "ESPACIAL", "PORLIS2.LST"))
            _gravar(os.path.join(self.ed, "PILAR", "SELEC.LST"))
            _gravar(os.path.join(self.ed, "ROOFTOP", "VIGAS", "ORDCON.LST"))
            _gravar(os.path.join(self.ed, "ROOFTOP", "VIGAS", "RELGER.LST"), conteudo="")
            return SimpleNamespace(returncode=0, stdout=stdout, stderr="")

        cwd = os.getcwd()
        os.chdir(self.ed)
        try:
            with mock.patch.object(bp.subprocess, "run", side_effect=fake_run):
                return self.proc._executar_batch(
                    ["PROC", "PORLID", "RESEST"],
                    timeout_segundos=10,
                    descricao="teste",
                    artefatos_esperados={
                        "PROC (pórtico espacial)": [r"ESPACIAL\CARDWG2.LST"],
                        "PROC (dimensionamento de pilares)": [r"PILAR\SELEC.LST"],
                        "PORLID": [r"ESPACIAL\PORLID.DWG"],
                        "RESEST": [r"ESPACIAL\RESEST2.TXT"],
                    },
                    verificar_vigas=True,
                )
        finally:
            os.chdir(cwd)

    def test_falha_com_codigo_zero_nao_e_sucesso(self):
        res = self._rodar(stdout="-CMD: Erro executando [PORLID]\nErro executando [GERENCIADOR.DAT]\n")
        self.assertFalse(res["sucesso"])
        self.assertEqual(res["status"], "erro")
        self.assertIn("PORLID (reportado pelo TQS)", res["tarefas_com_falha"])
        self.assertIn("RESEST (saída não gravada)", res["tarefas_com_falha"])
        # PORLID não deve aparecer duas vezes (log + artefato)
        self.assertEqual(sum("PORLID" in t for t in res["tarefas_com_falha"]), 1)
        self.assertEqual(res["pavimentos_sem_vigas_dimensionadas"], ["ROOFTOP"])
        self.assertIn("PORLID", res["erro"])

    def test_falha_detectada_sem_log(self):
        # stdout vazio (caso real: o log fica só na janela do TQS)
        res = self._rodar(stdout="")
        self.assertFalse(res["sucesso"])
        self.assertIn("PORLID (saída não gravada)", res["tarefas_com_falha"])
        self.assertTrue(res["tem_cardwg"] and res["tem_porlis"])


if __name__ == "__main__":
    unittest.main()
