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
        self.modificacao_pendente: Optional[Dict[str, Any]] = None

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
        num_match = re.search(r'(?<![\d.])(0\d{2}|\d{3,4})(?![\d.])', msg)
        edificios_disponiveis = TQSBuildingReader.listar_edificios_disponiveis()
        if num_match:
            candidato = num_match.group(1)
            for ed in edificios_disponiveis:
                if candidato in ed["nome"]:
                    self.edificio_ativo = candidato
                    break
        else:
            for ed in edificios_disponiveis:
                PALAVRAS_RESERVADAS_EDIFICIO = {"pilar", "pilares", "viga", "vigas", "laje", "lajes", "pavimento", "pavimentos", "piso", "pisos", "edificio", "edificios", "modelo", "modelos", "carga", "cargas", "planta", "plantas", "forma", "formas", "projeto", "projetos", "obra", "obras", "modificacao", "modificacoes", "alteracao", "alteracoes", "terreo"}
                tokens = [w for w in re.split(r'[\s\-_[\]]+', ed["nome"].lower()) if len(w) > 3 and w not in PALAVRAS_RESERVADAS_EDIFICIO]
                if any(t in msg_lower for t in tokens):
                    self.edificio_ativo = ed["nome"]
                    break

        from src.tqs_adapter.model_editor import normalizar_texto
        msg_norm = normalizar_texto(msg)

        # Resposta a solicitação de aprovação pendente no chat
        if self.modificacao_pendente:
            eh_afirmacao = any(msg_norm == k for k in ["SIM", "S", "CONFIRMO", "CONFIRMAR", "APROVAR", "APROVADO", "YES", "Y", "OK", "CLARO", "AUTORIZO", "AUTORIZADO", "PODE"])
            eh_negacao = any(msg_norm == k for k in ["NAO", "N", "CANCELA", "CANCELAR", "REJEITAR", "NO", "NUNCA", "DEIXA"])

            if eh_afirmacao:
                pend = self.modificacao_pendente
                self.modificacao_pendente = None
                res_mut = self.orchestrator.registry.executar_ferramenta(pend["funcao"], pend["parametros"])
                if pend.get("tipo") == "revisao_planta":
                    return {
                        "tipo": "texto" if res_mut.get("status") == "sucesso" else "erro",
                        "texto": res_mut.get("resumo_executivo") or res_mut.get("erro", "Falha ao gravar a revisão."),
                        "dados": res_mut,
                    }
                if res_mut.get("status") == "sucesso":
                    elem_tipo = res_mut.get("elemento", "").capitalize()
                    nome_elem = res_mut.get("nome", "")
                    pav_nome = res_mut.get("pavimento", "")
                    antes = res_mut.get("antes", {})
                    depois = res_mut.get("depois", {})

                    linhas = [
                        f"### ✅ Alteração no Modelador Estrutural Aprovada e Aplicada com Sucesso!\n",
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
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Erro na alteração do modelo:** {res_mut.get('mensagem', 'Operação não concluída.')}"
                    }
            elif eh_negacao:
                pend = self.modificacao_pendente
                self.modificacao_pendente = None
                if pend.get("tipo") == "revisao_planta":
                    return {
                        "tipo": "texto",
                        "texto": "🚫 **Operação cancelada pelo usuário.**\n\nNada foi gravado: os arquivos da prancha permanecem inalterados."
                    }
                return {
                    "tipo": "texto",
                    "texto": "🚫 **Modificação cancelada pelo usuário.**\n\nNenhuma alteração foi gravada. O modelo estrutural permanece inalterado."
                }
            else:
                self.modificacao_pendente = None

        # 1.5. Revisões de pranchas do Editor de Plantas (Case 15). Fica antes das rotas genéricas
        # ("listar ... projeto", "comparar/revisar planta"), que também reagiriam a esses pedidos.
        from src.skills.case_15_revisao_plantas.comandos import eh_pedido_revisao, extrair_parametros_revisao
        if eh_pedido_revisao(msg):
            params_rev = extrair_parametros_revisao(msg, self.edificio_ativo or "054")
            params_rev.pop("aprovado", None)
            res_rev = self.orchestrator.registry.executar_ferramenta("emitir_revisao_planta", params_rev)
            if res_rev.get("status") == "aguardando_aprovacao":
                aprovados = dict(params_rev, aprovado=True)
                rev = res_rev.get("revisao") if isinstance(res_rev.get("revisao"), dict) else None
                if rev:  # grava exatamente o texto mostrado na prévia
                    aprovados.update(descricao=rev["descricao"], autor=rev["autor"], data=rev["data"])
                aprovados.pop("simular", None)
                self.modificacao_pendente = {"tipo": "revisao_planta", "funcao": "emitir_revisao_planta", "parametros": aprovados}
                alvo = ("a revisão no .CPL" if rev else "o PDF em PLANTAS" if res_rev.get("acao") == "plotar"
                        else "o carimbo (_CR.DWG)")
                texto = (res_rev["resumo_executivo"]
                         + f"\n\n> [!WARNING]\n> {alvo[0].upper() + alvo[1:]} da prancha só é gravado depois da sua aprovação."
                         + f"\n\nDeseja gravar {alvo}?\n👉 Responda **sim** para gravar ou **não** para cancelar.")
                return {"tipo": "solicitacao_aprovacao", "texto": texto, "dados": res_rev}
            return {
                "tipo": "texto" if res_rev.get("sucesso") else "erro",
                "texto": res_rev.get("resumo_executivo") or res_rev.get("erro", ""),
                "dados": res_rev,
            }

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

        # 3. SOLICITAÇÃO DE EDIÇÃO NO MODELADOR ESTRUTURAL (Requer Aprovação Obrigatória)
        mut = self.orchestrator.extrair_intencao_mutacao(msg, {"edificio_nome": self.edificio_ativo or "054"})
        if mut:
            from src.tqs_adapter.model_editor import TQSModelEditor
            ed_nome = mut["parametros"].get("edificio_nome", "054")
            pav = mut["parametros"].get("pavimento", "terreo")
            tipo_elem = mut.get("tipo_elemento", "elemento")

            detalhes_tabela = []
            elem_nome = ""

            try:
                with TQSModelEditor(ed_nome) as editor:
                    if tipo_elem == "viga":
                        ident = mut["parametros"].get("identificador_viga", "")
                        v = editor.obter_viga(pav, ident)
                        if not v:
                            return {"tipo": "erro", "texto": f"❌ Viga '{ident}' não foi localizada no pavimento '{pav}'."}
                        elem_nome = v["nome"]
                        b_novo = mut["parametros"].get("b_cm")
                        h_novo = mut["parametros"].get("h_cm")
                        desn_novo = mut["parametros"].get("desnivel_cm")
                        if b_novo is not None:
                            detalhes_tabela.append(f"| **Largura (b)** | `{v['b_cm']:.0f} cm` | **`{b_novo:.0f} cm`** |")
                        if h_novo is not None:
                            detalhes_tabela.append(f"| **Altura (h)** | `{v['h_cm']:.0f} cm` | **`{h_novo:.0f} cm`** |")
                        if desn_novo is not None:
                            detalhes_tabela.append(f"| **Desnível** | `{v['desnivel_cm']:.1f} cm` | **`{desn_novo:.1f} cm`** |")

                    elif tipo_elem == "laje":
                        ident = mut["parametros"].get("identificador_laje", "")
                        l = editor.obter_laje(pav, ident)
                        if not l:
                            return {"tipo": "erro", "texto": f"❌ Laje '{ident}' não foi localizada no pavimento '{pav}'."}
                        elem_nome = l["nome"]
                        esp_novo = mut["parametros"].get("espessura_cm")
                        desn_novo = mut["parametros"].get("desnivel_cm")
                        if esp_novo is not None:
                            detalhes_tabela.append(f"| **Espessura** | `{l['espessura_cm']:.1f} cm` | **`{esp_novo:.1f} cm`** |")
                        if desn_novo is not None:
                            detalhes_tabela.append(f"| **Desnível** | `{l['desnivel_cm']:.1f} cm` | **`{desn_novo:.1f} cm`** |")
                        if mut["parametros"].get("carga_permanente_tf_m2") is not None:
                            detalhes_tabela.append(f"| **Carga Permanente (g)** | - | **`{mut['parametros']['carga_permanente_tf_m2']:.2f} tf/m²`** |")
                        if mut["parametros"].get("carga_acidental_tf_m2") is not None:
                            detalhes_tabela.append(f"| **Carga Acidental (q)** | - | **`{mut['parametros']['carga_acidental_tf_m2']:.2f} tf/m²`** |")

                    elif tipo_elem == "pilar":
                        ident = mut["parametros"].get("identificador_pilar", "")
                        p = editor.obter_pilar(pav, ident)
                        if not p:
                            return {"tipo": "erro", "texto": f"❌ Pilar '{ident}' não foi localizado no pavimento '{pav}'."}
                        elem_nome = p["nome"]
                        b_novo = mut["parametros"].get("b_cm")
                        h_novo = mut["parametros"].get("h_cm")
                        if b_novo is not None:
                            detalhes_tabela.append(f"| **Largura (b)** | `{p['b_cm']:.0f} cm` | **`{b_novo:.0f} cm`** |")
                        if h_novo is not None:
                            detalhes_tabela.append(f"| **Comprimento (h)** | `{p['h_cm']:.0f} cm` | **`{h_novo:.0f} cm`** |")

            except Exception as e:
                return {"tipo": "erro", "texto": f"❌ Erro ao inspecionar elemento no modelo: {e}"}

            if not detalhes_tabela:
                return {"tipo": "texto", "texto": "⚠️ Nenhuma alteração geométrica identificada para aplicar."}

            self.modificacao_pendente = mut

            linhas = [
                "### ⚠️ Solicitação de Aprovação: Modificação no Modelo Estrutural TQS\n",
                f"- **Edifício:** `{ed_nome}`",
                f"- **Pavimento:** `{pav.upper()}`",
                f"- **Elemento:** `{tipo_elem.capitalize()} {elem_nome}`\n",
                "| Parâmetro | Valor Atual | Novo Valor Proposto |",
                "| :--- | :---: | :---: |",
            ] + detalhes_tabela + [
                "\n> [!WARNING]",
                "> **REGRA DE SEGURANÇA:** Toda e qualquer modificação no modelo estrutural deve ser previamente aprovada pelo usuário.",
                "\nDeseja aprovar e aplicar esta alteração no modelo estrutural?",
                "👉 Responda **sim** para aprovar ou **não** para cancelar."
            ]

            return {
                "tipo": "solicitacao_aprovacao",
                "texto": "\n".join(linhas),
                "dados": mut
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

        # 6.0. Comparação de Geometrias e Plantas de Formas (Case 07: Diff DWG)
        pediu_comparacao = any(k in msg_norm for k in ["COMPAR", "DIFF", "ALTERA", "MUDOU", "DIFERENC", "SOBREPOSI"]) and any(k in msg_norm for k in ["GEOMETR", "FORMA", "PLANTA", "ARQUITETUR", "DESENHO", "PROJETO"])
        if pediu_comparacao:
            edificio_alvo = self.edificio_ativo or "054"
            pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', msg_lower)
            pav_alvo = pav_match.group(1).upper() if pav_match else None

            try:
                params = {"edificio_base": edificio_alvo}
                if pav_alvo:
                    params["pavimento_base"] = pav_alvo
                else:
                    params["modo"] = "edificio_geometrias"
                res = self.orchestrator.registry.executar_ferramenta("comparar_geometrias_formas", params)
                if res.get("sucesso") or res.get("status") == "sucesso":
                    texto = res.get("resumo_executivo", "Auditoria de comparação concluída.")
                    dxf = res.get("caminho_diff_dxf")
                    return {
                        "tipo": "comparacao_formas",
                        "texto": texto,
                        "arquivo_dwg": dxf,
                        "dados": res.get("dados_completos"),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na comparação de geometrias:** {res.get('erro', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na comparação de geometrias:**\n\n`{str(e)}`"
                }

        # 6.01. Dimensionamento e Auditoria de Pilares (Case 04)
        pediu_pilares = any(k in msg_norm for k in ["DIMENSION", "OTIMIZ", "AUDIT"]) and any(k in msg_norm for k in ["PILAR", "PILARES"])
        if pediu_pilares:
            edificio_alvo = self.edificio_ativo or "054"
            p_match = re.search(r'\b[pP](\d+)\b', msg)
            pilar_filtro = f"P{p_match.group(1)}" if p_match else None
            try:
                params = {"edificio_nome": edificio_alvo, "formato": "resumo"}
                if pilar_filtro:
                    params["pilar"] = pilar_filtro
                res = self.orchestrator.registry.executar_ferramenta("analisar_pilares_edificio", params)
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "analise_pilares_avancada",
                        "texto": res.get("resumo", "Auditoria de pilares concluída."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na auditoria de pilares:** {res.get('erro', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na auditoria de pilares:**\n\n`{str(e)}`"
                }

        # 6.02. Verificação de Consistência da Planta de Formas (Case 05)
        pediu_consistencia = any(k in msg_norm for k in ["CONSIST", "ERRO", "INCONFORM", "AUDIT"]) and any(k in msg_norm for k in ["FORMA", "PLANTA", "APOIO"])
        if pediu_consistencia:
            edificio_alvo = self.edificio_ativo or "054"
            pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', msg_lower)
            pav_alvo = pav_match.group(1).upper() if pav_match else None
            try:
                params = {"edificio_nome": edificio_alvo, "formato": "resumo"}
                if pav_alvo:
                    params["pavimento"] = pav_alvo
                res = self.orchestrator.registry.executar_ferramenta("verificar_consistencia_planta", params)
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "consistencia_formas",
                        "texto": res.get("resumo", "Auditoria de consistência concluída."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na verificação de consistência:** {res.get('erro', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na verificação de consistência:**\n\n`{str(e)}`"
                }

        # 6.03. Análise de Esforços, Cortante e Bielas de Vigas (Case 06)
        pediu_vigas = any(k in msg_norm for k in ["BIELA", "CORTANT", "ESFORC", "DIMENSION"]) and any(k in msg_norm for k in ["VIGA", "VIGAS"])
        if pediu_vigas:
            edificio_alvo = self.edificio_ativo or "054"
            pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', msg_lower)
            pav_alvo = pav_match.group(1).upper() if pav_match else "TERREO"
            v_match = re.search(r'\b[vV](\d+)\b', msg)
            viga_alvo = f"V{v_match.group(1)}" if v_match else None
            try:
                params = {"edificio_nome": edificio_alvo, "pavimento": pav_alvo, "formato": "resumo"}
                if viga_alvo:
                    params["viga"] = viga_alvo
                res = self.orchestrator.registry.executar_ferramenta("analisar_vigas_pavimento", params)
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "analise_vigas",
                        "texto": res.get("resumo", "Auditoria de vigas concluída."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na análise de vigas:** {res.get('erro', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na análise de vigas:**\n\n`{str(e)}`"
                }

        # 6.04. Estabilidade Global e ELS (Case 08: GamaZ, FAVt, Alfa e Deslocamentos de Vento)
        pediu_estabilidade = any(k in msg_norm for k in ["ESTABILID", "GAMAZ", "GAMA_Z", "ALFA", "DRIFT"]) or (
            any(k in msg_norm for k in ["DESLOCAMENT", "VENT"]) and any(k in msg_norm for k in ["TOPO", "INTERPISO", "ELS", "GLOBAL"])
        )
        if pediu_estabilidade:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.registry.executar_ferramenta("auditar_estabilidade_global", {"edificio_nome": edificio_alvo, "formato": "resumo"})
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "estabilidade_global",
                        "texto": res.get("resumo_executivo", "Auditoria de estabilidade global concluída."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na auditoria de estabilidade:** {res.get('mensagem', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na auditoria de estabilidade:**\n\n`{str(e)}`"
                }

        # 6.05. Auditoria de Lajes, Grelhas e Flechas (Case 09)
        pediu_lajes = any(k in msg_norm for k in ["LAJE", "GRELH", "FLECH", "PUNCA"]) and any(k in msg_norm for k in ["AUDIT", "VERIFIC", "ANALIS", "ESBELTEZ", "MODEL"])
        if pediu_lajes:
            edificio_alvo = self.edificio_ativo or "054"
            pav_match = re.search(r'(?:pavimento|piso)\s+([a-zA-Z0-9_\^]+(?:\s+[a-zA-Z0-9_\^]+)?)', msg_lower)
            pav_alvo = pav_match.group(1).upper() if pav_match else None
            try:
                params = {"edificio_nome": edificio_alvo, "formato": "resumo"}
                if pav_alvo:
                    params["pavimento"] = pav_alvo
                res = self.orchestrator.registry.executar_ferramenta("auditar_lajes_edificio", params)
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "auditoria_lajes",
                        "texto": res.get("resumo_executivo", "Auditoria de lajes concluída."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha na auditoria de lajes:** {res.get('mensagem', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro na auditoria de lajes:**\n\n`{str(e)}`"
                }

        # 6.06. Quantitativo Global de Materiais e Índices de Consumo (Case 10)
        pediu_materiais = any(k in msg_norm for k in ["QUANTITATIV", "CONSUM", "MATERIA"]) or (
            any(k in msg_norm for k in ["VOLUME", "TAXA"]) and any(k in msg_norm for k in ["CONCRET", "FORMA", "ACO", "CARBON"])
        )
        if pediu_materiais:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.registry.executar_ferramenta("extrair_quantitativo_materiais", {"edificio_nome": edificio_alvo, "formato": "resumo"})
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "quantitativo_materiais",
                        "texto": res.get("resumo_executivo", "Quantitativo de materiais concluído."),
                        "dados": res.get("dados", {}),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha no levantamento de materiais:** {res.get('mensagem', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro no levantamento de materiais:**\n\n`{str(e)}`"
                }

        # 6.07. Memorial Descritivo e Justificativo de Cálculo (Case 11)
        pediu_memorial = any(k in msg_norm for k in ["MEMORIAL", "JUSTIFICATIV"]) or (
            any(k in msg_norm for k in ["RELATORI", "DOCUMENT"]) and any(k in msg_norm for k in ["EXECUTIV", "CALCUL", "OBRA", "PROJET"])
        )
        if pediu_memorial:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.registry.executar_ferramenta("gerar_memorial_descritivo", {"edificio_nome": edificio_alvo})
                if res.get("sucesso") or res.get("status") == "sucesso":
                    return {
                        "tipo": "memorial_descritivo",
                        "texto": res.get("resumo_executivo", "Memorial descritivo gerado com sucesso."),
                        "arquivo_md": res.get("arquivo_md"),
                        "arquivo_html": res.get("arquivo_html"),
                    }
                else:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Falha ao gerar memorial:** {res.get('mensagem', 'Erro desconhecido.')}"
                    }
            except Exception as e:
                return {
                    "tipo": "erro",
                    "texto": f"❌ **Erro ao gerar memorial:**\n\n`{str(e)}`"
                }

        # 6.08. Limpeza e Padronização de Arquitetura CAD (Case 12)
        pediu_limpeza = any(k in msg_norm for k in ["LIMPEZA", "PADRONIZ", "HIGIENIZ"]) and any(k in msg_norm for k in ["ARQUITETUR", "DWG", "DXF", "GEO_"])
        if pediu_limpeza:
            m_arq = re.search(r'["\']?([a-zA-Z0-9_\-/\\]+\.(?:dwg|dxf))["\']?', msg, re.IGNORECASE)
            caminho_arq = m_arq.group(1) if m_arq else None
            if caminho_arq:
                try:
                    res = self.orchestrator.registry.executar_ferramenta("padronizar_arquitetura_tqs", {"caminho_arquivo": caminho_arq})
                    if res.get("sucesso") or res.get("status") == "sucesso":
                        return {
                            "tipo": "padronizacao_arquitetura",
                            "texto": res.get("resumo_executivo", "Padronização de arquitetura concluída."),
                            "arquivo_dwg": res.get("arquivo_gerado"),
                            "dados": res.get("dados", {}),
                        }
                    else:
                        return {
                            "tipo": "erro",
                            "texto": f"❌ **Falha na padronização da arquitetura:** {res.get('mensagem', 'Erro desconhecido.')}"
                        }
                except Exception as e:
                    return {
                        "tipo": "erro",
                        "texto": f"❌ **Erro na padronização da arquitetura:**\n\n`{str(e)}`"
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
        m_coords_avulsas = re.search(
            r'^\s*(?:mudar\s+(?:para\s+)?)?(?:origem\s+(?:para\s+)?)?([+-]?\d{2,}(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d{2,}(?:\.\d+)?)\s*$',
            msg,
            re.IGNORECASE,
        )
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha", "gabarito"])
            or "gabarito" in msg_lower
            or ("cota" in msg_lower and any(k in msg_norm for k in ["REFERENC", "ORIGEM", "PONTO", "0,0"]))
            or bool(m_coords_avulsas)
            or ("mudar" in msg_lower and any(k in msg_norm for k in ["ORIGEM", "PONTO", "COTA", "REFERENC"]))
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            # Detecção de origem de cotas
            origem_cotas = None
            if m_coords_avulsas:
                origem_cotas = (float(m_coords_avulsas.group(1)), float(m_coords_avulsas.group(2)))
            else:
                m_orig = re.search(r'(?:ponto|origem|refer[eê]ncia|mudar\s+para)[^\d+-]*?([+-]?\d+(?:\.\d+)?)\s*[,;\s]\s*([+-]?\d+(?:\.\d+)?)', msg, re.IGNORECASE)
                if m_orig:
                    try:
                        origem_cotas = (float(m_orig.group(1)), float(m_orig.group(2)))
                    except Exception:
                        pass

            params_planta = {"edificio_nome": edificio_alvo, "caminho_saida_desenho": "GABARITO.DWG"}
            if origem_cotas:
                params_planta["origem_cotas"] = origem_cotas

            try:
                res = self.orchestrator.processar_comando_local(
                    "gerar_planta_de_cargas",
                    params_planta
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

                    orig_info = ""
                    orig_ret = res.get("origem_cotas")
                    if orig_ret:
                        orig_info = f"- 📍 **Origem das Cotas Relativas (0,0):** `X = {orig_ret['x_cm']:.2f} cm` | `Y = {orig_ret['y_cm']:.2f} cm`\n"

                    resposta_texto = (
                        f"### 🎯 Planta de Cargas e Locação Gerada com Sucesso!\n\n"
                        f"- **Edifício:** `{res.get('edificio')}`\n"
                        f"- **Total de Pilares na Fundação:** **{total} pilares**\n"
                        f"{orig_info}"
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
