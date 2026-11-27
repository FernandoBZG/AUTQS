"""
Testes do Case 15 (emissão de revisões de plantas do Editor de Plantas do TQS).
Usam .CPL / NMCARQ.DAT / TXT sintéticos, no formato observado no TQS V25, em pasta temporária.
"""
import os
import shutil
import tempfile
import time
import unittest
from unittest.mock import patch

from src.skills.case_15_revisao_plantas.cpl import (
    ErroCPL, Revisao, ler_cpl, MAX_CARACTERES_DESCRICAO,
)
from src.skills.case_15_revisao_plantas.nomenclatura import (
    ErroNomenclatura, decompor_id, ler_nmcarq, ler_variaveis_plotagem, nome_fase_esperado, trocar_fase,
)
from src.skills.case_15_revisao_plantas.skill import RevisaoPlantasSkill

ID = "999-EST-PB-0601-TP-1FIA"


def ler_bytes(caminho):
    with open(caminho, "rb") as f:
        return f.read()

NMCARQ = """//------------------------------------------
// Arquivo de Máscaras para Desenhos - TQS
<Pré-Definidos>
 <REVISAO>
   Título=Revisão da Planta
   Prefixo=-R
   NCaract=2
   Sufixo=
 </REVISAO>
</Pré-Definidos>
<Variáveis>
 <Fases>
 NCaract=2
   <EP>
     <Estudo preliminar>
   </EP>
   <PE>
     <Projeto executivo>
   </PE>
   <PB>
     <Projeto Base>
   </PB>
 </Fases>
</Variáveis>
"""

CABECALHO = ("A0-45                  0.    1    1    1                             1    1   118.000    45.000"
             "    3    0   -1    2{atual:5d}{qtd:5d}    0     0.000     0.000     0.000     0.000")


def _mascara(oculto=None):
    bits = ["1"] * 256
    if oculto is not None:
        bits[oculto] = "0"
    s = "".join(bits)
    return [s[:80], s[80:160], s[160:]]


def montar_cpl(revisoes, titulo="PRÉ FOR 1aFIADA Tipo B", id_prancha=ID):
    linhas = [CABECALHO.format(atual=revisoes[-1][0] if revisoes else 0, qtd=len(revisoes)),
              "---V14.0---", "---V14.0---", "", titulo]
    for n, data, autor, desc in revisoes:
        linhas += [f"{n:5d}", data, autor, desc]
    linhas += ["    0", "--EOC--"]
    linhas += [r"..\TIPO A\PRE_FOR_1aFIADA_TIPO A",
               "     50.00         0         0         0      0.00  PRE_FOR_1aFIADA_TIPO A / Fiada",
               "         -1359.70000         -1606.60000             0.00000             0.00000           118.90000"
               "            45.00000   -1   17    0    0    1    0         -1359.70000         -1606.60000"
               "             0.00000             0.00000           118.90000            45.00000",
               "TIPO A"] + _mascara() + ["#"]
    linhas += [rf"..\PLANTAS\{id_prancha}_CR",
               f"      1.00         0         0         0      0.00  {id_prancha}_CR",
               "             0.00000             0.00000             0.00000             0.00000           118.00000"
               "            45.00000   -1    1    0    2    1    0             0.00000             0.00000"
               "             0.00000             0.00000           118.00000            45.00000",
               "INDEFINIDO"] + _mascara(oculto=230) + ["#", "#", ""]
    return "\r\n".join(linhas).encode("cp1252")


REVS = [(0, "06/08/2026", "FERNANDO ZEN", "EMISSÃO INICIAL"),
        (1, "11/09/2026", "FERNANDO ZEN", "MODIFICAÇÕES GERAIS")]


def txt_plotagem(n, desc, data, autor, fase="PROJETO BÁSICO"):
    s = f"{n:02d}"
    linhas = [f"REVISAO,{s}", f"REVISAO_TXT{s},{desc}", f"REVISAO_AUT{s},{autor}",
              f"REVISAO_DAT{'010' if n == 10 else s},{data}", f"_FASE,{fase}"]
    return ("\r\n".join(linhas) + "\r\n").encode("cp1252")


