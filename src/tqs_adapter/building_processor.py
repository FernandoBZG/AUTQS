import os
import re
import sys
import time
import subprocess
from typing import Dict, Any, Optional, List
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.tqs_adapter.building_reader import TQSBuildingReader

# O TQS.EXE -RLST retorna código 0 mesmo quando uma tarefa do GERENCIADOR.DAT falha
# (ex.: "-CMD: Erro executando [PORLID]"), e essa mensagem nem sempre chega ao stdout.
# Por isso a confirmação de cada tarefa é feita pelos artefatos que ela deveria gravar.
_RE_ERRO_TQS = re.compile(r"Erro executando\s*\[([^\]]+)\]", re.IGNORECASE)
_TOLERANCIA_MTIME_S = 2.0


def extrair_erros_tqs(*textos: Optional[str]) -> List[str]:
    """Retorna os nomes das tarefas reportadas como 'Erro executando [X]' na saída do TQS."""
    erros: List[str] = []
    for texto in textos:
        for nome in _RE_ERRO_TQS.findall(texto or ""):
            nome = nome.strip()
            if nome and nome not in erros:
                erros.append(nome)
    return erros


def arquivo_atualizado(caminho: str, desde: float, exigir_conteudo: bool = False) -> bool:
    """True se o arquivo existe e foi gravado a partir de `desde` (epoch), opcionalmente não-vazio."""
    try:
        st = os.stat(caminho)
    except OSError:
        return False
    if st.st_mtime < desde - _TOLERANCIA_MTIME_S:
        return False
    return st.st_size > 0 if exigir_conteudo else True


def verificar_artefatos(caminho_edificio: str, artefatos: Dict[str, List[str]], desde: float) -> List[str]:
    """
    Para cada tarefa, exige que ao menos um dos arquivos esperados (caminhos relativos ao
    edifício) tenha sido gravado durante o processamento. Retorna as tarefas não confirmadas.
    """
    falhas = []
    for tarefa, arquivos in artefatos.items():
        if not any(arquivo_atualizado(os.path.join(caminho_edificio, a), desde) for a in arquivos):
            falhas.append(tarefa)
    return falhas


def verificar_vigas_dimensionadas(caminho_edificio: str, desde: float) -> List[str]:
    """
    Retorna os pavimentos cujas vigas foram processadas nesta execução (ORDCON.LST regravado)
    mas cujo relatório de dimensionamento VIGAS/RELGER.LST ficou vazio ou não foi regravado.
    """
    pavimentos_sem_relger = []
    try:
        entradas = sorted(os.listdir(caminho_edificio))
    except OSError:
        return pavimentos_sem_relger
    for nome in entradas:
        pasta_vigas = os.path.join(caminho_edificio, nome, "VIGAS")
        if not os.path.isdir(pasta_vigas):
            continue
        if not arquivo_atualizado(os.path.join(pasta_vigas, "ORDCON.LST"), desde):
            continue
        if not arquivo_atualizado(os.path.join(pasta_vigas, "RELGER.LST"), desde, exigir_conteudo=True):
            pavimentos_sem_relger.append(nome)
    return pavimentos_sem_relger


