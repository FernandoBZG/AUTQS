import os
import sys
import subprocess
import pandas as pd
import streamlit as st

# Garante que a raiz do projeto esteja no sys.path
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

from src.agent.chat_agent import AutqsChatAgent
from src.tqs_adapter.building_reader import TQSBuildingReader

# Configuração da Página
st.set_page_config(
    page_title="AUTQS - Agente de Inteligência Artificial para TQS V25",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização Moderna de Engenharia
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .status-badge-ok {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-badge-warn {
        background-color: #FEF08A;
        color: #713F12;
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Inicialização do Agente e Estado da Sessão
if "agent" not in st.session_state:
    st.session_state.agent = AutqsChatAgent()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Olá, Engenheiro(a)! Sou o **AUTQS Agent**, seu assistente de inteligência artificial "
                "integrado nativamente ao **TQS V25**.\n\n"
                "Posso emitir a **Planta de Cargas e Locação de Fundações** de qualquer edifício, "
                "calcular baricentros analíticos, auditar esforços críticos de tração e flexão, "
                "e gerar arquivos **.DWG nativos** formatados no padrão TQS.\n\n"
                "**Como posso te ajudar hoje?** Você pode clicar nos botões rápidos ao lado ou digitar sua mensagem abaixo."
            ),
            "tipo": "texto",
        }
    ]

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/structural.png", width=64)
    st.title("AUTQS Engine")
    st.caption("Autonomia Cognitiva para TQS V25")
    st.divider()

    st.subheader("🏢 Seleção de Edifício")
    edificios = TQSBuildingReader.listar_edificios_disponiveis()
    nomes_edificios = [e["nome"] for e in edificios]

    # Identifica o índice do edifício padrão (ex: 054)
    default_idx = 0
    for idx, e in enumerate(edificios):
        if "054" in e["nome"]:
            default_idx = idx
            break

    edificio_selecionado = st.selectbox(
        "Edifícios Detectados no TQS:",
        options=nomes_edificios,
        index=default_idx if nomes_edificios else 0,
    )

    ed_info = next((e for e in edificios if e["nome"] == edificio_selecionado), None)
    if ed_info:
        st.session_state.agent.edificio_ativo = ed_info["nome"]
        if ed_info["processado"]:
            st.markdown('<span class="status-badge-ok">● Pronto (Pórtico Espacial OK)</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-badge-warn">▲ Requer Processamento Global</span>', unsafe_allow_html=True)
        
        st.caption(f"📁 `{ed_info['caminho']}`")

    st.divider()
    st.subheader("⚡ Ações Rápidas")

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📐 Gerar DWG", use_container_width=True):
            st.session_state.queued_prompt = f"Gere a planta de cargas do edifício {edificio_selecionado}"
        if st.button("🏆 Top Cargas", use_container_width=True):
            st.session_state.queued_prompt = "Quais são os pilares mais carregados?"
    with col_btn2:
        if st.button("🏢 Listar Obras", use_container_width=True):
            st.session_state.queued_prompt = "Quais edifícios tenho no TQS?"
        if st.button("⚠️ Ver Tração", use_container_width=True):
            st.session_state.queued_prompt = "Tem pilar com esforço de tração?"

    st.divider()
    st.subheader("🤖 Inteligência Artificial")
    gemini_key = st.text_input(
        "Chave Google Gemini API (Opcional):",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        placeholder="Cole sua chave gratuita aqui",
        help="Obtenha uma chave 100% gratuita no Google AI Studio (aistudio.google.com)"
    )
    if gemini_key and len(gemini_key.strip()) > 10:
        st.session_state.agent.set_api_key(gemini_key.strip())
        st.markdown('<span class="status-badge-ok">✨ Gemini 1.5 Flash Conectado</span>', unsafe_allow_html=True)
    else:
        st.caption("🔒 **Modo Local Offline Ativo** (Zero custo, sem internet).")
        st.caption("👉 [Clique aqui para obter uma chave Gemini gratuita](https://aistudio.google.com)")

    st.divider()
    st.caption("ℹ️ **Integração Técnica:**")
    st.caption("- TQS V25 (Build Oficial)")
    st.caption("- TQSPythonInterface x64")
    st.caption("- Template Oficial: GEO_CARGAS.DWG")
    st.caption("- Molduras: Catálogo ABNT / NGE")

# --- ÁREA PRINCIPAL DO CHAT ---
st.markdown('<div class="main-title">AUTQS • Assistente de Projetos Estruturais</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Converse com seu projeto em linguagem natural e gere pranchas DWG nativas no TQS</div>', unsafe_allow_html=True)