class BaseTemp(unittest.TestCase):
    def setUp(self):
        self.ed = tempfile.mkdtemp(prefix="AUTQS_rev_[999]_")
        self.plantas = os.path.join(self.ed, "PLANTAS")
        os.makedirs(self.plantas)
        os.makedirs(os.path.join(self.ed, "TIPO A"))
        with open(os.path.join(self.ed, "NMCARQ.DAT"), "wb") as f:
            f.write(NMCARQ.replace("\n", "\r\n").encode("cp1252"))
        self.cpl = os.path.join(self.plantas, ID + ".CPL")
        with open(self.cpl, "wb") as f:
            f.write(montar_cpl(REVS))
        self.dwg = os.path.join(self.ed, "TIPO A", "PRE_FOR_1aFIADA_TIPO A.DWG")
        with open(self.dwg, "wb") as f:
            f.write(b"DWG")
        with open(os.path.join(self.plantas, ID + "_CR.DWG"), "wb") as f:
            f.write(b"CR")

    def tearDown(self):
        shutil.rmtree(self.ed, ignore_errors=True)

    def plotar(self, n, desc, data="11/09/2026", autor="FERNANDO ZEN", fase="PROJETO BÁSICO", atraso_dwg=-600):
        base = os.path.join(self.plantas, f"{ID}-R{n:02d}")
        with open(base + ".PDF", "wb") as f:
            f.write(b"%PDF")
        with open(base + ".TXT", "wb") as f:
            f.write(txt_plotagem(n, desc, data, autor, fase))
        agora = time.time()
        os.utime(self.dwg, (agora + atraso_dwg, agora + atraso_dwg))


class TestCPL(BaseTemp):
    def test_ida_e_volta_identica(self):
        pl = ler_cpl(self.cpl)
        self.assertEqual(pl.serializar(), ler_bytes(self.cpl))

    def test_leitura_historico_e_desenhos(self):
        pl = ler_cpl(self.cpl)
        self.assertEqual(pl.titulo, "PRÉ FOR 1aFIADA Tipo B")
        self.assertEqual(pl.revisao_atual, 1)
        self.assertEqual([r.descricao for r in pl.revisoes], ["EMISSÃO INICIAL", "MODIFICAÇÕES GERAIS"])
        self.assertEqual(pl.proximo_numero(), 2)
        desenhos = pl.desenhos()
        self.assertEqual([d.tipo for d in desenhos], [0, 2])
        d = pl.desenhos_conteudo()[0]
        self.assertEqual(d.escala, 50.0)
        self.assertEqual(d.para_folha(-1359.7, -1606.6), (0.0, 0.0))
        x, y = d.para_folha(-1359.7 + 500, -1606.6 + 100)
        self.assertAlmostEqual(x, 10.0)
        self.assertAlmostEqual(y, 2.0)
        self.assertTrue(d.nivel_visivel(230))
        self.assertFalse(desenhos[1].nivel_visivel(230))
        self.assertEqual(d.caminho_absoluto(pl.pasta), os.path.normpath(self.dwg))

    def test_adicionar_revisao_edicao_cirurgica(self):
        pl = ler_cpl(self.cpl)
        cab_antes = pl.linhas[0]
        pl.adicionar_revisao(Revisao(2, "26/11/2026", "FERNANDO ZEN", "ALTERAÇÃO DE PAREDES"))
        self.assertEqual(len(pl.linhas[0]), len(cab_antes))
        self.assertEqual(pl.linhas[0].split()[13:15], ["2", "3"])
        pl.salvar()
        bruto = ler_bytes(self.cpl)
        self.assertIn("ALTERAÇÃO DE PAREDES".encode("cp1252"), bruto)
        self.assertIn(b"\r\n    2\r\n26/11/2026\r\nFERNANDO ZEN\r\n", bruto)
        relido = ler_cpl(self.cpl)
        self.assertEqual(relido.revisao_atual, 2)
        self.assertEqual(relido.ultima_revisao.descricao, "ALTERAÇÃO DE PAREDES")
        self.assertEqual(len(relido.desenhos()), 2)

    def test_validacoes(self):
        pl = ler_cpl(self.cpl)
        self.assertTrue(any("próxima revisão" in p for p in pl.validar_revisao(Revisao(5, "26/11/2026", "A", "B"))))
        self.assertTrue(any("dd/mm/aaaa" in p for p in pl.validar_revisao(Revisao(2, "2026-11-26", "A", "B"))))
        self.assertTrue(any("CP1252" in p for p in pl.validar_revisao(Revisao(2, "26/11/2026", "A", "OK ✓"))))
        longa = "X" * (MAX_CARACTERES_DESCRICAO + 5)
        probs = pl.validar_revisao(Revisao(2, "26/11/2026", "A", longa))
        self.assertTrue(probs and all(p.startswith("AVISO:") for p in probs))
        with self.assertRaises(ErroCPL):
            pl.adicionar_revisao(Revisao(7, "26/11/2026", "A", "B"))

    def test_tabela_cheia(self):
        revs = [(n, "01/01/2026", "A", f"REV {n}") for n in range(11)]
        with open(self.cpl, "wb") as f:
            f.write(montar_cpl(revs))
        pl = ler_cpl(self.cpl)
        probs = pl.validar_revisao(Revisao(11, "26/11/2026", "A", "B"))
        self.assertTrue(any("11 linhas" in p for p in probs))

    def test_zerar_e_renomear_para_nova_fase(self):
        pl = ler_cpl(self.cpl)
        novo_id = ID.replace("-PB-", "-PE-")
        nova = pl.copiar_para(os.path.join(self.plantas, novo_id + ".CPL"))
        nova.zerar_revisoes()
        self.assertEqual(nova.renomear_referencias(ID, novo_id), 2)
        nova.adicionar_revisao(Revisao(0, "26/11/2026", "FERNANDO ZEN", "EMISSÃO INICIAL"))
        nova.salvar()
        relida = ler_cpl(nova.caminho)
        self.assertEqual(len(relida.revisoes), 1)
        self.assertEqual(relida.revisao_atual, 0)
        self.assertIn(novo_id + "_CR", relida.desenhos()[1].caminho_relativo)
        self.assertEqual(ler_cpl(self.cpl).revisao_atual, 1)  # original intacto

    def test_cabecalho_inconsistente(self):
        bruto = montar_cpl(REVS).replace(b"    1    2    0     0.000", b"    1    3    0     0.000")
        with open(self.cpl, "wb") as f:
            f.write(bruto)
        with self.assertRaises(ErroCPL):
            ler_cpl(self.cpl)

    def test_titulo_com_caractere_invalido(self):
        with open(self.cpl, "wb") as f:
            f.write(montar_cpl(REVS, titulo="PRX FOR").replace(b"PRX", b"PR\xef\xbf\xbd"))
        pl = ler_cpl(self.cpl)
        self.assertTrue(pl.titulo_com_caractere_invalido)
        self.assertEqual(pl.serializar(), ler_bytes(self.cpl))


