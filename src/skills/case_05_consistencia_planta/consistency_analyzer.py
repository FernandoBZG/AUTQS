import os
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional, Tuple

from src.tqs_adapter.building_reader import TQSBuildingReader
from src.tqs_adapter.building_processor import TQSBuildingProcessor
from src.tqs_adapter.pavimentos import filtrar_pavimentos, listar_pastas_pavimento, remover_acentos


_remover_acentos = remover_acentos  # compatibilidade com usos internos


@dataclass
class InconsistenciaItem:
    """Representa uma ocorrência de aviso ou erro de consistência estrutural do TQS."""
    elemento: str
    tipo: str  # 'sem_apoio', 'apoio_nulo', 'fora_do_pilar', 'balanco', 'interferencia', 'normativo', etc.
    severidade: str  # 'CRITICO', 'IMPORTANTE', 'NORMATIVO', 'INFORMATIVO'
    mensagem: str
    sugestao: str


@dataclass
class ConsistenciaPavimentoResultado:
    """Resultado da auditoria de consistência de um pavimento."""
    edificio: str
    pavimento: str
    caminho_pasta: str
    status: str  # 'consistente', 'com_avisos', 'inconsistente'
    duracao_segundos: float = 0.0
    desenho_formas_gerado: bool = False
    caminho_dwg: Optional[str] = None
    erros_extracao: Optional[str] = None
    itens: List[InconsistenciaItem] = field(default_factory=list)

    @property
    def total_erros_criticos(self) -> int:
        return sum(1 for it in self.itens if it.severidade == "CRITICO")

    @property
    def total_avisos_importantes(self) -> int:
        return sum(1 for it in self.itens if it.severidade == "IMPORTANTE")

    @property
    def total_avisos_normativos(self) -> int:
        return sum(1 for it in self.itens if it.severidade == "NORMATIVO")

    @property
    def total_informativos(self) -> int:
        return sum(1 for it in self.itens if it.severidade == "INFORMATIVO")

    def para_dict(self) -> Dict[str, Any]:
        return {
            "edificio": self.edificio,
            "pavimento": self.pavimento,
            "caminho_pasta": self.caminho_pasta,
            "status": self.status,
            "duracao_segundos": self.duracao_segundos,
            "desenho_formas_gerado": self.desenho_formas_gerado,
            "caminho_dwg": self.caminho_dwg,
            "erros_extracao": self.erros_extracao,
            "metricas": {
                "total_itens": len(self.itens),
                "erros_criticos": self.total_erros_criticos,
                "avisos_importantes": self.total_avisos_importantes,
                "avisos_normativos": self.total_avisos_normativos,
                "informativos": self.total_informativos,
            },
            "itens": [asdict(it) for it in self.itens],
        }

    def para_resumo_executivo(self) -> str:
        """Gera resumo compacto para respostas de chat / LLM pouparem tokens."""
        icones = {
            "consistente": "✅ CONSISTENTE",
            "com_avisos": "⚠️ CONSISTENTE COM AVISOS",
            "inconsistente": "❌ INCONSISTENTE (ERROS CRÍTICOS)",
        }
        linhas = [
            f"Relatório de Consistência TQS - Pavimento: {self.pavimento}",
            f"Status: {icones.get(self.status, self.status)} | Edifício: {self.edificio}",
            f"Métricas: {self.total_erros_criticos} erros críticos, {self.total_avisos_importantes} avisos de apoio/eixo, {self.total_avisos_normativos} alertas normativos.",
        ]

        if self.erros_extracao:
            linhas.append(f"\n[ERRO CRÍTICO DE EXTRAÇÃO]: {self.erros_extracao[:250]}")

        criticos = [it for it in self.itens if it.severidade == "CRITICO"]
        if criticos:
            linhas.append("\nErros Bloqueantes:")
            for it in criticos[:5]:
                linhas.append(f"  • [{it.elemento}] {it.mensagem} -> Sugestão: {it.sugestao}")

        importantes = [it for it in self.itens if it.severidade == "IMPORTANTE"]
        if importantes:
            linhas.append("\nAvisos Importantes de Modelagem:")
            for it in importantes[:8]:
                linhas.append(f"  • [{it.elemento}] {it.mensagem} -> {it.sugestao}")

        if len(self.itens) > 13:
            linhas.append(f"  ... e mais {len(self.itens) - 13} avisos secundários registrados no TQS.")

        if self.desenho_formas_gerado and self.caminho_dwg:
            linhas.append(f"\nPlanta de Formas gerada: {os.path.basename(self.caminho_dwg)}")

        return "\n".join(linhas)

    def para_tabela_terminal(self) -> str:
        """Gera tabela formatada para o terminal do engenheiro."""
        linhas = [
            "\n" + "=" * 78,
            f"   AUDITORIA DE CONSISTÊNCIA DE FORMAS TQS: {self.pavimento.upper()}",
            "=" * 78,
            f"Edifício:   {self.edificio}",
            f"Pasta:      {self.caminho_pasta}",
            f"Status:     {self.status.upper()}",
            f"Diagnóstico: {self.total_erros_criticos} Críticos | {self.total_avisos_importantes} Importantes | {self.total_avisos_normativos} Normativos | {self.total_informativos} Informativos",
            "-" * 78,
        ]

        if self.erros_extracao:
            linhas.append(f"❌ ERRO CRÍTICO NA EXTRAÇÃO GRÁFICA DO TQS:")
            linhas.append(f"   {self.erros_extracao}\n")

        if not self.itens:
            linhas.append("✅ Nenhuma inconsistência detectada! O modelo atende integralmente às regras do TQS.")
        else:
            linhas.append(f"{'Severidade':<12} | {'Elemento':<12} | {'Mensagem / Diagnóstico':<50}")
            linhas.append("-" * 78)
            for it in self.itens[:25]:
                sev = it.severidade
                linhas.append(f"{sev:<12} | {it.elemento:<12} | {it.mensagem[:48]}")
                linhas.append(f"{'':<12} | {'-> Sugestão:':<12} | {it.sugestao[:48]}")
                linhas.append("-" * 78)

            if len(self.itens) > 25:
                linhas.append(f"  [+] {len(self.itens) - 25} outros avisos listados no relatório oficial TQS.")

        if self.desenho_formas_gerado and self.caminho_dwg:
            linhas.append(f"\nDesenho gerado: {self.caminho_dwg}")
        linhas.append("=" * 78 + "\n")
        return "\n".join(linhas)


