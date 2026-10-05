import os
import re
from typing import Dict, Any, List, Optional
from src.agent.orchestrator import AutqsAgentOrchestrator
from src.tqs_adapter.building_reader import TQSBuildingReader
from src.agent.gemini_client import GeminiClient

class AutqsChatAgent:
    """
    Agente de Conversação Inteligente para Engenharia Estrutural e TQS V25.
    Processa mensagens em linguagem natural, executa habilidades estruturais,
    inspeciona e modifica elementos no Modelador Estrutural (Vigas, Lajes, Pilares e Cargas),
    faz análises estatísticas dos esforços e integra opcionalmente ao Google Gemini.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.orchestrator = AutqsAgentOrchestrator()
        self.gemini_client = GeminiClient(api_key=api_key)
        self.edificio_ativo: Optional[str] = "054"
        self.ultima_planta: Optional[Any] = None

    def set_api_key(self, api_key: str):
        self.gemini_client = GeminiClient(api_key=api_key)

    def responder(self, mensagem_usuario: str) -> Dict[str, Any]:
        """
        Processa a mensagem do usuário e retorna uma resposta estruturada contendo:
        - texto: Mensagem explicativa formatada em Markdown
        - dados: Tabela ou lista de pilares (se aplicável)
        - arquivo_dwg: Caminho do DWG gerado (se houver)
        - alerta: Avisos estruturais (ex: tração, excentricidade excessiva)
        - tipo: 'texto', 'planta_gerada', 'listagem_edificios', 'analise_pilares', 'edicao_modelo', 'listagem_modelo'
        """
        msg = mensagem_usuario.strip()
        msg_lower = msg.lower()

        # 1. Troca ou especificação de edifício (por código numérico ou por nome)
        num_match = re.search(r'\b(0\d{2}|\d{3,4})\b', msg)
        edificios_disponiveis = TQSBuildingReader.listar_edificios_disponiveis()
        if num_match:
            candidato = num_match.group(1)
            for ed in edificios_disponiveis:
                if candidato in ed["nome"]:
                    self.edificio_ativo = candidato
                    break
        else:
            for ed in edificios_disponiveis:
                tokens = [w for w in re.split(r'[\s\-_\[\]]+', ed["nome"].lower()) if len(w) > 3]
                if any(t in msg_lower for t in tokens):
                    self.edificio_ativo = ed["nome"]
                    break

        from src.tqs_adapter.model_editor import normalizar_texto
        msg_norm = normalizar_texto(msg)

        # 2. Pergunta sobre edifícios disponíveis
        if any(k in msg_norm for k in ["QUAI", "LIST", "MOSTR", "EXIB"]) and any(k in msg_norm for k in ["EDIF", "PROJET", "OBRA"]) and not any(k in msg_norm for k in ["PAVIMENT", "PISO", "VIGA", "LAJE", "PILAR", "CARGA"]):
            edificios = TQSBuildingReader.listar_edificios_disponiveis()
            linhas = ["### 🏢 Edifícios Detectados no Sistema TQS:\n"]
            for e in edificios:
                status = "✅ **Pronto para Emissão (Pórtico OK)**" if e["processado"] else "⚠️ *Requer Processamento no TQS*"
                linhas.append(f"- **{e['nome']}**\n  - Status: {status}\n  - Pasta: `{e['caminho']}`")
            
            linhas.append("\n*Para operar um edifício, digite por exemplo:* `Mudar para edifício 054` ou `Gere a planta de cargas`")
            return {
                "tipo": "listagem_edificios",
                "texto": "\n".join(linhas),
                "dados": edificios,
            }

        # 3. EDIÇÃO NO MODELADOR ESTRUTURAL (Vigas, Lajes, Pilares)
        eh_mutacao = any(k in msg_norm for k in ["MUD", "ALTER", "EDIT", "DEFIN", "TROC", "APLIC", "ADIC"])
        tem_elemento = any(k in msg_norm for k in ["VIGA", "LAJE", "PILAR", "CARGA", "SOBRECARGA"])
        
        if eh_mutacao and tem_elemento:
            try:
                res_mut = self.orchestrator.processar_comando_local(msg, {"edificio_nome": self.edificio_ativo or "054"})
                if res_mut.get("status") == "sucesso":
                    elem_tipo = res_mut.get("elemento", "").capitalize()
                    nome_elem = res_mut.get("nome", "")
                    pav_nome = res_mut.get("pavimento", "")
                    antes = res_mut.get("antes", {})
                    depois = res_mut.get("depois", {})

                    linhas = [
                        f"### ✏️ Alteração no Modelador Estrutural Concluída com Sucesso!\n",
                        f"- **Edifício:** `{res_mut.get('edificio')}`",
                        f"- **Pavimento:** `{pav_nome}`",
                        f"- **Elemento:** `{elem_tipo} {nome_elem}`\n",
                    ]

                    if elem_tipo.lower() == "viga":
                        linhas.append(f"| Parâmetro | Antes | Depois |")
                        linhas.append(f"| :--- | :---: | :---: |")
                        linhas.append(f"| **Largura (b)** | `{antes.get('b_cm', 0):.0f} cm` | **`{depois.get('b_cm', 0):.0f} cm`** |")
                        linhas.append(f"| **Altura (h)** | `{antes.get('h_cm', 0):.0f} cm` | **`{depois.get('h_cm', 0):.0f} cm`** |")
                        if antes.get("desnivel_cm") != depois.get("desnivel_cm"):
                            linhas.append(f"| **Desnível** | `{antes.get('desnivel_cm', 0):.1f} cm` | **`{depois.get('desnivel_cm', 0):.1f} cm`** |")

                    elif elem_tipo.lower() == "laje":
                        linhas.append(f"| Parâmetro | Antes | Depois |")
                        linhas.append(f"| :--- | :---: | :---: |")
                        linhas.append(f"| **Espessura (h)** | `{antes.get('espessura_cm', 0):.1f} cm` | **`{depois.get('espessura_cm', 0):.1f} cm`** |")
                        if res_mut.get("cargas_aplicadas"):
                            cargs = res_mut["cargas_aplicadas"]
                            if "carga_permanente_tf_m2" in cargs:
                                linhas.append(f"| **Carga Permanente (g)** | - | **`{cargs['carga_permanente_tf_m2']:.2f} tf/m²`** |")
                            if "carga_acidental_tf_m2" in cargs:
                                linhas.append(f"| **Carga Acidental (q)** | - | **`{cargs['carga_acidental_tf_m2']:.2f} tf/m²`** |")

                    elif elem_tipo.lower() == "pilar":
                        linhas.append(f"| Dimensão | Antes | Depois |")
                        linhas.append(f"| :--- | :---: | :---: |")
                        linhas.append(f"| **Seção BxH** | `{antes.get('b_cm', 0):.0f}x{antes.get('h_cm', 0):.0f} cm` | **`{depois.get('b_cm', 0):.0f}x{depois.get('h_cm', 0):.0f} cm`** |")

                    linhas.append(f"\n> [!NOTE]\n> A geometria foi gravada no arquivo de modelo do edifício via API nativa do TQS. Ao abrir o Modelador Estrutural no TQS, a nova seção já estará ativa.")

                    return {
                        "tipo": "edicao_modelo",
                        "texto": "\n".join(linhas),
                        "dados": res_mut,
                    }
                elif res_mut.get("status") == "erro":
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Erro na alteração do modelo:** {res_mut.get('mensagem', 'Operação não concluída.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro ao processar edição no modelador:**\n\n`{str(e)}`"
                }

        # 4. CONSULTA / LISTAGEM NO MODELADOR ESTRUTURAL
        pediu_consulta_modelo = any(k in msg_norm for k in ["LIST", "QUAI", "MOSTR", "VER", "EXIB"]) and any(k in msg_norm for k in ["PAVIMENT", "PISO", "VIGA", "LAJE", "PILAR", "CARGA"])
        if pediu_consulta_modelo:
            try:
                res_cons = self.orchestrator.processar_comando_local(msg, {"edificio_nome": self.edificio_ativo or "054"})
                if res_cons.get("status") == "sucesso":
                    tipo_c = res_cons.get("tipo")

                    if tipo_c == "pavimentos_modelo":
                        pavs = res_cons.get("pavimentos", [])
                        linhas = [f"### 📑 Pavimentos do Edifício `{res_cons.get('edificio')}` no Modelador:\n"]
                        linhas.append("| # | Pavimento | Vigas | Lajes | Pilares | Cargas Área | Cargas Lin. |")
                        linhas.append("| :-: | :--- | :-: | :-: | :-: | :-: | :-: |")
                        for p in pavs:
                            linhas.append(f"| {p['indice']} | **{p['nome']}** | {p['num_vigas']} | {p['num_lajes']} | {p['num_pilares']} | {p['num_cargas_area']} | {p['num_cargas_lineares']} |")
                        linhas.append(f"\n*Para ver os detalhes de qualquer pavimento, digite por exemplo:* `Liste as vigas do pavimento térreo`")
                        return {
                            "tipo": "listagem_modelo",
                            "texto": "\n".join(linhas),
                            "dados": pavs,
                        }

                    elif tipo_c == "elementos_pavimento":
                        linhas = [f"### 🔍 Elementos do Pavimento `{res_cons.get('pavimento')}` ({res_cons.get('edificio')}):\n"]
                        if "vigas" in res_cons:
                            vigas = res_cons["vigas"]
                            linhas.append(f"**Total de Vigas:** {len(vigas)}\n")
                            linhas.append("| Viga | Seção (cm) | Desnível (cm) | Nós | Extensão (m) |")
                            linhas.append("| :--- | :---: | :---: | :---: | :---: |")
                            for v in vigas[:20]:
                                ext = "-"
                                if len(v["coordenadas"]) >= 2:
                                    x0, y0 = v["coordenadas"][0]["x_m"], v["coordenadas"][0]["y_m"]
                                    x1, y1 = v["coordenadas"][-1]["x_m"], v["coordenadas"][-1]["y_m"]
                                    ext = f"{((x1-x0)**2 + (y1-y0)**2)**0.5:.2f} m"
                                linhas.append(f"| **{v['nome']}** | **{v['b_cm']:.0f}x{v['h_cm']:.0f}** | {v['desnivel_cm']:.1f} | {v['num_nos']} | {ext} |")
                            if len(vigas) > 20:
                                linhas.append(f"\n*... e mais {len(vigas) - 20} vigas catalogadas.*")

                        elif "lajes" in res_cons:
                            lajes = res_cons["lajes"]
                            linhas.append(f"**Total de Lajes:** {len(lajes)}\n")
                            linhas.append("| Laje | Espessura (cm) | Desnível (cm) | Tipo | Ângulo |")
                            linhas.append("| :--- | :---: | :---: | :---: | :---: |")
                            for l in lajes[:20]:
                                linhas.append(f"| **{l['nome']}** | **{l['espessura_cm']:.1f} cm** | {l['desnivel_cm']:.1f} | {l['tipo_descricao']} | {l['angulo_principal_graus']:.0f}° |")
                            if len(lajes) > 20:
                                linhas.append(f"\n*... e mais {len(lajes) - 20} lajes catalogadas.*")

                        elif "pilares" in res_cons:
                            pilares = res_cons["pilares"]
                            linhas.append(f"**Total de Pilares:** {len(pilares)}\n")
                            linhas.append("| Pilar | Seção (cm) | X (m) | Y (m) |")
                            linhas.append("| :--- | :---: | :---: | :---: |")
                            for p in pilares[:20]:
                                linhas.append(f"| **{p['nome']}** | **{p['secao_cm']}** | {p['x_m']:.2f} | {p['y_m']:.2f} |")
                            if len(pilares) > 20:
                                linhas.append(f"\n*... e mais {len(pilares) - 20} pilares catalogados.*")

                        return {
                            "tipo": "listagem_modelo",
                            "texto": "\n".join(linhas),
                            "dados": res_cons,
                        }
            except Exception as e:
                pass

        # 5. Solicitação de Processamento Estrutural do Edifício
        pediu_processamento = any(k in msg_norm for k in ["PROCESS", "CALCUL", "ROD", "EXECUT", "PORTIC", "RECALCUL"]) and any(k in msg_norm for k in ["EDIFIC", "OBRA", "PROJET", "PORTIC", "ESTRUTUR", "MODEL"])
        if pediu_processamento:
            edificio_alvo = self.edificio_ativo or "054"
            num_match = re.search(r'\b(0\d{2}|\d{3,4})\b', msg)
            if num_match:
                edificio_alvo = num_match.group(1)

            try:
                res_proc = self.orchestrator.processar_comando_local(
                    msg, {"edificio_nome": edificio_alvo}
                )
                if res_proc.get("sucesso"):
                    self.edificio_ativo = res_proc.get("edificio", edificio_alvo)
                    dur = res_proc.get("duracao_segundos", 0.0)
                    tipo_desc = res_proc.get("tipo_processamento", "Pórtico Espacial")
                    linhas = [f"### ⚙️ Processamento do Edifício Concluído com Sucesso!\n"]
                    linhas.append(
                        f"- **Edifício:** `{res_proc.get('edificio')}`\n"
                        f"- **Tipo de Cálculo:** {tipo_desc}\n"
                        f"- **Tempo de Execução:** `{dur:.1f} segundos`\n"
                        f"- **Pórtico Espacial:** `{'Calculado e Convergido (PORLIS OK)' if res_proc.get('tem_porlis') else 'Não gerado'}`\n"
                        f"- **Geometria de Pilares (CARDWG):** `{'Extraída com sucesso' if res_proc.get('tem_cardwg') else 'Não gerada'}`\n"
                    )

                    if res_proc.get("planta_gerada", {}).get("sucesso"):
                        pg = res_proc["planta_gerada"]
                        linhas.append(
                            f"> [!TIP]\n"
                            f"> **Planta de Cargas Atualizada:** O desenho `{os.path.basename(pg['caminho_dwg'])}` foi gerado automaticamente "
                            f"na pasta `ESPACIAL` com as novas reações dos **{pg['total_pilares']} pilares**.\n"
                        )

                    return {
                        "tipo": "processamento_concluido",
                        "texto": "\n".join(linhas),
                        "dados": res_proc,
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha no processamento do edifício:** {res_proc.get('erro', 'O TQS não retornou os arquivos esperados.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro durante o processamento do edifício:**\n\n`{str(e)}`"
                }

        # 6. Solicitação de Geração de Planta de Formas de Alvenaria Estrutural
        pediu_formas_alvenaria = any(k in msg_norm for k in ["FORMA", "ALVENAR", "FIADA", "DESFIAD", "PRE_FOR", "MODULAC"]) and any(k in msg_norm for k in ["PLANTA", "DESENH", "GERAR", "EMITIR", "CRIAR", "FAZER", "TRANSFORM"])
        if pediu_formas_alvenaria:
            edificio_alvo = self.edificio_ativo or "054"
            pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', msg_lower)
            pav_alvo = pav_match.group(1).upper() if pav_match else "TIPO A"

            try:
                res = self.orchestrator.processar_comando_local(
                    f"gerar formas alvenaria no pavimento {pav_alvo}",
                    {"edificio_nome": edificio_alvo, "pavimento": pav_alvo}
                )
                if res.get("status") == "sucesso":
                    aud = res.get("auditoria", {})
                    dwg_caminho = res.get("caminho_dwg")
                    linhas = [
                        f"### 🧱 Planta de Formas de Alvenaria Estrutural Gerada com Sucesso!\n",
                        f"- **Edifício:** `{res.get('edificio')}`",
                        f"- **Pavimento:** `{res.get('pavimento')}`",
                        f"- **Escala:** `1:{res.get('escala')}`",
                        f"- **Arquivo Executivo:** `{dwg_caminho}`",
                        f"- **Elementos Estruturais Purgados (limpeza de poluição):** `{res.get('elementos_purgados')} elementos`",
                        f"- **Lajes Identificadas e Sobrepostas:** `{res.get('total_lajes')} lajes` (com espessuras h)",
                        f"- **Vãos e Esquadrias Cotados:** `{res.get('total_vaos')} aberturas`",
                        f"- **Total de Textos Normativos:** `{aud.get('total_textos')} textos` (altura mínima: `{aud.get('min_text_height_papel_cm'):.2f} cm` no papel)",
                        f"\n> [!TIP]\n> O desenho executivo foi gerado no formato oficial **A0-45**, integrando lajes, cotas modulares de aberturas, resumo de materiais (LISTMELV), legenda de blocos e corte esquemático de resistências dos materiais.",
                    ]
                    return {
                        "tipo": "planta_formas_alvenaria_gerada",
                        "texto": "\n".join(linhas),
                        "arquivo_dwg": dwg_caminho,
                        "dados": res,
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha ao gerar planta de formas de alvenaria:** {res.get('erro', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro ao processar formas de alvenaria:**\n\n`{str(e)}`"
                }

        # 7. Solicitação de Geração de Planta de Cargas / Gabarito
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
            or "gabarito" in msg_lower
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.processar_comando_local(
                    "gerar_planta_de_cargas",
                    {"edificio_nome": edificio_alvo, "caminho_saida_desenho": "GABARITO.DWG"}
                )

                if res.get("status") == "sucesso":
                    self.ultima_planta = res
                    pilares = res.get("pilares", [])
                    total = len(pilares)
                    dwg_local = res.get("arquivo_desenho_gerado")
                    caminho_ed = res.get("caminho_edificio", "")
                    copia_tqs = res.get("caminho_espacial")
                    if not copia_tqs and caminho_ed and dwg_local:
                        copia_tqs = os.path.join(caminho_ed, "ESPACIAL", os.path.basename(dwg_local))

                    # Verifica se há pilares tracionados
                    tracionados = [p for p in pilares if p.get("nk_max_tf", 0.0) < 0]

                    dados_porlid = res.get("dados_porlid")
                    porlid_info = ""
                    if dados_porlid and dados_porlid.get("sucesso"):
                        num_c = dados_porlid.get("num_casos", 1)
                        if num_c > 1:
                            casos_nomes = [c["nome"] for c in dados_porlid.get("casos", [])]
                            porlid_info = (
                                f"- **Tabela de Cargas Oficial (PORLID):** {dados_porlid.get('total_elementos')} elementos em **{num_c} Casos Críticos**:\n"
                                + "\n".join([f"  * `{c['nome']}`: {c['titulo']}" for c in dados_porlid.get("casos", [])])
                                + "\n"
                            )
                        else:
                            porlid_info = f"- **Tabela de Cargas Oficial (PORLID):** {dados_porlid.get('total_elementos')} elementos ({dados_porlid.get('titulo')})\n"

                    bkp_info = ""
                    caminho_bkp = res.get("caminho_backup")
                    if caminho_bkp:
                        bkp_info = f"- 🛡️ **Backup da Versão Anterior Preservado:** `{os.path.basename(caminho_bkp)}`\n"

                    resposta_texto = (
                        f"### 🎯 Planta de Cargas e Locação Gerada com Sucesso!\n\n"
                        f"- **Edifício:** `{res.get('edificio')}`\n"
                        f"- **Total de Pilares na Fundação:** **{total} pilares**\n"
                        f"{porlid_info}"
                        f"- **Escala:** 1:50 com Projeção de Moldura Oficial TQS\n"
                        f"- **Arquivo DWG Nativo:** `{dwg_local}`\n"
                        f"- **Salvo na pasta ESPACIAL do TQS:** `{copia_tqs}`\n"
                        f"{bkp_info}\n"
                    )

                    if tracionados:
                        resposta_texto += (
                            f"> [!WARNING]\n"
                            f"> **Atenção Estrutural:** Foram detectados **{len(tracionados)} pilar(es) com esforço de tração** "
                            f"(ex: `{tracionados[0]['pilar']}` com Nk = `{tracionados[0]['nk_max_tf']:.1f} tf`). "
                            f"Verifique a ancoragem das estacas/sapatas contra arrancamento.\n\n"
                        )

                    resposta_texto += (
                        "O arquivo `.DWG` foi gravado com todos os níveis oficiais do TQS V25 (Nível 3 contorno, "
                        "Nível 9 nomes, Nível 12 dimensões, Nível 21 baricentros, Nível 32 margens e tabela de cargas idêntica ao PORLID "
                        "com todos os casos críticos e 7 colunas por bloco: Pilar, Fz, Fx, Fy, Mx, My, Mz)."
                    )

                    return {
                        "tipo": "planta_gerada",
                        "texto": resposta_texto,
                        "dados": pilares,
                        "dados_porlid": dados_porlid,
                        "arquivo_dwg": dwg_local,
                        "copia_tqs": copia_tqs,
                        "caminho_backup": caminho_bkp,
                        "edificio": res.get("edificio"),
                        "tracionados": tracionados,
                    }

                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Não foi possível gerar a planta:** {res.get('mensagem', 'Erro desconhecido')}",
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro ao processar o edifício `{edificio_alvo}`:**\n\n`{str(e)}`",
                }

        # 6. Perguntas analíticas sobre os pilares (maiores cargas, tração, etc.)
        if any(k in msg_lower for k in ["maior", "pesado", "mais carregado", "critico", "ranking"]):
            if not self.ultima_planta:
                try:
                    self.orchestrator.processar_comando_local("gerar_planta_de_cargas", {"edificio_nome": self.edificio_ativo or "054"})
                except Exception:
                    pass

            if self.ultima_planta:
                pilares = self.ultima_planta.get("pilares", [])
                ordenados = sorted(pilares, key=lambda x: x.get("nk_max_tf", 0.0), reverse=True)
                top5 = ordenados[:5]

                linhas = [f"### 🏆 Top 5 Pilares Mais Carregados da Fundação ({self.edificio_ativo}):\n"]
                linhas.append("| Pilar | Seção (cm) | Nk Máx (tf) | Mx (tf.m) | My (tf.m) | Xcg (m) | Ycg (m) |")
                linhas.append("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
                for p in top5:
                    linhas.append(
                        f"| **{p['pilar']}** | {p['secao_cm']} | **{p['nk_max_tf']:.1f}** | "
                        f"{p['mxk_tfm']:.2f} | {p['myk_tfm']:.2f} | {p['xcg_m']:.2f} | {p['ycg_m']:.2f} |"
                    )
                return {
                    "tipo": "analise_pilares",
                    "texto": "\n".join(linhas),
                    "dados": top5,
                }

        # 7. Pergunta sobre pilares com tração
        if any(k in msg_lower for k in ["tracao", "tração", "arrancamento", "negativo"]):
            if not self.ultima_planta:
                try:
                    self.orchestrator.processar_comando_local("gerar_planta_de_cargas", {"edificio_nome": self.edificio_ativo or "054"})
                except Exception:
                    pass

            if self.ultima_planta:
                pilares = self.ultima_planta.get("pilares", [])
                tracionados = [p for p in pilares if p.get("nk_max_tf", 0.0) < 0]
                if tracionados:
                    linhas = [f"### ⚠️ Pilares com Esforço de Tração na Fundação:\n"]
                    linhas.append("| Pilar | Seção (cm) | Nk (tf) | Xcg (m) | Ycg (m) |")
                    linhas.append("| :--- | :---: | :---: | :---: | :---: |")
                    for p in tracionados:
                        linhas.append(f"| **{p['pilar']}** | {p['secao_cm']} | **{p['nk_max_tf']:.2f}** | {p['xcg_m']:.2f} | {p['ycg_m']:.2f} |")
                    linhas.append("\n> [!CAUTION]\n> Pilares com tração requerem elementos de fundação projetados para resistir ao arrancamento.")
                    return {"tipo": "analise_pilares", "texto": "\n".join(linhas), "dados": tracionados}
                else:
                    return {
                        "tipo": "texto",
                        "texto": f"✅ Nenhum pilar da fundação no edifício `{self.edificio_ativo}` apresenta esforços axiais de tração ($N_k < 0$). Todos os pilares estão em compressão."
                    }

        # 8. Se o Gemini estiver configurado, responde com raciocínio de IA generativa
        if self.gemini_client.esta_configurado():
            contexto = f"Edifício selecionado: {self.edificio_ativo}."
            if self.ultima_planta:
                pils = self.ultima_planta.get("pilares", [])
                contexto += f" Total de pilares na fundação: {len(pils)}."
                if pils:
                    max_nk = max(p.get("nk_max_tf", 0.0) for p in pils)
                    contexto += f" Carga vertical máxima: {max_nk:.1f} tf."
            
            resp_gemini = self.gemini_client.gerar_resposta(
                mensagens=[{"role": "user", "content": mensagem_usuario}],
                contexto_estrutural=contexto,
            )
            if resp_gemini.get("sucesso"):
                return {"tipo": "texto", "texto": resp_gemini["texto"]}

        # 9. Resposta Geral Padrão (Modo Local Offline)
        return {
            "tipo": "texto",
            "texto": (
                f"Olá! Sou o **AUTQS Agent**, seu assistente especializado em TQS V25 e Engenharia Estrutural.\n\n"
                f"**Edifício ativo selecionado:** `{self.edificio_ativo or 'Nenhum'}`\n\n"
                f"**Comandos que você pode me pedir:**\n"
                f"1. 🏢 *'Quais edifícios tenho no TQS?'* — Lista todos os projetos no disco e status de cálculo.\n"
                f"2. 📑 *'Liste os pavimentos do edifício'* — Mostra resumo de vigas, lajes e pilares por piso.\n"
                f"3. 🔍 *'Liste as vigas do térreo'* ou *'Quais são as lajes do 2º pavimento?'* — Inspeciona elementos.\n"
                f"4. ✏️ *'Mude a viga V1 para 20x60'* ou *'Altere a laje L3 para espessura 14cm'* — Edita elementos no modelador.\n"
                f"5. 📐 *'Gere a planta de cargas do edifício 054'* — Emite a prancha DWG nativa completa.\n"
                f"6. 🏆 *'Quais são os pilares mais carregados?'* — Exibe os pilares com maiores valores de $N_k$."
            )
        }