class TestNomenclatura(BaseTemp):
    def test_nmcarq(self):
        regras = ler_nmcarq(self.ed)
        self.assertEqual(set(regras.fases), {"EP", "PE", "PB"})
        self.assertEqual(regras.prefixo_revisao, "-R")
        self.assertEqual(regras.nome_arquivo_revisao(ID, 5), ID + "-R05")

    def test_id_e_troca_de_fase(self):
        regras = ler_nmcarq(self.ed)
        idp = decompor_id(ID, regras)
        self.assertEqual((idp.fase, idp.numero), ("PB", "0601"))
        self.assertEqual(trocar_fase(ID, "pe", regras), "999-EST-PE-0601-TP-1FIA")
        with self.assertRaises(ErroNomenclatura):
            trocar_fase(ID, "XX", regras)
        with self.assertRaises(ErroNomenclatura):
            decompor_id("SEM-FASE-AQUI", regras)

    def test_fase_esperada(self):
        regras = ler_nmcarq(self.ed)
        self.assertEqual(nome_fase_esperado(self.plantas, "PB", regras), "PROJETO BASE")
        self.plotar(1, "MODIFICAÇÕES GERAIS", fase="PROJETO BÁSICO")
        txt = os.path.join(self.plantas, ID + "-R01.TXT")
        self.assertEqual(nome_fase_esperado(self.plantas, "PB", regras), "PROJETO BÁSICO")
        self.assertEqual(nome_fase_esperado(self.plantas, "PB", regras, ignorar=txt), "PROJETO BASE")
        self.assertEqual(ler_variaveis_plotagem(txt)["REVISAO_TXT01"], "MODIFICAÇÕES GERAIS")


