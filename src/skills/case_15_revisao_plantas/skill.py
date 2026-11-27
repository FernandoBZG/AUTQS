"""
Case 15: emissão de revisões de plantas do TQS (Editor de Plantas, arquivos .CPL).

Fluxo:
    listar   -> pranchas do edifício, revisão atual e status (pendente / aguardando plotagem)
    emitir   -> registra a próxima revisão no .CPL (prévia + aprovação + backup); na troca
                de fase cria a prancha da nova fase começando em R00
    preencher-> gera o carimbo <ID>_CR.DWG preenchido (botão "Preencher" do editor)
    plotar   -> plota o PDF da revisão atual com o motor de plotagem do TQS (NCVRPLD.EXE)
                numa cópia temporária da prancha e, aprovado, grava o PDF em PLANTAS
    conferir -> confere o -Rnn.PDF (e o .TXT, quando o Editor de Plantas o gera)

A skill nunca abre o TQS nem altera desenhos; o motor de plotagem roda só sobre cópias.
"""
import difflib
import os
import shutil
import subprocess
import tempfile
import unicodedata
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.skills.base_skill import BaseSkill
from src.skills.case_15_revisao_plantas.cpl import (
    ErroCPL, PlantaCPL, Revisao, ler_cpl, listar_cpls, TIPO_CARIMBO,
)
from src.skills.case_15_revisao_plantas.nomenclatura import (
    ErroNomenclatura, RegrasNomenclatura, decompor_id, ler_nmcarq, ler_variaveis_plotagem,
    localizar_saida_plotagem, nome_fase_esperado, trocar_fase,
)
from src.skills.case_15_revisao_plantas.plotagem import ErroPlotagem

DESCRICAO_PADRAO = "MODIFICAÇÕES GERAIS"
DESCRICAO_EMISSAO_INICIAL = "EMISSÃO INICIAL"
TOLERANCIA_PLOTAGEM_S = 120.0


def _norm(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto or "") if unicodedata.category(c) != "Mn")
    return " ".join(sem_acento.upper().split())


def _ler_bytes(caminho: str) -> bytes:
    with open(caminho, "rb") as f:
        return f.read()


def _data_hora(ts: Optional[float]) -> str:
    return datetime.fromtimestamp(ts).strftime("%d/%m/%Y %H:%M") if ts else "-"


def _tqs_editor_aberto() -> bool:
    """True se o EAGW (editor gráfico onde roda o Editor de Plantas) estiver aberto."""
    try:
        saida = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq EAGW.EXE", "/NH"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return "EAGW.EXE" in saida.upper()
    except Exception:
        return False


