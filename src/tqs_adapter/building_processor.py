import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional, List
from src.tqs_adapter.tqs_env import configurar_ambiente_tqs_64
from src.tqs_adapter.building_reader import TQSBuildingReader

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

        if gerar_porlid:
            tarefas.append("PORLID")

        return self._executar_batch(tarefas, timeout_segundos=timeout_segundos, descricao="Pórtico Espacial e Cargas")

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

        return self._executar_batch(tarefas, timeout_segundos=timeout_segundos, descricao="Processamento Global Completo")

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
        exigir_cargas: bool = True
    ) -> Dict[str, Any]:
        """
        Serializa o script GERENCIADOR.DAT na pasta da obra e invoca TQS.EXE -RLST.
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

            return {
                "status": "sucesso" if sucesso else "aviso",
                "sucesso": sucesso,
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