@patch("src.skills.case_15_revisao_plantas.skill._tqs_editor_aberto", return_value=False)
class TestSkillRevisao(BaseTemp):
    def setUp(self):
        super().setUp()
        self.skill = RevisaoPlantasSkill()

    def run_skill(self, **kw):
        return self.skill.executar(caminho_edificio=self.ed, **kw)

    def test_listar_status(self, _):
        res = self.run_skill(acao="listar")
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["pranchas"][0]["status"], "aguardando plotagem")
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        self.assertEqual(self.run_skill(acao="listar")["pranchas"][0]["status"], "em dia")
        self.plotar(1, "MODIFICAÇÕES GERAIS", atraso_dwg=+600)
        self.assertEqual(self.run_skill(acao="listar")["pranchas"][0]["status"], "pendente")

    def test_resolver_prancha(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        for alvo in ("0601", "601", ID, "1afiada tipo b", "TIPO A"):
            res = self.run_skill(acao="emitir", prancha=alvo, descricao="X")
            self.assertEqual(res["prancha"], ID, alvo)
        self.assertFalse(self.run_skill(acao="emitir", prancha="0999", descricao="X")["sucesso"])

    def test_previa_nao_grava(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        antes = ler_bytes(self.cpl)
        res = self.run_skill(acao="emitir", prancha="0601", descricao="ajuste de vãos", data="26/11/2026")
        self.assertEqual(res["status"], "aguardando_aprovacao")
        self.assertEqual(res["revisao"]["rotulo"], "R02")
        self.assertEqual(res["revisao"]["descricao"], "AJUSTE DE VÃOS")
        self.assertEqual(res["revisao"]["autor"], "FERNANDO ZEN")
        self.assertEqual(ler_bytes(self.cpl), antes)

    def test_simular_nao_grava(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        antes = ler_bytes(self.cpl)
        res = self.run_skill(acao="emitir", prancha="0601", descricao="X", simular=True)
        self.assertEqual(res["status"], "simulado")
        self.assertTrue(os.path.exists(res["caminho_simulado"]))
        self.assertIn("+    2", res["diff_cpl"])
        self.assertEqual(ler_bytes(self.cpl), antes)

    def test_emitir_aprovado(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        res = self.run_skill(acao="emitir", prancha="0601", descricao="ajuste", data="26/11/2026", aprovado=True)
        self.assertEqual(res["status"], "sucesso", res.get("erro"))
        self.assertTrue(os.path.exists(res["backup_criado"]))
        self.assertEqual(os.path.basename(os.path.dirname(res["backup_criado"])), "backup_claude")
        self.assertTrue(self.skill.validar(res))
        self.assertEqual(ler_cpl(self.cpl).ultima_revisao.descricao, "AJUSTE")

    def test_bloqueia_revisao_nao_plotada(self, _):
        res = self.run_skill(acao="emitir", prancha="0601", descricao="X")
        self.assertFalse(res["sucesso"])
        self.assertIn("não foi plotada", res["erro"])
        self.assertTrue(self.run_skill(acao="emitir", prancha="0601", descricao="X", forcar=True)["sucesso"])

    def test_descricao_padrao_sem_base(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        res = self.run_skill(acao="emitir", prancha="0601")
        self.assertTrue(res["descricao_sugerida"])
        self.assertTrue(res["revisao"]["descricao"])

    def test_troca_de_fase(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        res = self.run_skill(acao="emitir", prancha="0601", fase="PE", data="26/11/2026", aprovado=True)
        self.assertEqual(res["status"], "sucesso", res.get("erro"))
        novo_id = "999-EST-PE-0601-TP-1FIA"
        nova = ler_cpl(os.path.join(self.plantas, novo_id + ".CPL"))
        self.assertEqual([(r.numero, r.descricao) for r in nova.revisoes], [(0, "EMISSÃO INICIAL")])
        self.assertTrue(os.path.exists(os.path.join(self.plantas, novo_id + "_CR.DWG")))
        self.assertEqual(ler_cpl(self.cpl).revisao_atual, 1)
        self.assertTrue(any("_FASE" in p for p in res["proximos_passos"]))
        self.assertEqual(res["fase_esperada_no_carimbo"], "PROJETO EXECUTIVO")
        # Repetir a troca para a mesma fase deve ser recusado
        self.assertFalse(self.run_skill(acao="emitir", prancha=ID, fase="PE")["sucesso"])

    def test_conferir(self, _):
        self.plotar(1, "MODIFICAÇÕES GERAIS")
        self.run_skill(acao="emitir", prancha="0601", descricao="ajuste", data="26/11/2026", aprovado=True)
        res = self.run_skill(acao="conferir", prancha="0601")
        self.assertEqual(res["status"], "divergente")
        # Uma plotagem anterior desta fase ensina o nome da fase (PB = PROJETO BÁSICO)
        self.plotar(2, "AJUSTE", data="26/11/2026")
        res = self.run_skill(acao="conferir", prancha="0601")
        self.assertEqual(res["status"], "sucesso", res["resumo_executivo"])
        self.plotar(2, "OUTRA COISA", data="26/11/2026")
        self.assertEqual(self.run_skill(acao="conferir", prancha="0601")["status"], "divergente")


class TestDiffEmissao(unittest.TestCase):
    def setUp(self):
        from src.skills.case_15_revisao_plantas import diff_emissao as de
        self.de = de

    def seg(self, a, b, **kw):
        return self.de._segmento(a, b, **kw)

    def test_normalizacao_de_texto(self):
        n = self.de._norm_texto
        self.assertEqual(n("%%c 16"), n("{ 16"))
        self.assertEqual(n("2%%d AO 19%%d PAVIMENTO"), n("2^ AO 19^ PAVIMENTO"))
        self.assertEqual(n("PRÉ-MODULAÇÃO"), n("PR\ufffd-MODULA\ufffd\ufffdO"))
        self.assertIsNone(self.de._texto(r"C:\TQS\X\GERAIS\BLOCO 15 MPa.jpg", 50, 20))

    def test_comparacao_por_presenca_tolerancia_e_macros(self):
        de = self.de
        base = [self.seg((10, 10), (20, 10), camada="1"), self.seg((30.004, 10), (40, 10), camada="1"),
                de._texto("120", 15, 12, camada="2"), de._texto("C:VALOR", 50, 20, camada="2")]
        atual = [self.seg((10, 10), (20, 10), nivel=247), self.seg((20, 10), (10, 10), nivel=247),  # duplicata invertida
                 self.seg((30.0, 10), (40, 10), nivel=247),                                          # arredondamento
                 de._texto("120", 15.4, 12, nivel=239)]                                              # alinhamento
        res = de.comparar(base, atual, macros=[(50.2, 20)])
        self.assertEqual((res.so_atual, res.so_base), ([], []))
        self.assertEqual(res.pena_para_nivel.get("1"), 247)

    def test_descricao_por_regioes(self):
        de = self.de
        res = de.ResultadoComparacao(
            so_atual=[self.seg((10, 10 + i * 0.1), (12, 10 + i * 0.1), nivel=247) for i in range(6)]
                     + [de._texto("ELEVADOR", 11, 11.5, nivel=291), de._texto("161x221", 30, 30, nivel=239)],
            so_base=[de._texto("161x211", 30.2, 30, camada="5")], casados=100)
        textos = [p for p in res.so_atual if p.tipo == "T"]
        desc, regioes = de.montar_descricao(res, textos)
        self.assertEqual(desc, "ALTERAÇÃO DE PAREDES E VÃOS - ELEVADOR")
        self.assertEqual(len(regioes), 2)
        self.assertTrue(any("161x211" in r["resumo"] and "161x221" in r["resumo"] for r in regioes))
        vazio = de.ResultadoComparacao(so_atual=[], so_base=[], casados=10)
        self.assertEqual(de.montar_descricao(vazio, [])[0], de.DESCRICAO_SEM_ALTERACAO)

    def test_ruido_pequeno_nao_vira_regiao(self):
        de = self.de
        res = de.ResultadoComparacao(so_atual=[self.seg((10, 10), (10.5, 10), nivel=0)], so_base=[], casados=10)
        self.assertEqual(de.montar_descricao(res, [])[0], de.DESCRICAO_SEM_ALTERACAO)

    def test_calibracao_054_r04(self):
        """O DWG salvo no instante da plotagem R04 não pode apresentar diferenças contra o R04.DXF."""
        ed = r"C:\TQS\Flexinc - [054] Visconde do Herval AE"
        dwg = os.path.join(ed, "TIPO A", "PRE_FOR_1aFIADA_TIPO A-R02.DWG")
        dxf = os.path.join(ed, "PLANTAS", "054-EST-PB-0601-TP-1FIA-R04.DXF")
        cpl = os.path.join(ed, "PLANTAS", "054-EST-PB-0601-TP-1FIA.CPL")
        if not all(os.path.exists(p) for p in (dwg, dxf, cpl)):
            self.skipTest("Arquivos do edifício 054 AE não disponíveis nesta máquina.")
        de = self.de
        desenho = ler_cpl(cpl).desenhos_conteudo()[0]
        atual, macros = de.primitivas_dwg(desenho, dwg)
        res = de.comparar(de.primitivas_dxf(dxf), atual, macros)
        desc, regioes = de.montar_descricao(res, [p for p in atual if p.tipo == "T"])
        self.assertEqual(desc, de.DESCRICAO_SEM_ALTERACAO, [r["resumo"] for r in regioes][:5])


class TestCarimbo(unittest.TestCase):
    def test_quebra_pecasdet_como_tqs(self):
        from src.skills.case_15_revisao_plantas.carimbo import quebrar_linhas
        # Os dois casos reais gerados pelo TQS (carimbos da R04 e da R05 da 054-...-0601)
        self.assertEqual(quebrar_linhas("PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO TIPO (2^ AO 19^ PAVIMENTO)"),
                         ["PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO ", "TIPO (2^ AO 19^ PAVIMENTO)"])
        self.assertEqual(quebrar_linhas("PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO TIPO A"),
                         ["PRÉ-MODULAÇÃO DE 1ª FIADA - PAVIMENTO ", "TIPO A"])
        self.assertEqual(quebrar_linhas("CURTO"), ["CURTO"])

    def test_carimbo_054_reproduz_tqs(self):
        """Gera o carimbo da 0601 numa pasta temporária: nenhuma variável sobra e a tabela segue o .CPL."""
        ed = r"C:\TQS\Flexinc - [054] Visconde do Herval AE"
        cpl = os.path.join(ed, "PLANTAS", "054-EST-PB-0601-TP-1FIA.CPL")
        cr = os.path.join(ed, "PLANTAS", "054-EST-PB-0601-TP-1FIA_CR.DWG")
        if not (os.path.exists(cpl) and os.path.exists(cr)):
            self.skipTest("Arquivos do edifício 054 AE não disponíveis nesta máquina.")
        from src.skills.case_15_revisao_plantas import carimbo as cb
        pl = ler_cpl(cpl)
        pasta = tempfile.mkdtemp(prefix="AUTQS_cr_")
        try:
            res = cb.preencher_carimbo(pl, ler_nmcarq(ed), ed, os.path.join(pasta, "teste_CR.DWG"))
            textos = [t[7] for t in cb._ler_textos(res["caminho"])]
            self.assertFalse([t for t in textos if t.strip().startswith("%")])
            ult = pl.ultima_revisao
            self.assertIn(ult.descricao, textos)
            self.assertEqual(res["preenchidas"]["REVISAO"], f"{ult.numero:02d}")
            self.assertIn(f"REVISAO_TXT{ult.numero + 1:02d}", res["apagadas"])
            anteriores = cb.valores_do_carimbo_existente(cr, cb.ler_variaveis_moldura(res["moldura"]))
            for var in ("TITEDI", "TITCLI", "ENDERECO_OBRA", "_FASE"):
                self.assertEqual(res["preenchidas"].get(var, ""), anteriores.get(var, ""), var)
        finally:
            shutil.rmtree(pasta, ignore_errors=True)


class TestPlotagem(unittest.TestCase):
    ED = r"C:\TQS\Flexinc - [054] Visconde do Herval AE"

    def test_cpl_temporario_com_caminhos_absolutos(self):
        cpl = os.path.join(self.ED, "PLANTAS", "054-EST-PB-0601-TP-1FIA.CPL")
        if not os.path.exists(cpl):
            self.skipTest("Arquivos do edifício 054 AE não disponíveis nesta máquina.")
        pl = ler_cpl(cpl)
        self.assertEqual([d.indice_linha for d in pl.desenhos()][:1], [pl.indice_eoc + 1])
        for d in pl.desenhos():
            self.assertEqual(pl.linhas[d.indice_linha].strip(), d.caminho_relativo.strip())

    def test_plotagem_054_igual_ao_editor(self):
        """Plota a 0601 numa pasta temporária: mesmos textos da R05 do Editor de Plantas e o edifício intocado."""
        from src.skills.case_15_revisao_plantas import plotagem as pt
        cpl = os.path.join(self.ED, "PLANTAS", "054-EST-PB-0601-TP-1FIA.CPL")
        try:
            pt.localizar_motor()
        except pt.ErroPlotagem:
            self.skipTest("TQS não instalado nesta máquina.")
        if not os.path.exists(cpl):
            self.skipTest("Arquivos do edifício 054 AE não disponíveis nesta máquina.")
        pl = ler_cpl(cpl)
        regras = ler_nmcarq(self.ED)
        oficial = os.path.join(self.ED, "PLANTAS", regras.nome_arquivo_revisao(pl.id, pl.revisao_atual) + ".PDF")
        pasta_plantas = os.path.join(self.ED, "PLANTAS")
        antes = {f: os.path.getmtime(os.path.join(pasta_plantas, f)) for f in os.listdir(pasta_plantas)}
        pasta = tempfile.mkdtemp(prefix="AUTQS_plot_teste_")
        try:
            res = pt.plotar_prancha(pl, regras, self.ED, pasta_trabalho=pasta)
            self.assertTrue(os.path.isfile(res["pdf"]))
            self.assertEqual(sorted(res["arquivos"]), [".DXF", ".PDF"])
            self.assertIn("DXF da plotagem", [c["item"] for c in res["checagens"]])
            self.assertTrue(all(c["ok"] for c in res["checagens"]), res["checagens"])
            if os.path.exists(oficial) and pl.revisao_atual == 5:
                def textos(p):
                    return sorted(t["texto"] for t in pt._textos_pdf(p)[1:] if ".PLT" not in t["texto"].upper())
                self.assertEqual(textos(res["pdf"]), textos(oficial))
        finally:
            shutil.rmtree(pasta, ignore_errors=True)
        depois = {f: os.path.getmtime(os.path.join(pasta_plantas, f)) for f in os.listdir(pasta_plantas)}
        self.assertEqual(antes, depois)


class TestComandos(unittest.TestCase):
    def test_intencao(self):
        from src.skills.case_15_revisao_plantas.comandos import eh_pedido_revisao
        self.assertTrue(eh_pedido_revisao("Emitir revisão da prancha 0601"))
        self.assertTrue(eh_pedido_revisao("listar revisões das plantas do 054 AE"))
        self.assertTrue(eh_pedido_revisao("conferir a revisão da 0601"))
        self.assertFalse(eh_pedido_revisao("comparar a revisão da planta de formas"))
        self.assertFalse(eh_pedido_revisao("gere a planta de cargas do 054"))

    def test_parametros(self):
        from src.skills.case_15_revisao_plantas.comandos import extrair_parametros_revisao as ext
        p = ext("emitir revisão da prancha 0601 do 054 AE descrição: ajuste do elevador 2")
        self.assertEqual((p["acao"], p["prancha"], p["edificio_nome"], p["descricao"]),
                         ("emitir", "0601", "054 AE", "ajuste do elevador 2"))
        p = ext("emitir revisão da 054-EST-PB-0601-TP-1FIA na fase PE")
        self.assertEqual((p["prancha"], p["edificio_nome"], p["fase"]), ("054-EST-PB-0601-TP-1FIA", "054", "PE"))
        p = ext("listar revisões das pranchas do 054 AE")
        self.assertEqual((p["acao"], p["edificio_nome"]), ("listar", "054 AE"))
        self.assertNotIn("prancha", p)
        p = ext("conferir revisão da prancha 601", "055")
        self.assertEqual((p["acao"], p["prancha"], p["edificio_nome"]), ("conferir", "601", "055"))
        self.assertNotIn("fase", ext("emitir revisão da prancha 0601 conforme a fase do projeto"))
        self.assertTrue(ext("simular nova revisão da 0601")["simular"])
        p = ext("preencher o carimbo da prancha 0601 do 054 AE")
        self.assertEqual((p["acao"], p["prancha"], p["edificio_nome"]), ("preencher", "0601", "054 AE"))
        p = ext("plotar a prancha 0601 do 054 AE em PDF")
        self.assertEqual((p["acao"], p["prancha"], p["edificio_nome"]), ("plotar", "0601", "054 AE"))
        self.assertEqual(ext("gerar o PDF da revisão da 0601")["acao"], "plotar")

    def test_intencao_plotar(self):
        from src.skills.case_15_revisao_plantas.comandos import eh_pedido_revisao
        self.assertTrue(eh_pedido_revisao("plotar a prancha 0601"))
        self.assertTrue(eh_pedido_revisao("gere o PDF da revisão R05 da 0601"))
        self.assertFalse(eh_pedido_revisao("gere a planta de cargas do 054"))


class TestRoteamentoRevisao(unittest.TestCase):
    def test_orquestrador_encaminha_sem_aprovar(self):
        from src.agent.orchestrator import AutqsAgentOrchestrator
        orq = AutqsAgentOrchestrator()
        with patch.object(orq.registry, "executar_ferramenta", return_value={"status": "sucesso"}) as m:
            orq.processar_comando_local("emitir revisão da prancha 0601 do 054 AE", {"aprovado": True})
        nome, params = m.call_args[0]
        self.assertEqual(nome, "emitir_revisao_planta")
        self.assertEqual((params["prancha"], params["edificio_nome"]), ("0601", "054 AE"))
        self.assertNotIn("aprovado", params)

    def test_chat_pede_aprovacao_e_grava(self):
        from src.agent.chat_agent import AutqsChatAgent
        agente = AutqsChatAgent()
        previa = {"status": "aguardando_aprovacao", "sucesso": True, "resumo_executivo": "prévia",
                  "revisao": {"numero": 5, "rotulo": "R05", "data": "26/11/2026", "autor": "FERNANDO ZEN",
                              "descricao": "AJUSTE DO ELEVADOR"}}
        gravado = {"status": "sucesso", "sucesso": True, "resumo_executivo": "✅ gravado"}
        with patch.object(agente.orchestrator.registry, "executar_ferramenta", side_effect=[previa, gravado]) as m:
            r1 = agente.responder("emitir revisão da prancha 0601 do 054 AE")
            self.assertEqual(r1["tipo"], "solicitacao_aprovacao")
            self.assertNotIn("aprovado", m.call_args_list[0][0][1])
            r2 = agente.responder("sim")
        self.assertEqual(r2["texto"], "✅ gravado")
        params_gravacao = m.call_args_list[1][0][1]
        self.assertTrue(params_gravacao["aprovado"])
        self.assertEqual(params_gravacao["descricao"], "AJUSTE DO ELEVADOR")

    def test_chat_plotar_pede_aprovacao(self):
        from src.agent.chat_agent import AutqsChatAgent
        agente = AutqsChatAgent()
        previa = {"status": "aguardando_aprovacao", "sucesso": True, "acao": "plotar", "revisao": "R05",
                  "resumo_executivo": "prévia do PDF"}
        gravado = {"status": "sucesso", "sucesso": True, "resumo_executivo": "✅ PDF gravado"}
        with patch.object(agente.orchestrator.registry, "executar_ferramenta", side_effect=[previa, gravado]) as m:
            r1 = agente.responder("plotar a prancha 0601 do 054 AE")
            self.assertEqual(r1["tipo"], "solicitacao_aprovacao")
            self.assertIn("o PDF/DXF em PLANTAS", r1["texto"])
            r2 = agente.responder("sim")
        self.assertEqual(r2["texto"], "✅ PDF gravado")
        params_gravacao = m.call_args_list[1][0][1]
        self.assertEqual((params_gravacao["acao"], params_gravacao["aprovado"]), ("plotar", True))
        self.assertNotIn("descricao", params_gravacao)

    def test_chat_cancelamento(self):
        from src.agent.chat_agent import AutqsChatAgent
        agente = AutqsChatAgent()
        previa = {"status": "aguardando_aprovacao", "sucesso": True, "resumo_executivo": "prévia",
                  "revisao": {"numero": 5, "rotulo": "R05", "data": "26/11/2026", "autor": "A", "descricao": "B"}}
        with patch.object(agente.orchestrator.registry, "executar_ferramenta", return_value=previa) as m:
            agente.responder("emitir revisão da prancha 0601 do 054 AE")
            r = agente.responder("não")
        self.assertEqual(m.call_count, 1)
        self.assertIn("Operação cancelada", r["texto"])


if __name__ == "__main__":
    unittest.main()