class TQSConsistencyAnalyzer:
    """
    Auditor inteligente de consistência de plantas de formas no CAD/TQS V25.
    Dispara o motor de verificação de formas (FXEXTME, FXFORMAS, FDESFOR) e
    processa relatórios MENAVI.LST, *.LST, ERROS.DAT e ERROS.TXT para identificar:
      - Vigas sem apoio / apoios nulos (iniciais e finais)
      - Eixos de vigas que não caem sobre a seção dos pilares
      - Interferências entre apoios adjacentes
      - Barras em balanço imprevistas
      - Incompatibilidades de discretização de lajes
      - Alertas de estabilidade lateral de vigas (NBR 6118 item 15.10)
    """

    def __init__(self, caminho_ou_nome_edificio: str, pasta_raiz_tqs: Optional[str] = None):
        leitor = TQSBuildingReader(caminho_ou_nome_edificio, pasta_raiz_tqs or r"C:\TQS")
        self.caminho_edificio = leitor.caminho_edificio
        self.nome_edificio = leitor.nome_edificio
        self.pasta_raiz = os.path.dirname(self.caminho_edificio)

    def listar_pavimentos_disponiveis(self) -> List[Tuple[str, str]]:
        """
        Retorna lista de tuplas (nome_pasta, caminho_completo) de pavimentos
        estruturais válidos do edifício (excluindo pastas técnicas e de backup).
        """
        pastas = []
        for item, p in listar_pastas_pavimento(self.caminho_edificio):
            # Verifica se possui indícios de pavimento estrutural
            tem_ldf = any(f.endswith(".LDF") for f in os.listdir(p))
            tem_dat = os.path.exists(os.path.join(p, "EDIFICIO.DAT"))
            tem_lst = os.path.exists(os.path.join(p, "MENAVI.LST"))
            if tem_ldf or tem_dat or tem_lst:
                pastas.append((item, p))

        return pastas

    def localizar_pasta_pavimento(self, filtro_pavimento: Optional[str] = None) -> List[Tuple[str, str]]:
        """
        Pasta(s) de pavimento que correspondem ao filtro do usuário (ver
        tqs_adapter.pavimentos.filtrar_pavimentos). Sem correspondência devolve lista vazia.
        """
        return filtrar_pavimentos(self.listar_pavimentos_disponiveis(), filtro_pavimento)

    def analisar(
        self,
        pavimento: Optional[str] = None,
        executar_tqs: bool = True,
        desenhar_formas: bool = True,
        timeout_segundos: int = 240,
    ) -> List[ConsistenciaPavimentoResultado]:
        """
        Executa a verificação e retorna os resultados estruturados de consistência.
        :param pavimento: Nome ou código do pavimento (ex: 'terreo', '2', None para todos).
        :param executar_tqs: Se True, dispara 'PROC FORMAS 2 1' no TQS para recalcular.
        :param desenhar_formas: Se True, emite desenho de formas FOR00xx.DWG.
        :param timeout_segundos: Limite de execução do processo em lote do TQS.
        """
        pavimentos_alvo = self.localizar_pasta_pavimento(pavimento)
        if not pavimentos_alvo:
            # Filtro sem correspondência: não processa nada (antes caía em "todos os pavimentos")
            return []

        duracao = 0.0
        erros_extracao_global = None

        if executar_tqs:
            try:
                proc = TQSBuildingProcessor(self.caminho_edificio, self.pasta_raiz)
                # Se for um único pavimento específico, pode passar o nome para o TQS
                nome_pav_tqs = pavimentos_alvo[0][0] if len(pavimentos_alvo) == 1 else None
                res_proc = proc.verificar_consistencia_formas(
                    pavimento=nome_pav_tqs,
                    desenhar_formas=desenhar_formas,
                    timeout_segundos=timeout_segundos
                )
                duracao = res_proc.get("duracao_segundos", 0.0)
                if res_proc.get("erros_extracao"):
                    erros_extracao_global = res_proc.get("erros_extracao")
            except Exception as e:
                erros_extracao_global = f"Erro ao acionar motor TQS: {str(e)}"

        resultados = []
        for nome_pav, caminho_pav in pavimentos_alvo:
            res_pav = self._analisar_pasta_pavimento(nome_pav, caminho_pav, duracao, erros_extracao_global)
            resultados.append(res_pav)

        return resultados

    def _analisar_pasta_pavimento(
        self,
        nome_pav: str,
        caminho_pav: str,
        duracao: float,
        erros_extracao: Optional[str]
    ) -> ConsistenciaPavimentoResultado:
        """Processa e consolida as listagens de consistência de uma pasta de pavimento."""
        itens: List[InconsistenciaItem] = []
        visto = set()

        # 1. Parser do MENAVI.LST (Avisos de Modelagem)
        menavi_path = os.path.join(caminho_pav, "MENAVI.LST")
        if os.path.exists(menavi_path):
            with open(menavi_path, "r", encoding="latin-1", errors="ignore") as f:
                for line in f:
                    item = self._interpretar_linha_menavi(line.strip())
                    if item:
                        chave = (item.elemento, item.tipo, item.mensagem)
                        if chave not in visto:
                            visto.add(chave)
                            itens.append(item)

        # 2. Parser do relatório detalhado do pavimento (*.LST)
        for arq in os.listdir(caminho_pav):
            if arq.endswith(".LST") and not arq.startswith("GRE") and arq != "MENAVI.LST" and arq != "PORLAJ.LST":
                p_rel = os.path.join(caminho_pav, arq)
                self._complementar_com_relatorio_pavimento(p_rel, itens, visto)

        # 3. Verifica existência de desenho de formas FOR*.DWG
        caminho_dwg = None
        desenho_ok = False
        for f in os.listdir(caminho_pav):
            if f.upper().startswith("FOR") and f.upper().endswith(".DWG"):
                caminho_dwg = os.path.join(caminho_pav, f)
                desenho_ok = os.path.getsize(caminho_dwg) > 1024
                break

        # 4. Avalia erros de extração específicos do pavimento
        err_txt_pav = None
        if erros_extracao and nome_pav in erros_extracao:
            err_txt_pav = erros_extracao
            itens.insert(0, InconsistenciaItem(
                elemento="Pavimento",
                tipo="extracao_invalida",
                severidade="CRITICO",
                mensagem=f"Falha de extração gráfica: {erros_extracao[:120]}...",
                sugestao="Corrija cruzamentos de vigas ou geometria inválida no Modelador Estrutural."
            ))

        # 5. Define status global
        tem_criticos = any(it.severidade == "CRITICO" for it in itens) or (err_txt_pav is not None)
        tem_importantes = any(it.severidade in ["IMPORTANTE", "NORMATIVO"] for it in itens)

        if tem_criticos:
            status = "inconsistente"
        elif tem_importantes:
            status = "com_avisos"
        else:
            status = "consistente"

        return ConsistenciaPavimentoResultado(
            edificio=self.nome_edificio,
            pavimento=nome_pav,
            caminho_pasta=caminho_pav,
            status=status,
            duracao_segundos=duracao,
            desenho_formas_gerado=desenho_ok,
            caminho_dwg=caminho_dwg,
            erros_extracao=err_txt_pav,
            itens=itens
        )

    def _interpretar_linha_menavi(self, line: str) -> Optional[InconsistenciaItem]:
        """Interpreta e categoriza uma linha do arquivo MENAVI.LST."""
        m = re.match(r"^\*{3}\d+\s+(AVISO|ERRO):\s*(.+)$", line, re.IGNORECASE)
        if not m:
            return None

        tipo_orig, texto = m.groups()
        texto_limpo = " ".join(texto.split())

        def _extrair_nome_viga(t: str) -> str:
            mv = re.search(r"viga\s+(?:v\s*)?([0-9]+|[A-Za-z0-9]+)", t, re.IGNORECASE)
            return f"Viga {mv.group(1)}" if mv else "Viga"

        # Viga sem apoios (CRÍTICO)
        if "sem apoio" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="sem_apoio",
                severidade="CRITICO",
                mensagem=texto_limpo,
                sugestao=f"Defina apoios (pilares ou vigas principais) nas extremidades da {elem} para evitar mecanismo estrutural."
            )

        # Apoio nulo (inicial ou final)
        if "apoio" in texto_limpo.lower() and "nulo" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="apoio_nulo",
                severidade="IMPORTANTE",
                mensagem=texto_limpo,
                sugestao=f"Realinhe o nó de apoio da {elem} com o eixo do pilar ou verifique a vinculação estrutural."
            )

        # Nó não cai sobre o pilar
        if "não cai sobre o pilar" in texto_limpo.lower() or "nao cai sobre o pilar" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            m_pil = re.search(r"pilar\s+(?:p\s*)?([0-9]+|[A-Za-z0-9]+)", texto_limpo, re.IGNORECASE)
            pil_str = f"P{m_pil.group(1)}" if m_pil else "pilar"
            return InconsistenciaItem(
                elemento=elem,
                tipo="fora_do_pilar",
                severidade="IMPORTANTE",
                mensagem=texto_limpo,
                sugestao=f"Ajuste as coordenadas do nó da {elem} para que recaia dentro da seção de concreto do {pil_str}."
            )

        # Barra em balanço indesejada
        if "balanço" in texto_limpo.lower() or "balanco" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="balanco",
                severidade="IMPORTANTE",
                mensagem=texto_limpo,
                sugestao=f"Verifique se o balanço é intencional ou se decorre de nó de apoio que não interceptou a viga."
            )

        # Interferência entre apoios
        if "interferência entre apoios" in texto_limpo.lower() or "interferencia entre apoios" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="interferencia",
                severidade="IMPORTANTE",
                mensagem=texto_limpo,
                sugestao=f"Ajuste a distância mínima entre apoios contíguos na {elem} ou unifique os nós na geometria."
            )

        # Nó posicionado após centro do apoio
        if "após centro do apoio" in texto_limpo.lower() or "apos centro do apoio" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="no_apos_centro",
                severidade="IMPORTANTE",
                mensagem=texto_limpo,
                sugestao=f"Reposicione o nó para o centro do apoio para não distorcer a distribuição de reações e momentos."
            )

        # Norma NBR-6118 / Instabilidade lateral de vigas (item 15.10)
        if "item 15.10 da nbr-6118" in texto_limpo.lower() or "largura" in texto_limpo.lower() and "menor que" in texto_limpo.lower():
            elem = _extrair_nome_viga(texto_limpo)
            return InconsistenciaItem(
                elemento=elem,
                tipo="normativo",
                severidade="NORMATIVO",
                mensagem=texto_limpo,
                sugestao="Aumente a largura da viga ou garanta travamento lateral por laje conforme NBR 6118 item 15.10."
            )

        # Discretização de laje (DISEIX/DISCIN)
        if "diseix" in texto_limpo.lower() or "discin" in texto_limpo.lower():
            m_laj = re.search(r"laje\s+(\d+)", texto_limpo, re.IGNORECASE)
            elem = f"Laje {m_laj.group(1)}" if m_laj else "Laje"
            return InconsistenciaItem(
                elemento=elem,
                tipo="laje_discretizacao",
                severidade="INFORMATIVO",
                mensagem=texto_limpo,
                sugestao="Verifique continuidade dos eixos e bordos de vigas em torno da laje."
            )

        # Ausência de cargas de alvenaria
        if "não há cargas de alvenaria" in texto_limpo.lower() or "nao ha cargas de alvenaria" in texto_limpo.lower():
            m_viga = re.search(r"viga\s+(\d+)", texto_limpo, re.IGNORECASE)
            elem = f"Viga {m_viga.group(1)}" if m_viga else "Viga"
            return InconsistenciaItem(
                elemento=elem,
                tipo="carga_alvenaria",
                severidade="INFORMATIVO",
                mensagem=texto_limpo,
                sugestao="Verifique se a viga suporta parede e precisa de carregamento linear atribuído."
            )

        # Informativos padrão (peso próprio, etc.)
        if "peso próprio" in texto_limpo.lower() or "peso proprio" in texto_limpo.lower():
            return InconsistenciaItem(
                elemento="Geral",
                tipo="peso_proprio",
                severidade="INFORMATIVO",
                mensagem=texto_limpo,
                sugestao="Informativo de combinações de carregamento do TQS."
            )

        # Outros avisos
        return InconsistenciaItem(
            elemento="Modelo",
            tipo="outro",
            severidade="IMPORTANTE" if tipo_orig.upper() == "ERRO" else "INFORMATIVO",
            mensagem=texto_limpo,
            sugestao="Consulte o menu Visualizar > Relatórios no Gerenciador TQS."
        )

    def _complementar_com_relatorio_pavimento(self, caminho_lst: str, itens: List[InconsistenciaItem], visto: set):
        """Varre o relatório do pavimento em busca de erros não capturados no MENAVI."""
        try:
            with open(caminho_lst, "r", encoding="latin-1", errors="ignore") as f:
                for line in f:
                    line_s = line.strip()
                    if "ERRO:" in line_s.upper() or "INCONSIST" in line_s.upper():
                        msg_limpa = " ".join(line_s.split())
                        chave = ("Pavimento", "relatorio_lst", msg_limpa)
                        if chave not in visto:
                            visto.add(chave)
                            itens.append(InconsistenciaItem(
                                elemento="Pavimento",
                                tipo="relatorio_lst",
                                severidade="CRITICO" if "ERRO:" in line_s.upper() else "IMPORTANTE",
                                mensagem=msg_limpa[:150],
                                sugestao="Verifique a consistência do pavimento no Modelador Estrutural."
                            ))
        except Exception:
            pass