class TQSBuildingProcessor:
    """
    Controlador de automação em batch do motor de cálculo do TQS V25 (TQSExec).
    Permite disparar e monitorar o processamento de formas, grelhas,
    pórtico espacial 3D e extração de cargas das fundações (PORLID).
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        prog, sup, usr = configurar_ambiente_tqs_64()
        self.pasta_programas = prog
        self.pasta_suporte = sup
        self.pasta_usuario = usr
        self.tqs_exe = os.path.join(prog, "TQS.EXE")

        if not os.path.exists(self.tqs_exe):
            raise FileNotFoundError(f"Executável TQS.EXE não encontrado em: {self.tqs_exe}")

        # Localiza o edifício
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio
        self.pasta_raiz = os.path.dirname(self.caminho_edificio)

    def processar_portico_e_cargas(
        self,
        extrair_formas: bool = True,
        calcular_grelhas: bool = True,
        calcular_portico: bool = True,
        gerar_porlid: bool = True,
        timeout_segundos: int = 300,
    ) -> Dict[str, Any]:
        """
        Executa o pipeline essencial para cálculo das reações estruturais:
          1. Extração e processamento de formas a partir do Modelador
          2. Geração e análise de esforços de grelhas
          3. Montagem e resolução da matriz do Pórtico Espacial 3D
          4. Transferência de esforços para pilares e fundações
          5. Extração oficial do relatório de cargas PORLID
        """
        f_plan = 2 if extrair_formas else 0
        g_model = 1 if calcular_grelhas else 0
        g_anal = 1 if calcular_grelhas else 0
        p_model = 1 if calcular_portico else 0
        p_anal = 1 if calcular_portico else 0

        # Monta os comandos da DSL do Gerenciador TQS
        # PROC FORMAS <floorPlan> <floorDraw> LAJES <slabs> VIGAS <beams>
        #      PILARES <colData> <colDim> <colRep>
        #      GRELHAS <model> <draw> <extr> <analysis> <beamsTrnsf> <slabsTrnsf> <nonLinear>
        #      PORTICO <model> <analysis> <beamsTrnsf> <columnsTrnsf> FUNDAC <foundations>
        proc_cmd = (
            f"PROC FORMAS {f_plan} 0 LAJES 0 VIGAS 1 PILARES 1 0 1 "
            f"GRELHAS {g_model} 0 1 {g_anal} 0 1 0 "
            f"PORTICO {p_model} {p_anal} 1 1 FUNDAC 0"
        )

        tarefas = [
            f"ARVORE '{self.pasta_raiz}'",
            f"EDIFICIO '{self.nome_edificio}' ESPACIAL",
            proc_cmd,
        ]

        artefatos: Dict[str, List[str]] = {}
        if calcular_portico:
            artefatos["PROC (pórtico espacial)"] = [r"ESPACIAL\CARDWG2.LST", r"ESPACIAL\CARDWG.LST"]

        if gerar_porlid:
            tarefas.append("PORLID")
            artefatos["PORLID"] = [r"ESPACIAL\PORLID.DWG"]

        return self._executar_batch(
            tarefas,
            timeout_segundos=timeout_segundos,
            descricao="Pórtico Espacial e Cargas",
            artefatos_esperados=artefatos,
        )

    def processar_global_completo(
        self,
        dimensionar_vigas: bool = True,
        dimensionar_pilares: bool = True,
        dimensionar_fundacoes: bool = False,
        timeout_segundos: int = 600,
    ) -> Dict[str, Any]:
        """
        Executa o Processamento Global Completo do TQS:
          - Formas, Lajes, Vigas (com dimensionamento/detalhamento),
          - Pilares (dados, dimensionamento e relatório),
          - Grelhas de pavimentos, Pórtico Espacial 3D, Fundações e PORLID.
        """
        beams_flag = 2 if dimensionar_vigas else 1
        cols_flag = 1 if dimensionar_pilares else 0
        fund_flag = 1 if dimensionar_fundacoes else 0

        proc_cmd = (
            f"PROC FORMAS 2 0 LAJES 1 VIGAS {beams_flag} PILARES 1 {cols_flag} 1 "
            f"GRELHAS 1 0 1 1 0 1 0 "
            f"PORTICO 1 1 1 1 FUNDAC {fund_flag}"
        )

        tarefas = [
            f"ARVORE '{self.pasta_raiz}'",
            f"EDIFICIO '{self.nome_edificio}' ESPACIAL",
            proc_cmd,
            "PORLID",
            "RESEST",
        ]

        artefatos: Dict[str, List[str]] = {
            "PROC (pórtico espacial)": [r"ESPACIAL\CARDWG2.LST", r"ESPACIAL\CARDWG.LST"],
        }
        if dimensionar_pilares:
            artefatos["PROC (dimensionamento de pilares)"] = [r"PILAR\SELEC.LST"]
        artefatos["PORLID"] = [r"ESPACIAL\PORLID.DWG"]
        artefatos["RESEST"] = [rf"ESPACIAL\RESEST{i}.TXT" for i in range(1, 9)]

        return self._executar_batch(
            tarefas,
            timeout_segundos=timeout_segundos,
            descricao="Processamento Global Completo",
            artefatos_esperados=artefatos,
            verificar_vigas=dimensionar_vigas,
        )

    def verificar_consistencia_formas(
        self,
        pavimento: Optional[str] = None,
        desenhar_formas: bool = True,
        timeout_segundos: int = 240,
    ) -> Dict[str, Any]:
        """
        Executa a extração e verificação de consistência da planta de formas no TQS:
          1. Extração gráfica de formas do modelador estrutural (FXEXTME/FEXTDWG)
          2. Compilação e checagem de consistência geométrica e vinculações (FXFORMAS)
          3. Emissão dos relatórios de modelagem (MENAVI.LST, *.LST, ERROS.DAT)
          4. Geração do desenho de formas (FOR00xx.DWG) se desenhar_formas=True
        """
        f_draw = 1 if desenhar_formas else 0
        proc_cmd = f"PROC FORMAS 2 {f_draw}"

        pasta_alvo = f"'{pavimento}'" if pavimento else "ESPACIAL"
        tarefas = [
            f"ARVORE '{self.pasta_raiz}'",
            f"EDIFICIO '{self.nome_edificio}' {pasta_alvo}",
            proc_cmd,
        ]

        # Limpa ERROS.TXT antigo na raiz do edifício para evitar falsos positivos
        err_txt = os.path.join(self.caminho_edificio, "ERROS.TXT")
        if os.path.exists(err_txt):
            try:
                os.remove(err_txt)
            except Exception:
                pass

        res = self._executar_batch(
            tarefas,
            timeout_segundos=timeout_segundos,
            descricao="Consistência de Formas",
            exigir_cargas=False
        )

        if os.path.exists(err_txt):
            try:
                with open(err_txt, "r", encoding="latin-1", errors="ignore") as f:
                    txt = f.read().strip()
                    if txt:
                        res["erros_extracao"] = txt
                        res["sucesso"] = False
                        res["status"] = "erro"
            except Exception:
                pass

        return res

    def _executar_batch(
        self,
        tarefas: List[str],
        timeout_segundos: int,
        descricao: str,
        exigir_cargas: bool = True,
        artefatos_esperados: Optional[Dict[str, List[str]]] = None,
        verificar_vigas: bool = False,
    ) -> Dict[str, Any]:
        """
        Serializa o script GERENCIADOR.DAT na pasta da obra e invoca TQS.EXE -RLST.

        :param artefatos_esperados: {tarefa: [arquivos relativos ao edifício]}; a tarefa só é
            considerada executada se ao menos um desses arquivos for gravado durante o lote.
        :param verificar_vigas: exige RELGER.LST não-vazio nos pavimentos cujas vigas foram processadas.
        """
        inicio = time.time()
        caminho_dat = os.path.join(self.caminho_edificio, "GERENCIADOR.DAT")

        conteudo_script = "\n".join(tarefas) + "\n"
        with open(caminho_dat, "w", encoding="latin-1") as f:
            f.write(conteudo_script)

        # Também grava no CWD para compatibilidade com versões do TQS que leem do CWD
        cwd_dat = os.path.abspath("GERENCIADOR.DAT")
        try:
            with open(cwd_dat, "w", encoding="latin-1") as f:
                f.write(conteudo_script)
        except Exception:
            pass

        comando = f'"{self.tqs_exe}" -RLST -CMD:GERENCIADOR.DAT'
        
        try:
            # Executa com cwd na pasta do edifício
            proc = subprocess.run(
                comando,
                cwd=self.caminho_edificio,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout_segundos,
            )
            duracao = round(time.time() - inicio, 1)

            # Verifica arquivos de resultados gerados na pasta ESPACIAL
            pasta_espacial = os.path.join(self.caminho_edificio, "ESPACIAL")
            tem_porlis = os.path.exists(os.path.join(pasta_espacial, "PORLIS2.LST")) or os.path.exists(os.path.join(pasta_espacial, "PORLIS.LST"))
            tem_cardwg = os.path.exists(os.path.join(pasta_espacial, "CARDWG2.LST")) or os.path.exists(os.path.join(pasta_espacial, "CARDWG.LST"))

            # Lê alertas ou mensagens de erro do TQS se houver
            mensagens = []
            for arq_msg in ["MENAVI.LST", "JANMSG.LST", "RESESTERR.LST"]:
                p_msg = os.path.join(pasta_espacial, arq_msg)
                if os.path.exists(p_msg):
                    try:
                        with open(p_msg, "r", encoding="latin-1", errors="ignore") as f:
                            conteudo = [l.strip() for l in f.readlines() if l.strip()]
                            if conteudo:
                                mensagens.extend(conteudo[-10:])
                    except Exception:
                        pass

            if exigir_cargas:
                sucesso = (proc.returncode == 0) and tem_cardwg and tem_porlis
            else:
                sucesso = (proc.returncode == 0)

            # Confirmação por tarefa: o código de retorno do TQS não reflete falhas internas.
            reportadas = {
                t.upper() for t in extrair_erros_tqs(proc.stdout, proc.stderr) if t.upper() != "GERENCIADOR.DAT"
            }
            tarefas_com_falha = [f"{t} (reportado pelo TQS)" for t in sorted(reportadas)]
            for t in verificar_artefatos(self.caminho_edificio, artefatos_esperados or {}, inicio):
                if t.split(" ")[0].upper() not in reportadas:
                    tarefas_com_falha.append(f"{t} (saída não gravada)")
            pavimentos_sem_vigas = (
                verificar_vigas_dimensionadas(self.caminho_edificio, inicio) if verificar_vigas else []
            )

            erro_msg = None
            if tarefas_com_falha or pavimentos_sem_vigas:
                sucesso = False
                partes = []
                if tarefas_com_falha:
                    partes.append("tarefas sem confirmação: " + ", ".join(tarefas_com_falha))
                if pavimentos_sem_vigas:
                    partes.append("vigas não dimensionadas (RELGER.LST vazio) em: " + ", ".join(pavimentos_sem_vigas))
                erro_msg = "Processamento incompleto - " + "; ".join(partes)

            if erro_msg:
                status = "erro"
            else:
                status = "sucesso" if sucesso else "aviso"

            return {
                "status": status,
                "sucesso": sucesso,
                "erro": erro_msg,
                "tarefas_com_falha": tarefas_com_falha,
                "pavimentos_sem_vigas_dimensionadas": pavimentos_sem_vigas,
                "edificio": self.nome_edificio,
                "caminho_edificio": self.caminho_edificio,
                "tipo_processamento": descricao,
                "duracao_segundos": duracao,
                "codigo_retorno": proc.returncode,
                "tem_porlis": tem_porlis,
                "tem_cardwg": tem_cardwg,
                "mensagens": mensagens[:15],
                "stdout": proc.stdout,
                "stderr": proc.stderr,
            }

        except subprocess.TimeoutExpired:
            duracao = round(time.time() - inicio, 1)
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": self.nome_edificio,
                "erro": f"Tempo limite de processamento ({timeout_segundos}s) excedido.",
                "duracao_segundos": duracao,
            }
        except Exception as e:
            duracao = round(time.time() - inicio, 1)
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": self.nome_edificio,
                "erro": str(e),
                "duracao_segundos": duracao,
            }
        finally:
            # Limpeza de scripts temporários
            for p in [caminho_dat, cwd_dat]:
                if os.path.exists(p):
                    try:
                        os.remove(p)
                    except Exception:
                        pass
