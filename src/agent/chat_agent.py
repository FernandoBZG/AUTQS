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
    faz análises estatísticas dos esforços e integra opcionalmente ao Google Gemini (camada gratuita).
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
        - tipo: 'texto', 'planta_gerada', 'listagem_edificios', 'analise_pilares'
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
            # Procura por palavras-chave do nome do edifício na mensagem (ex: "jardim", "europa")
            for ed in edificios_disponiveis:
                tokens = [w for w in re.split(r'[\s\-_\[\]]+', ed["nome"].lower()) if len(w) > 3]
                if any(t in msg_lower for t in tokens):
                    self.edificio_ativo = ed["nome"]
                    break


        # 2. Pergunta sobre edifícios disponíveis
        if any(k in msg_lower for k in ["quais", "listar", "mostrar"]) and any(k in msg_lower for k in ["edif", "projet", "obra"]):
            edificios = TQSBuildingReader.listar_edificios_disponiveis()
            linhas = ["### 🏢 Edifícios Detectados no Sistema TQS:\n"]
            for e in edificios:
                status = "✅ **Pronto para Emissão (Pórtico OK)**" if e["processado"] else "⚠️ *Requer Processamento no TQS*"
                linhas.append(f"- **{e['nome']}**\n  - Status: {status}\n  - Pasta: `{e['caminho']}`")
            
            linhas.append("\n*Para gerar a planta de cargas de qualquer um, digite por exemplo:* `Gere a planta de cargas do edifício 054`")
            return {
                "tipo": "listagem_edificios",
                "texto": "\n".join(linhas),
                "dados": edificios,
            }

        # 3. Solicitação de Geração de Planta de Cargas
        pediu_gerar_planta = (
            ("planta" in msg_lower and any(k in msg_lower for k in ["carga", "loca", "gerar", "desenh", "emitir", "funda"]))
            or any(k in msg_lower for k in ["gerar dwg", "criar dwg", "emitir prancha", "desenhar prancha", "gerar prancha"])
        )
        if pediu_gerar_planta:
            edificio_alvo = self.edificio_ativo or "054"
            try:
                res = self.orchestrator.processar_comando_local(
                    "gerar_planta_de_cargas",
                    {"edificio_nome": edificio_alvo}
                )

                if res.get("status") == "sucesso":
                    self.ultima_planta = res
                    pilares = res.get("pilares", [])
                    total = len(pilares)
                    dwg_local = res.get("arquivo_desenho_gerado")
                    caminho_ed = res.get("caminho_edificio", "")
                    copia_tqs = os.path.join(caminho_ed, os.path.basename(dwg_local)) if caminho_ed else dwg_local

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

                    resposta_texto = (
                        f"### 🎯 Planta de Cargas e Locação Gerada com Sucesso!\n\n"
                        f"- **Edifício:** `{res.get('edificio')}`\n"
                        f"- **Total de Pilares na Fundação:** **{total} pilares**\n"
                        f"{porlid_info}"
                        f"- **Escala:** 1:50 com Projeção de Moldura Oficial TQS\n"
                        f"- **Arquivo DWG Nativo:** `{dwg_local}`\n"
                        f"- **Salvo no TQS:** `{copia_tqs}`\n\n"
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

        # 4. Perguntas analíticas sobre os pilares (maiores cargas, tração, etc.)
        if any(k in msg_lower for k in ["maior", "pesado", "mais carregado", "critico", "ranking"]):
            if not self.ultima_planta:
                # Carrega automaticamente o edifício ativo
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

        # 5. Pergunta sobre pilares com tração
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

        # 6. Se o Gemini estiver configurado, responde com raciocínio de IA generativa
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

        # 7. Resposta Geral Padrão (Modo Local Offline)
        return {
            "tipo": "texto",
            "texto": (
                f"Olá! Sou o **AUTQS Agent**, seu assistente especializado em TQS V25 e Engenharia Estrutural.\n\n"
                f"**Edifício ativo selecionado:** `{self.edificio_ativo or 'Nenhum'}`\n\n"
                f"**Comandos que você pode me pedir:**\n"
                f"1. 🏢 *'Quais edifícios tenho no TQS?'* — Lista todos os projetos no disco e status de cálculo.\n"
                f"2. 📐 *'Gere a planta de cargas do edifício 054'* — Emite a prancha DWG nativa completa.\n"
                f"3. 🏆 *'Quais são os pilares mais carregados?'* — Exibe os pilares com maiores valores de $N_k$.\n"
                f"4. ⚠️ *'Tem algum pilar com tração?'* — Varre a fundação em busca de esforços negativos de alívio/arrancamento.\n"
                f"5. 🔄 *'Mudar para o edifício X'* — Alterna o foco para outro projeto."
            )
        }