# Renderiza histórico de mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Se houver dados tabulares anexados à mensagem
        if "dados" in msg and msg["dados"]:
            dados = msg["dados"]
            if isinstance(dados, list) and len(dados) > 0 and isinstance(dados[0], dict) and "pilar" in dados[0]:
                df = pd.DataFrame(dados)
                
                # Exibe métricas resumo
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total de Pilares", len(df))
                with col2:
                    st.metric("Carga Máxima (Nk)", f"{df['nk_max_tf'].max():.1f} tf")
                with col3:
                    st.metric("Carga Média", f"{df['nk_max_tf'].mean():.1f} tf")
                with col4:
                    trac = len(df[df['nk_max_tf'] < 0])
                    st.metric("Pilares com Tração", trac)

                # Abas para Tabela Interativa e Gráfico de Locação
                tem_porlid = "dados_porlid" in msg and msg["dados_porlid"] and msg["dados_porlid"].get("linhas")
                if tem_porlid:
                    tab_graf, tab_tab, tab_porlid = st.tabs(["📊 Mapa de Locação e Cargas", "📋 Baricentros e Dimensões", "📑 Tabela Oficial TQS (PORLID)"])
                else:
                    tab_graf, tab_tab = st.tabs(["📊 Mapa de Locação e Cargas", "📋 Tabela Detalhada de Pilares"])

                with tab_graf:
                    try:
                        import plotly.express as px
                        import plotly.graph_objects as go

                        fig = px.scatter(
                            df,
                            x="xcg_m",
                            y="ycg_m",
                            size=df["nk_max_tf"].apply(lambda v: max(8, abs(v) * 0.15)),
                            color="nk_max_tf",
                            color_continuous_scale="Viridis",
                            hover_name="pilar",
                            hover_data={
                                "secao_cm": True,
                                "nk_max_tf": ":.1f",
                                "mxk_tfm": ":.2f",
                                "myk_tfm": ":.2f",
                                "xcg_m": ":.2f",
                                "ycg_m": ":.2f",
                            },
                            labels={
                                "xcg_m": "X (metros)",
                                "ycg_m": "Y (metros)",
                                "nk_max_tf": "Nk (tf)",
                            },
                            title="Locação dos Pilares na Fundação e Magnitude da Carga Vertical (Nk)",
                        )
                        # Adiciona anotações com o nome do pilar
                        for _, row in df.iterrows():
                            fig.add_annotation(
                                x=row["xcg_m"],
                                y=row["ycg_m"],
                                text=row["pilar"],
                                showarrow=False,
                                yshift=12,
                                font=dict(size=10, color="black"),
                            )

                        fig.update_layout(
                            height=480,
                            yaxis=dict(scaleanchor="x", scaleratio=1),
                            template="plotly_white",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"Visualização gráfica não disponível: {e}")

                with tab_tab:
                    st.dataframe(
                        df,
                        use_container_width=True,
                        column_config={
                            "pilar": "Pilar",
                            "secao_cm": "Seção (cm)",
                            "xcg_m": st.column_config.NumberColumn("Xcg (m)", format="%.3f"),
                            "ycg_m": st.column_config.NumberColumn("Ycg (m)", format="%.3f"),
                            "nk_max_tf": st.column_config.NumberColumn("Nk Máx (tf)", format="%.1f"),
                            "nk_min_tf": st.column_config.NumberColumn("Nk Mín (tf)", format="%.1f"),
                            "mxk_tfm": st.column_config.NumberColumn("Mx (tf.m)", format="%.2f"),
                            "myk_tfm": st.column_config.NumberColumn("My (tf.m)", format="%.2f"),
                        }
                    )

                if tem_porlid:
                    with tab_porlid:
                        porlid = msg["dados_porlid"]
                        st.caption(f"**Combinação Crítica:** `{porlid.get('titulo')}`")
                        df_porlid = pd.DataFrame(porlid["linhas"], columns=porlid["colunas"])
                        st.dataframe(df_porlid, use_container_width=True)


        # Se houver arquivo DWG gerado
        if "arquivo_dwg" in msg and msg["arquivo_dwg"]:
            dwg_path = msg["arquivo_dwg"]
            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                if os.path.exists(dwg_path):
                    with open(dwg_path, "rb") as file_dwg:
                        st.download_button(
                            label="📥 Baixar Arquivo .DWG",
                            data=file_dwg,
                            file_name=os.path.basename(dwg_path),
                            mime="application/octet-stream",
                            use_container_width=True,
                        )
            with col_d2:
                if st.button("🚀 Abrir no Editor Gráfico TQS (EAGW)", key=f"open_{hash(dwg_path)}", use_container_width=True):
                    try:
                        os.startfile(dwg_path)
                        st.toast("Comando enviado para o TQS!", icon="✅")
                    except Exception as e:
                        st.error(f"Erro ao abrir arquivo: {e}")

# Processamento de Prompt Enfileirado por Botão ou Input do Usuário
prompt = None
if "queued_prompt" in st.session_state and st.session_state.queued_prompt:
    prompt = st.session_state.queued_prompt
    st.session_state.queued_prompt = None
else:
    prompt = st.chat_input("Ex: 'Gere a planta de cargas do edifício 054' ou 'Quais são os pilares mais carregados?'")

if prompt:
    # 1. Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Executa a resposta do Agente de IA com indicador de progresso
    with st.chat_message("assistant"):
        with st.spinner("Processando dados estruturais e integrando ao TQS V25..."):
            resposta = st.session_state.agent.responder(prompt)
            st.markdown(resposta["texto"])

            # Adiciona ao histórico com metadados
            item_historico = {
                "role": "assistant",
                "content": resposta["texto"],
                "tipo": resposta.get("tipo", "texto"),
                "dados": resposta.get("dados"),
                "dados_porlid": resposta.get("dados_porlid"),
                "arquivo_dwg": resposta.get("arquivo_dwg"),
            }

            st.session_state.messages.append(item_historico)
            st.rerun()