class RevisaoPlantasSkill(BaseSkill):
    """Emite, lista e confere revisões de pranchas do Editor de Plantas do TQS."""

    @property
    def nome(self) -> str:
        return "emitir_revisao_planta"

    @property
    def descricao(self) -> str:
        return (
            "Emite revisões de pranchas do Editor de Plantas do TQS (.CPL): lista as pranchas do edifício "
            "com a revisão atual e o que está pendente, registra a próxima revisão (nº, data, autor e "
            "descrição sugerida a partir do que mudou desde a última plotagem) na tabela de revisões do "
            "selo, abre uma nova prancha em R00 quando a fase do projeto muda (EP, AP, PB, PE...), preenche o "
            "carimbo, plota o PDF da revisão (-Rnn.PDF) com o motor de plotagem do TQS sem abrir o editor e "
            "confere a plotagem. Toda gravação no edifício exige aprovação."
        )

    # ======================================================================
    # Entrada
    # ======================================================================
    def executar(
        self,
        edificio_nome: str = "054",
        acao: str = "listar",
        prancha: Optional[str] = None,
        descricao: Optional[str] = None,
        autor: Optional[str] = None,
        data: Optional[str] = None,
        fase: Optional[str] = None,
        simular: bool = False,
        aprovado: bool = False,
        forcar: bool = False,
        caminho_edificio: str = "",
        **kwargs,
    ) -> Dict[str, Any]:
        acao = (acao or "listar").lower().strip()
        try:
            if acao == "listar":
                # Na listagem, um código que bate com mais de um edifício (ex.: 054 AE e 054 CA) lista todos
                resultados = [self._listar(c, os.path.join(c, "PLANTAS"), ler_nmcarq(c))
                              for c in self._candidatos_edificio(edificio_nome, caminho_edificio, None)]
                if len(resultados) == 1:
                    return resultados[0]
                return {"status": "sucesso", "sucesso": True, "acao": "listar",
                        "edificio": ", ".join(r["edificio"] for r in resultados),
                        "pranchas": [dict(p, edificio=r["edificio"]) for r in resultados for p in r["pranchas"]],
                        "resumo_executivo": "\n\n".join(r["resumo_executivo"] for r in resultados)}
            caminho_ed = self._resolver_edificio(edificio_nome, caminho_edificio, prancha)
            regras = ler_nmcarq(caminho_ed)
            pasta_plantas = os.path.join(caminho_ed, "PLANTAS")
            if not prancha:
                return self._erro("Informe a prancha (nº como '0601', o ID completo ou parte do título).")
            planta, avisos_resolucao = self._resolver_prancha(pasta_plantas, prancha, regras)
            if acao == "emitir":
                return self._emitir(caminho_ed, planta, regras, descricao, autor, data, fase,
                                    simular, aprovado, forcar, avisos_resolucao)
            if acao == "conferir":
                return self._conferir(planta, regras, avisos_resolucao)
            if acao == "preencher":
                return self._preencher(caminho_ed, planta, regras, simular, aprovado, avisos_resolucao)
            if acao == "plotar":
                return self._plotar(caminho_ed, planta, regras, simular, aprovado, forcar, avisos_resolucao)
            return self._erro(f"Ação '{acao}' desconhecida. Use 'listar', 'emitir', 'preencher', 'plotar' ou 'conferir'.")
        except (ErroCPL, ErroNomenclatura, ErroPlotagem, FileNotFoundError, ValueError) as e:
            return self._erro(str(e))

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Após uma emissão gravada, relê o .CPL e confere que a revisão está lá."""
        if not resultado.get("sucesso"):
            return False
        if resultado.get("acao") == "emitir" and resultado.get("status") == "sucesso":
            try:
                pl = ler_cpl(resultado["caminho_cpl"])
                rev = resultado["revisao"]
                ult = pl.ultima_revisao
                return bool(ult and ult.numero == rev["numero"] and _norm(ult.descricao) == _norm(rev["descricao"]))
            except Exception:
                return False
        return True

    # ======================================================================
    # Resolução de edifício e prancha
    # ======================================================================
    @staticmethod
    def _erro(msg: str, **extra) -> Dict[str, Any]:
        res = {"status": "erro", "sucesso": False, "erro": msg, "resumo_executivo": f"❌ {msg}"}
        res.update(extra)
        return res

    def _resolver_edificio(self, edificio_nome: str, caminho_edificio: str, prancha: Optional[str]) -> str:
        candidatos = self._candidatos_edificio(edificio_nome, caminho_edificio, prancha)
        if len(candidatos) > 1:
            nomes = ", ".join(os.path.basename(c) for c in candidatos)
            raise ValueError(f"Mais de um edifício corresponde a '{edificio_nome}': {nomes}. Seja mais específico.")
        return candidatos[0]

    def _candidatos_edificio(self, edificio_nome: str, caminho_edificio: str, prancha: Optional[str]) -> List[str]:
        """Edifícios com plantas do Editor de Plantas que correspondem ao nome (e contêm a prancha, se dada)."""
        for cand in (caminho_edificio, edificio_nome):
            if cand and os.path.isdir(cand):
                return [cand]

        from src.tqs_adapter.building_reader import TQSBuildingReader
        tokens = [t.lower() for t in (edificio_nome or "").split() if t]
        vistos, candidatos = set(), []
        for ed in TQSBuildingReader.listar_edificios_disponiveis():
            nome = ed["nome"]
            if nome in vistos or not all(t in nome.lower() for t in tokens):
                continue
            vistos.add(nome)
            if listar_cpls(os.path.join(ed["caminho"], "PLANTAS")):
                candidatos.append(ed["caminho"])

        if prancha and len(candidatos) > 1:
            com_prancha = []
            for c in candidatos:
                try:
                    self._resolver_prancha(os.path.join(c, "PLANTAS"), prancha, ler_nmcarq(c))
                    com_prancha.append(c)
                except ValueError:
                    com_prancha.append(c)   # a prancha existe, mas é ambígua: o erro aparece ao resolvê-la
                except (ErroCPL, ErroNomenclatura, FileNotFoundError):
                    pass
            candidatos = com_prancha or candidatos

        if not candidatos:
            raise FileNotFoundError(
                f"Nenhum edifício '{edificio_nome}' com plantas do Editor de Plantas (PLANTAS\\*.CPL) foi encontrado."
            )
        return candidatos

    def _resolver_prancha(self, pasta_plantas: str, prancha: str, regras: RegrasNomenclatura) -> Tuple[PlantaCPL, List[str]]:
        cpls = listar_cpls(pasta_plantas)
        if not cpls:
            raise FileNotFoundError(f"Nenhuma planta (.CPL) em {pasta_plantas}.")
        alvo = _norm(prancha)
        exatos, por_numero, parciais = [], [], []
        for caminho in cpls:
            pl = ler_cpl(caminho)
            pid = _norm(pl.id)
            try:
                numero = decompor_id(pl.id, regras).numero
            except ErroNomenclatura:
                numero = ""
            if pid == alvo:
                exatos.append(pl)
            elif numero and alvo.isdigit() and numero.lstrip("0") == alvo.lstrip("0"):
                por_numero.append(pl)
            else:
                textos = [pid, _norm(pl.titulo)] + [_norm(d.caminho_relativo) + " " + _norm(d.pavimento) for d in pl.desenhos_conteudo()]
                if any(alvo in t for t in textos):
                    parciais.append(pl)

        for grupo in (exatos, por_numero, parciais):
            if not grupo:
                continue
            if len(grupo) == 1:
                return grupo[0], []
            numeros = set()
            for pl in grupo:
                try:
                    numeros.add(decompor_id(pl.id, regras).numero)
                except ErroNomenclatura:
                    numeros.add(pl.id)
            if len(numeros) == 1:
                # Mesma prancha em fases diferentes: a fase vigente é o .CPL mais recente
                grupo.sort(key=lambda p: os.path.getmtime(p.caminho), reverse=True)
                outras = ", ".join(p.id for p in grupo[1:])
                return grupo[0], [f"Usei {grupo[0].id} (o .CPL mais recente); também existe: {outras}."]
            ids = ", ".join(p.id for p in grupo)
            raise ValueError(f"'{prancha}' corresponde a mais de uma prancha: {ids}. Informe o nº ou o ID completo.")
        disponiveis = ", ".join(os.path.splitext(os.path.basename(c))[0] for c in cpls)
        raise FileNotFoundError(f"Prancha '{prancha}' não encontrada. Pranchas disponíveis: {disponiveis}.")

    # ======================================================================
    # Status de plotagem
    # ======================================================================
    def _status_prancha(self, pl: PlantaCPL, regras: RegrasNomenclatura) -> Dict[str, Any]:
        n = pl.revisao_atual
        pdf = localizar_saida_plotagem(pl.pasta, pl.id, n, regras, ".PDF") if n is not None else None
        ts_pdf = os.path.getmtime(pdf) if pdf else None
        desenhos = []
        alterado_depois = []
        for d in pl.desenhos_conteudo():
            cam = d.caminho_absoluto(pl.pasta)
            ts = os.path.getmtime(cam) if os.path.exists(cam) else None
            desenhos.append({"caminho": cam, "existe": ts is not None, "modificado_em": _data_hora(ts)})
            if ts and ts_pdf and ts > ts_pdf + TOLERANCIA_PLOTAGEM_S:
                alterado_depois.append(os.path.basename(cam))
        if n is None:
            status = "sem revisões"
        elif not pdf:
            status = "aguardando plotagem"
        elif alterado_depois:
            status = "pendente"
        else:
            status = "em dia"
        return {"pdf_revisao_atual": pdf, "plotada_em": _data_hora(ts_pdf), "desenhos": desenhos,
                "alterados_apos_plotagem": alterado_depois, "status": status}

    # ======================================================================
    # Listar
    # ======================================================================
    def _listar(self, caminho_ed: str, pasta_plantas: str, regras: RegrasNomenclatura) -> Dict[str, Any]:
        pranchas = []
        for caminho in listar_cpls(pasta_plantas):
            try:
                pl = ler_cpl(caminho)
            except ErroCPL as e:
                pranchas.append({"id": os.path.splitext(os.path.basename(caminho))[0], "erro": str(e)})
                continue
            try:
                idp = decompor_id(pl.id, regras)
                fase, numero = idp.fase, idp.numero
            except ErroNomenclatura:
                fase, numero = "?", "?"
            ult = pl.ultima_revisao
            st = self._status_prancha(pl, regras)
            pranchas.append({
                "id": pl.id, "fase": fase, "numero": numero, "titulo": pl.titulo,
                "titulo_com_caractere_invalido": pl.titulo_com_caractere_invalido,
                "revisao_atual": pl.revisao_atual,
                "ultima_revisao": vars(ult) if ult else None,
                **st,
            })

        linhas = [f"### Pranchas do Editor de Plantas — {os.path.basename(caminho_ed)}\n",
                  "| Prancha | Fase | Título | Rev. | Última revisão | Plotada em | Status |",
                  "| :--- | :-: | :--- | :-: | :--- | :-: | :--- |"]
        for p in pranchas:
            if "erro" in p:
                linhas.append(f"| {p['id']} | - | ⚠️ {p['erro']} | - | - | - | erro |")
                continue
            ult = p["ultima_revisao"]
            ult_txt = f"{ult['data']} — {ult['descricao']}" if ult else "-"
            rev = f"R{p['revisao_atual']:02d}" if p["revisao_atual"] is not None else "-"
            status = p["status"]
            if p["alterados_apos_plotagem"]:
                status += f" ({', '.join(p['alterados_apos_plotagem'])} alterado após a plotagem)"
            titulo = p["titulo"] + (" ⚠️" if p["titulo_com_caractere_invalido"] else "")
            linhas.append(f"| {p['id']} | {p['fase']} | {titulo} | {rev} | {ult_txt} | {p['plotada_em']} | {status} |")
        if any(p.get("titulo_com_caractere_invalido") for p in pranchas):
            linhas.append("\n⚠️ Título com caractere inválido gravado no .CPL; corrija o título no Editor de Plantas.")
        return {"status": "sucesso", "sucesso": True, "acao": "listar", "edificio": os.path.basename(caminho_ed),
                "pasta_plantas": pasta_plantas, "pranchas": pranchas, "resumo_executivo": "\n".join(linhas)}

    # ======================================================================
    # Emitir
    # ======================================================================
    def _emitir(self, caminho_ed: str, pl: PlantaCPL, regras: RegrasNomenclatura,
                descricao: Optional[str], autor: Optional[str], data: Optional[str], fase: Optional[str],
                simular: bool, aprovado: bool, forcar: bool, avisos: List[str]) -> Dict[str, Any]:
        avisos = list(avisos)
        fase_atual = decompor_id(pl.id, regras).fase
        troca_fase = bool(fase) and fase.upper() != fase_atual.upper()

        # Pendências que normalmente indicam engano (ex.: registrar duas vezes sem plotar)
        st = self._status_prancha(pl, regras)
        if not troca_fase and st["status"] == "aguardando plotagem" and not forcar:
            return self._erro(
                f"A R{pl.revisao_atual:02d} de {pl.id} está registrada mas ainda não foi plotada "
                f"(não há {regras.nome_arquivo_revisao(pl.id, pl.revisao_atual)}.PDF). Plote essa revisão no "
                "Editor de Plantas antes de emitir a próxima, ou use forcar=True."
            )

        if troca_fase:
            novo_id = trocar_fase(pl.id, fase, regras)
            novo_caminho = os.path.join(pl.pasta, novo_id + ".CPL")
            if os.path.exists(novo_caminho):
                return self._erro(f"A prancha da fase {fase.upper()} já existe ({novo_id}); emita a revisão nela.")
            destino = pl.copiar_para(novo_caminho)
            destino.zerar_revisoes()
            destino.renomear_referencias(pl.id, novo_id)
            numero = 0
        else:
            novo_id = pl.id
            destino = pl.copiar_para(pl.caminho)
            numero = pl.proximo_numero()

        ult = pl.ultima_revisao
        autor_final = (autor or (ult.autor if ult else "") or os.environ.get("AUTQS_AUTOR_REVISAO", "")).strip().upper()
        if not autor_final:
            return self._erro("Informe o autor da revisão (a prancha ainda não tem histórico para usar como padrão).")
        data_final = (data or datetime.now().strftime("%d/%m/%Y")).strip()

        diferencas: Dict[str, Any] = {}
        descricao_sugerida = False
        if descricao:
            descricao_final = descricao
        elif troca_fase or numero == 0:
            descricao_final = DESCRICAO_EMISSAO_INICIAL
            descricao_sugerida = True
        else:
            descricao_final, diferencas = self._sugerir_descricao(pl, regras)
            descricao_sugerida = True
            if diferencas.get("aviso"):
                avisos.append(diferencas["aviso"])
        descricao_final = " ".join(descricao_final.split()).upper()

        rev = Revisao(numero=numero, data=data_final, autor=autor_final, descricao=descricao_final)
        problemas = destino.validar_revisao(rev)
        erros = [p for p in problemas if not p.startswith("AVISO:")]
        avisos += [p.replace("AVISO: ", "") for p in problemas if p.startswith("AVISO:")]
        if erros:
            return self._erro(" ".join(erros))
        destino.adicionar_revisao(rev)

        if _tqs_editor_aberto():
            avisos.append("O TQS (EAGW) está aberto: feche a planta no Editor de Plantas antes de gravar, "
                          "senão o editor pode sobrescrever o .CPL com a versão antiga.")
        if pl.titulo_com_caractere_invalido:
            avisos.append("O título desta planta tem um caractere inválido gravado; corrija-o no Editor de Plantas.")

        nome_saida = regras.nome_arquivo_revisao(novo_id, numero)
        fase_destino = (fase or fase_atual).upper()
        fase_esperada = nome_fase_esperado(pl.pasta, fase_destino, regras)
        proximos = [
            f"Plote pela skill (acao='plotar'): ela preenche o carimbo e gera {nome_saida}.PDF com o motor de "
            "plotagem do TQS, sem abrir o editor.",
            f"Ou, no TQS: abra a planta {novo_id} no Editor de Plantas (feche e abra de novo se já estiver aberta), "
            f"confira a linha {regras.rotulo_revisao(numero)} e plote; depois rode acao='conferir'.",
        ]
        if troca_fase:
            proximos.insert(1, f"Atualize a variável _FASE para \"{fase_esperada}\" nas variáveis do Editor de Plantas antes de plotar.")

        base = {
            "acao": "emitir", "edificio": os.path.basename(caminho_ed),
            "prancha": pl.id, "prancha_destino": novo_id, "troca_fase": troca_fase,
            "fase": fase_destino, "fase_esperada_no_carimbo": fase_esperada,
            "caminho_cpl": destino.caminho,
            "revisao": {"numero": numero, "rotulo": regras.rotulo_revisao(numero), "data": data_final,
                        "autor": autor_final, "descricao": descricao_final},
            "descricao_sugerida": descricao_sugerida, "diferencas": diferencas,
            "avisos": avisos, "proximos_passos": proximos, "nome_saida_plotagem": nome_saida,
        }

        original_bytes = _ler_bytes(pl.caminho)
        novo_bytes = destino.serializar()
        diff_cpl = "".join(difflib.unified_diff(
            original_bytes.decode("cp1252", errors="replace").splitlines(True) if not troca_fase else [],
            novo_bytes.decode("cp1252", errors="replace").splitlines(True),
            fromfile=os.path.basename(pl.caminho) if not troca_fase else "(novo)",
            tofile=os.path.basename(destino.caminho), n=1,
        ))

        if simular:
            pasta_sim = os.path.join(tempfile.gettempdir(), "AUTQS_revisoes")
            os.makedirs(pasta_sim, exist_ok=True)
            caminho_sim = destino.salvar(os.path.join(pasta_sim, os.path.basename(destino.caminho)))
            base.update(status="simulado", sucesso=True, caminho_simulado=caminho_sim, diff_cpl=diff_cpl)
            base["resumo_executivo"] = self._resumo_emissao(base, "🧪 Simulação (nada foi gravado no TQS)")
            return base

        if not aprovado:
            base.update(status="aguardando_aprovacao", sucesso=True, diff_cpl=diff_cpl)
            base["resumo_executivo"] = self._resumo_emissao(base, "⚠️ Revisão pronta para gravar — aguardando aprovação")
            return base

        # ---- Gravação aprovada ----
        if _ler_bytes(pl.caminho) != original_bytes:
            return self._erro(f"{pl.caminho} mudou durante a operação; nada foi gravado. Rode a emissão de novo.")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"{pl.caminho}_BKP_{ts}"   # extensão diferente de .CPL: o editor não lista como planta
        shutil.copy2(pl.caminho, backup)
        carimbo_copiado = None
        try:
            if troca_fase:
                carimbo_copiado = self._copiar_carimbo(pl, novo_id)
            destino.salvar()
            relido = ler_cpl(destino.caminho)
            if not relido.ultima_revisao or relido.ultima_revisao.numero != numero:
                raise ErroCPL("a releitura do .CPL gravado não mostra a nova revisão")
        except Exception as e:
            if troca_fase:
                if os.path.exists(destino.caminho):
                    os.remove(destino.caminho)
                if carimbo_copiado and os.path.exists(carimbo_copiado):
                    os.remove(carimbo_copiado)
            else:
                shutil.copy2(backup, pl.caminho)
            return self._erro(f"Falha ao gravar a revisão ({e}); o .CPL original foi mantido.", backup_criado=backup)

        base.update(status="sucesso", sucesso=True, backup_criado=backup, carimbo_copiado=carimbo_copiado,
                    gravado_em=_data_hora(os.path.getmtime(destino.caminho)))
        base["resumo_executivo"] = self._resumo_emissao(base, f"✅ Revisão {regras.rotulo_revisao(numero)} registrada em {novo_id}")
        return base

    @staticmethod
    def _copiar_carimbo(pl: PlantaCPL, novo_id: str) -> Optional[str]:
        """Na troca de fase, duplica o <ID>_CR.DWG para o novo ID (o TQS reescreve as variáveis na plotagem)."""
        for d in pl.desenhos():
            if d.tipo != TIPO_CARIMBO:
                continue
            origem = d.caminho_absoluto(pl.pasta)
            destino = os.path.join(os.path.dirname(origem), os.path.basename(origem).replace(pl.id, novo_id))
            if os.path.exists(origem) and not os.path.exists(destino):
                shutil.copy2(origem, destino)
                return destino
        return None

    def _sugerir_descricao(self, pl: PlantaCPL, regras: RegrasNomenclatura) -> Tuple[str, Dict[str, Any]]:
        try:
            from src.skills.case_15_revisao_plantas.diff_emissao import sugerir_descricao_revisao
        except ImportError:
            return DESCRICAO_PADRAO, {"aviso": "Comparação com a última emissão indisponível; usei a descrição padrão."}
        try:
            return sugerir_descricao_revisao(pl, regras)
        except Exception as e:
            return DESCRICAO_PADRAO, {"aviso": f"Não consegui comparar com a última emissão ({e}); usei a descrição padrão."}

    @staticmethod
    def _resumo_emissao(res: Dict[str, Any], titulo: str) -> str:
        rev = res["revisao"]
        linhas = [f"### {titulo}\n",
                  f"- **Edifício:** `{res['edificio']}`",
                  f"- **Prancha:** `{res['prancha_destino']}`" + (f" (nova fase, a partir de `{res['prancha']}`)" if res["troca_fase"] else ""),
                  f"- **Arquivo:** `{res['caminho_cpl']}`\n",
                  "| Rev. | Data | Autor | Descrição |",
                  "| :-: | :-: | :--- | :--- |",
                  f"| {rev['rotulo']} | {rev['data']} | {rev['autor']} | {rev['descricao']} |"]
        if res.get("descricao_sugerida"):
            linhas.append("\n_Descrição sugerida automaticamente — edite se quiser (parâmetro `descricao`)._")
        regioes = (res.get("diferencas") or {}).get("regioes") or []
        if regioes:
            linhas.append("\n**O que mudou desde a última emissão:**")
            for r in regioes[:8]:
                linhas.append(f"- {r['resumo']}")
        if res.get("backup_criado"):
            linhas.append(f"\nBackup do .CPL: `{res['backup_criado']}`")
        if res.get("caminho_simulado"):
            linhas.append(f"\n.CPL simulado: `{res['caminho_simulado']}`")
        for a in res.get("avisos", []):
            linhas.append(f"\n⚠️ {a}")
        if res["status"] in ("sucesso", "aguardando_aprovacao", "simulado"):
            linhas.append("\n**Próximos passos:**")
            for i, p in enumerate(res.get("proximos_passos", []), 1):
                linhas.append(f"{i}. {p}")
        return "\n".join(linhas)

    # ======================================================================
    # Preencher carimbo (<ID>_CR.DWG), como o botão "Preencher" do Editor de Plantas
    # ======================================================================
    def _preencher(self, caminho_ed: str, pl: PlantaCPL, regras: RegrasNomenclatura,
                   simular: bool, aprovado: bool, avisos: List[str]) -> Dict[str, Any]:
        from src.skills.case_15_revisao_plantas import carimbo as cb

        destino = next((d.caminho_absoluto(pl.pasta) for d in pl.desenhos() if d.tipo == TIPO_CARIMBO),
                       os.path.join(pl.pasta, f"{pl.id}_CR.DWG"))
        pasta_tmp = os.path.join(tempfile.gettempdir(), "AUTQS_revisoes")
        gerado = cb.preencher_carimbo(pl, regras, caminho_ed, os.path.join(pasta_tmp, os.path.basename(destino)))

        anteriores: Dict[str, str] = {}
        if os.path.exists(destino):
            anteriores = cb.valores_do_carimbo_existente(destino, cb.ler_variaveis_moldura(gerado["moldura"]))
        mudancas = []
        for nome in sorted(set(gerado["preenchidas"]) | set(anteriores)):
            antes = anteriores.get(nome, "")
            depois = gerado["preenchidas"].get(nome, "")
            if " ".join(antes.split()) != " ".join(depois.split()):
                mudancas.append({"variavel": nome, "antes": antes, "depois": depois})

        avisos = list(avisos)
        if _tqs_editor_aberto():
            avisos.append("O TQS (EAGW) está aberto: se a planta estiver aberta no Editor de Plantas, feche e abra "
                          "de novo depois da gravação para ver o carimbo atualizado.")
        base = {"acao": "preencher", "edificio": os.path.basename(caminho_ed), "prancha": pl.id,
                "caminho_carimbo": destino, "moldura": gerado["moldura"], "mudancas": mudancas,
                "variaveis_preenchidas": gerado["preenchidas"], "variaveis_apagadas": gerado["apagadas"],
                "avisos": avisos}

        def resumo(titulo: str) -> str:
            linhas = [f"### {titulo}\n", f"- **Prancha:** `{pl.id}`", f"- **Carimbo:** `{destino}`",
                      f"- **Moldura:** `{gerado['moldura']}`\n"]
            if mudancas:
                linhas += ["| Variável | Antes | Depois |", "| :--- | :--- | :--- |"]
                linhas += [f"| %{m['variavel']} | {m['antes'] or '(vazia)'} | {m['depois'] or '(apagada)'} |" for m in mudancas]
            else:
                linhas.append("Nenhuma variável muda em relação ao carimbo atual.")
            linhas.append("\n_O texto de %PECASDET é gravado como textos simples (o TQS usa um objeto IPOCOT); "
                          "o resultado plotado é o mesmo._")
            for a in avisos:
                linhas.append(f"\n⚠️ {a}")
            return "\n".join(linhas)

        if simular:
            base.update(status="simulado", sucesso=True, caminho_simulado=gerado["caminho"])
            base["resumo_executivo"] = resumo("🧪 Carimbo simulado (nada foi gravado no TQS)") + \
                f"\n\nCarimbo simulado: `{gerado['caminho']}`"
            return base
        if not aprovado:
            base.update(status="aguardando_aprovacao", sucesso=True)
            base["resumo_executivo"] = resumo("⚠️ Carimbo pronto para gravar — aguardando aprovação")
            return base

        backup = None
        if os.path.exists(destino):
            backup = f"{destino}_BKP_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(destino, backup)
        try:
            shutil.copy2(gerado["caminho"], destino)
            restantes = [t for t in cb._ler_textos(destino) if t[7].strip().startswith("%")]
            if restantes:
                raise ValueError(f"{len(restantes)} variáveis ficaram sem substituir")
        except Exception as e:
            if backup:
                shutil.copy2(backup, destino)
            return self._erro(f"Falha ao gravar o carimbo ({e}); o arquivo anterior foi mantido.", backup_criado=backup)
        base.update(status="sucesso", sucesso=True, backup_criado=backup)
        base["resumo_executivo"] = resumo(f"✅ Carimbo de {pl.id} preenchido") + \
            (f"\n\nBackup do carimbo anterior: `{backup}`" if backup else "")
        return base

    # ======================================================================
    # Plotar (PDF da revisão atual pelo motor de plotagem do TQS)
    # ======================================================================
    def _plotar(self, caminho_ed: str, pl: PlantaCPL, regras: RegrasNomenclatura,
                simular: bool, aprovado: bool, forcar: bool, avisos: List[str]) -> Dict[str, Any]:
        from src.skills.case_15_revisao_plantas.plotagem import plotar_prancha

        avisos = list(avisos)
        res = plotar_prancha(pl, regras, caminho_ed)
        nome = res["nome_saida"]
        destino_pdf = os.path.join(pl.pasta, nome + ".PDF")
        carimbo = res.get("carimbo")
        destino_cr = next((d.caminho_absoluto(pl.pasta) for d in pl.desenhos() if d.tipo == TIPO_CARIMBO), None)
        checagens = res["checagens"]
        tudo_ok = all(c["ok"] for c in checagens)

        gravar = [destino_pdf] + ([destino_cr] if carimbo and destino_cr else [])
        existentes = [g for g in gravar if os.path.exists(g)]
        if existentes:
            avisos.append("Será feito backup (_BKP_<data>) de: " + ", ".join(os.path.basename(e) for e in existentes) + ".")
        if pl.titulo_com_caractere_invalido:
            avisos.append("O título desta planta tem um caractere inválido gravado; corrija-o no Editor de Plantas.")

        base = {"acao": "plotar", "edificio": os.path.basename(caminho_ed), "prancha": pl.id,
                "revisao": regras.rotulo_revisao(res["numero"]), "pdf_gerado": res["pdf"],
                "pasta_trabalho": res["pasta_trabalho"], "destino_pdf": destino_pdf,
                "destino_carimbo": destino_cr if carimbo else None, "checagens": checagens, "avisos": avisos}

        def resumo(titulo: str) -> str:
            linhas = [f"### {titulo}\n", f"- **Prancha:** `{pl.id}` — revisão {base['revisao']}",
                      f"- **PDF gerado:** `{res['pdf']}`\n",
                      "| Item | OK | Detalhe |", "| :--- | :-: | :--- |"]
            linhas += [f"| {c['item']} | {'✅' if c['ok'] else '❌'} | {c['detalhe']} |" for c in checagens]
            linhas.append("\n**Arquivos no edifício:**")
            linhas += [f"- `{g}`" for g in gravar]
            for a in avisos:
                linhas.append(f"\n⚠️ {a}")
            return "\n".join(linhas)

        if simular:
            base.update(status="simulado", sucesso=True)
            base["resumo_executivo"] = resumo("🧪 Plotagem simulada (nada foi gravado no TQS)")
            return base
        if not tudo_ok and not forcar:
            base.update(status="divergente", sucesso=False,
                        erro="O PDF gerado não passou nas checagens; nada foi gravado (use forcar=True para gravar assim mesmo).")
            base["resumo_executivo"] = resumo("❌ PDF gerado com divergências — nada foi gravado")
            return base
        if not aprovado:
            base.update(status="aguardando_aprovacao", sucesso=True)
            base["resumo_executivo"] = resumo(f"⚠️ {nome}.PDF pronto para gravar em PLANTAS — aguardando aprovação")
            return base

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        copias = [(res["pdf"], destino_pdf)] + ([(carimbo["caminho"], destino_cr)] if carimbo and destino_cr else [])
        backups: Dict[str, str] = {}
        try:
            for origem, destino in copias:
                if os.path.exists(destino):
                    backups[destino] = f"{destino}_BKP_{ts}"
                    shutil.copy2(destino, backups[destino])
                shutil.copy2(origem, destino)
        except Exception as e:
            for destino, bkp in backups.items():
                shutil.copy2(bkp, destino)
            return self._erro(f"Falha ao gravar a plotagem ({e}); os arquivos anteriores foram mantidos.")
        base.update(status="sucesso", sucesso=True, backups=backups)
        base["resumo_executivo"] = resumo(f"✅ {nome}.PDF plotado e gravado em PLANTAS") + "".join(
            f"\n\nBackup: `{b}`" for b in backups.values())
        return base

    # ======================================================================
    # Conferir
    # ======================================================================
    def _conferir(self, pl: PlantaCPL, regras: RegrasNomenclatura, avisos: List[str]) -> Dict[str, Any]:
        rev = pl.ultima_revisao
        if rev is None:
            return self._erro(f"{pl.id} ainda não tem revisões registradas.")
        n = rev.numero
        nome_saida = regras.nome_arquivo_revisao(pl.id, n)
        pdf = localizar_saida_plotagem(pl.pasta, pl.id, n, regras, ".PDF")
        txt = localizar_saida_plotagem(pl.pasta, pl.id, n, regras, ".TXT")
        checagens = []

        def checar(nome: str, ok: bool, detalhe: str):
            checagens.append({"item": nome, "ok": bool(ok), "detalhe": detalhe})

        checar("PDF da plotagem", pdf is not None, pdf or f"{nome_saida}.PDF não encontrado em {pl.pasta}")
        # A prova de que a plotagem é posterior ao registro é o TXT trazer REVISAO=nn e a
        # descrição registrada (a data do .CPL não serve: o editor regrava o .CPL ao plotar).
        variaveis = ler_variaveis_plotagem(txt) if txt else {}
        if not txt and pdf:
            # Sem TXT (plotagem só em PDF, pelo editor ou pela skill): confere pelo conteúdo do PDF
            from src.skills.case_15_revisao_plantas.plotagem import verificar_pdf
            checagens.extend(verificar_pdf(pdf, pl, regras, n))
        else:
            checar("TXT de variáveis da plotagem", txt is not None, txt or f"{nome_saida}.TXT não encontrado")
        if txt:
            sufixo = f"{n:02d}"
            chave_dat = "REVISAO_DAT010" if n == 10 else f"REVISAO_DAT{sufixo}"
            checar("REVISAO no carimbo", variaveis.get("REVISAO") == sufixo, f"TXT: {variaveis.get('REVISAO')!r} / esperado {sufixo!r}")
            checar("Descrição na tabela", _norm(variaveis.get(f"REVISAO_TXT{sufixo}", "")) == _norm(rev.descricao),
                   variaveis.get(f"REVISAO_TXT{sufixo}", "(vazia)"))
            checar("Data na tabela", variaveis.get(chave_dat, "") == rev.data, variaveis.get(chave_dat, "(vazia)"))
            checar("Autor na tabela", _norm(variaveis.get(f"REVISAO_AUT{sufixo}", "")) == _norm(rev.autor),
                   variaveis.get(f"REVISAO_AUT{sufixo}", "(vazio)"))
            fase = decompor_id(pl.id, regras).fase
            esperada = nome_fase_esperado(pl.pasta, fase, regras, ignorar=txt)
            checar("Fase no carimbo (_FASE)", _norm(variaveis.get("_FASE", "")) == _norm(esperada),
                   f"TXT: {variaveis.get('_FASE', '(vazia)')!r} / esperado {esperada!r}")

        st = self._status_prancha(pl, regras)
        if st["alterados_apos_plotagem"]:
            avisos = avisos + [f"{', '.join(st['alterados_apos_plotagem'])} foi alterado depois da plotagem: "
                               "o PDF pode não refletir o desenho atual."]
        tudo_ok = all(c["ok"] for c in checagens)
        linhas = [f"### {'✅' if tudo_ok else '⚠️'} Conferência da plotagem {nome_saida}\n",
                  "| Item | OK | Detalhe |", "| :--- | :-: | :--- |"]
        for c in checagens:
            linhas.append(f"| {c['item']} | {'✅' if c['ok'] else '❌'} | {c['detalhe']} |")
        for a in avisos:
            linhas.append(f"\n⚠️ {a}")
        if tudo_ok and pdf:
            linhas.append(f"\nPDF para envio: `{pdf}`")
        return {"status": "sucesso" if tudo_ok else "divergente", "sucesso": tudo_ok, "acao": "conferir",
                "prancha": pl.id, "revisao": vars(rev), "pdf": pdf, "txt": txt, "checagens": checagens,
                "avisos": avisos, "resumo_executivo": "\n".join(linhas)}
