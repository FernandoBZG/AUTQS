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
from src.tqs_adapter.model_editor import TQSModelEditor

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
        margin-bottom: 1.2rem;
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
                "**Principais recursos:**\n"
                "1. 📐 **Planta de Cargas e Locação:** Emissão de pranchas `.DWG` nativas completas e baricentros analíticos.\n"
                "2. 🏗️ **Modelador Estrutural Interativo:** Consulta e edição paramétrica de **Vigas, Lajes e Pilares** (dimensões $b \\times h$, espessuras, desníveis e cargas distribuídas).\n"
                "3. 📊 **Auditoria Estrutural:** Detecção de trações de fundação e rankings de esforços críticos ($N_k, M_x, M_y$).\n\n"
                "Você pode clicar nos botões rápidos ao lado ou conversar comigo em linguagem natural."
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

    st.divider()
    st.caption("ℹ️ **Integração Técnica:**")
    st.caption("- TQS V25 (Build Oficial)")
    st.caption("- TQSPythonInterface x64")
    st.caption("- Modelador Estrutural FINTME.DLL")

# --- ÁREA PRINCIPAL DO CHAT ---
st.markdown('<div class="main-title">AUTQS • Assistente de Engenharia Estrutural</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Interaja em linguagem natural com o TQS V25: emita gabaritos DWG, consulte esforços e edite elementos no Modelador Estrutural</div>', unsafe_allow_html=True)

# Espaço Interativo: Capacidades Detalhadas do Modelo
with st.expander("✨ 💡 **Capacidades do Modelo e Guia de Comandos** (Clique aqui para ver todos os recursos)", expanded=False):
    st.markdown("""
    O **AUTQS** conecta modelos de Inteligência Artificial diretamente ao núcleo computacional do **TQS V25**,
    permitindo consultar, auditar e alterar modelos estruturais em linguagem natural ou inspecionar pranchas completas.
    """)

    tab_cap1, tab_cap2, tab_cap3, tab_cap4, tab_cap5, tab_cap6 = st.tabs([
        "🏗️ Modelador",
        "📐 Cargas & Locação",
        "🔍 Comparação de Formas",
        "🧱 Alvenaria Estrutural",
        "📊 Auditoria & Pilares/Vigas",
        "🤖 Normas & IA",
    ])

    with tab_cap1:
        st.markdown("""
        #### 🏗️ Operações no Modelador Estrutural (Vigas, Lajes, Pilares e Cargas)
        O AUTQS opera diretamente sobre os arquivos de modelo (`.MOD`) através da API nativa em modo batch (`FINTME.DLL`),
        salvando as alterações no disco sem necessidade de abrir janelas.

        * **Vigas:**
          * Consulta de dimensões ($b \\times h$), desníveis/rebaixos, quantidade de nós e extensões lineares.
          * Edição direta de largura ($b$), altura ($h$) e desnível de qualquer viga em qualquer pavimento.
        * **Lajes:**
          * Consulta de espessuras ($h$), desníveis, tipos de laje (maciça/nervurada) e ângulos principais.
          * Alteração de espessura ($h$), desnível e atribuição de carregamentos distribuídos (permanente $g$ e acidental $q$ em $\\text{tf/m}^2$).
        * **Pilares:**
          * Consulta de seções transversais ($b \\times h$) e coordenadas analíticas ($X, Y$) de inserção.
          * Alteração das dimensões de seção transversal dos pilares no pavimento.
        * **Pavimentos:**
          * Resumo de todos os níveis da estrutura com contagem de vigas, lajes, pilares e cargas cadastradas.
        """)
        st.markdown("**💬 Comandos de exemplo que você pode testar no chat:**")
        col_ex1, col_ex2 = st.columns(2)
        with col_ex1:
            if st.button("💬 'Liste os pavimentos do edifício'", key="btn_ex_pav"):
                st.session_state.queued_prompt = f"Liste os pavimentos do edifício {edificio_selecionado}"
                st.rerun()
            if st.button("💬 'Liste as vigas do pavimento térreo'", key="btn_ex_vig"):
                st.session_state.queued_prompt = f"Liste as vigas do pavimento térreo no edifício {edificio_selecionado}"
                st.rerun()
            if st.button("💬 'Mude a viga V1 para 20x60 no térreo'", key="btn_ex_edvig"):
                st.session_state.queued_prompt = f"Mude a viga V1 para 20x60 no pavimento térreo no edifício {edificio_selecionado}"
                st.rerun()
        with col_ex2:
            if st.button("💬 'Quais são as lajes do 2º pavimento?'", key="btn_ex_laj"):
                st.session_state.queued_prompt = f"Quais são as lajes do 2 pavimento no edifício {edificio_selecionado}?"
                st.rerun()
            if st.button("💬 'Altere a laje L3 para espessura 14cm'", key="btn_ex_edlaj"):
                st.session_state.queued_prompt = f"Altere a laje L3 para espessura 14cm no 2 pavimento no edifício {edificio_selecionado}"
                st.rerun()
            if st.button("💬 'Aplique sobrecarga de 0.3 tf/m² na laje L3'", key="btn_ex_carg"):
                st.session_state.queued_prompt = f"Aplique uma carga acidental de 0.3 tf/m² na laje L3 no 2 pavimento no edifício {edificio_selecionado}"
                st.rerun()

    with tab_cap2:
        st.markdown("""
        #### 📐 Emissão de Planta de Cargas e Locação de Fundações
        Gera pranchas oficiais completas em formato `.DWG` nativo do TQS V25 prontas para plotagem e compatíveis com a NBR 6118 / NBR 6122.

        * **Tabela de Cargas Oficial (PORLID):**
          * Extrai as reações e momentos diretamente do `PORLID.DWG` / `PORLIS2.LST` da pasta `ESPACIAL` da obra.
          * Gera 7 colunas por bloco: **Pilar, $F_z$, $F_x$, $F_y$, $M_x$, $M_y$, $M_z$** para cada caso crítico de carga.
        * **Baricentros Analíticos:**
          * Cálculo exato das coordenadas dos baricentros $(X_{cg}, Y_{cg})$ de cada pilar por decomposição de polígonos.
          * Linhas de centro em cruz projetando 50 cm além da seção, com cotas dinâmicas.
        * **Moldura de Projeção Técnica:**
          * Moldura no Nível 100 com Cor 37 (nível oficial não-plotável do TQS), mantendo o desenho limpo para montagem das plantas.
        * **Blocos Informativos de Projeto:**
          * Convenção de Cargas, Incidência de Vento com Rosa dos Ventos e Observações Gerais dinâmicas baseadas nos casos do edifício.
        * **Sincronização na Obra:**
          * Grava automaticamente uma cópia em `ESPACIAL/GABARITO.DWG` para visualização e edição imediata no TQS EAGW.
        """)
        if st.button("📐 'Gere a planta de cargas do edifício'", key="btn_ex_dwg", use_container_width=True):
            st.session_state.queued_prompt = f"Gere a planta de cargas do edifício {edificio_selecionado}"
            st.rerun()

    with tab_cap3:
        st.markdown("""
        #### 🔍 Comparação de Geometrias e Auditoria de Formas (Case 07)
        Compara a última geometria sem revisão no título com a planta de formas ou entre revisões do modelo:
        - Detecta pilares com desvios $(\Delta X, \Delta Y)$ ou novas seções $(\Delta b, \Delta h)$.
        - Identifica vigas e lajes modificadas, novas ou removidas.
        - Emite desenho de sobreposição gráfica técnica (`DIFF_FORMAS_*.DXF`) com fundo em cinza e destaques em verde/ciano/vermelho.
        """)
        col_comp1, col_comp2 = st.columns(2)
        with col_comp1:
            if st.button("🔍 'Compare as geometrias com as formas'", key="btn_ex_comp", use_container_width=True):
                st.session_state.queued_prompt = f"Compare as geometrias com a planta de formas do {edificio_selecionado}"
                st.rerun()
        with col_comp2:
            if st.button("📑 'Auditar consistência da planta de formas'", key="btn_ex_consist", use_container_width=True):
                st.session_state.queued_prompt = f"Verifique a consistência da planta de formas do {edificio_selecionado}"
                st.rerun()

    with tab_cap4:
        st.markdown("""
        #### 🧱 Alvenaria Estrutural (Case 03)
        Geração automatizada de pré-formas de alvenaria estrutural a partir do `DesFiad1.DWG`:
        - Extração de contornos de lajes exteriores e sacadas no Nível 237.
        - Limpeza de poluição gráfica, cotas automáticas de vãos de portas e janelas.
        - Inserção de resumo de materiais (LISTMELV), corte esquemático e moldura oficial.
        """)
        col_alv1, col_alv2 = st.columns(2)
        with col_alv1:
            if st.button("🧱 'Gere a pré-forma do pavimento Tipo A'", key="btn_ex_alv_tipo", use_container_width=True):
                st.session_state.queued_prompt = f"Gere a planta de formas de alvenaria do pavimento Tipo A no edifício {edificio_selecionado}"
                st.rerun()
        with col_alv2:
            if st.button("🧱 'Gere a pré-forma do 2º pavimento'", key="btn_ex_alv_2pav", use_container_width=True):
                st.session_state.queued_prompt = f"Gere a planta de formas de alvenaria do 2 pavimento no edifício {edificio_selecionado}"
                st.rerun()

    with tab_cap5:
        st.markdown("""
        #### 📊 Auditoria Estrutural e Esforços Críticos
        Varre a malha estrutural e o pórtico espacial para alertar sobre condições de risco antes da elaboração do projeto de fundações:

        * **Detecção de Tração na Fundação ($N_k < 0$):**
          * Identifica pilares com esforços axiais negativos de tração provocados por vento ou excentricidades excessivas, alertando para dimensionar armaduras de arrancamento em estacas ou sapatas.
        * **Ranking dos Pilares Mais Carregados:**
          * Classifica os pilares com maiores solicitações normais ($N_k$) e momentos fletores ($M_x, M_y$) para subsidiar a escolha do tipo de fundação com o projetista geotécnico.
        """)
        col_aud1, col_aud2 = st.columns(2)
        with col_aud1:
            if st.button("⚠️ 'Tem algum pilar com esforço de tração?'", key="btn_ex_trac", use_container_width=True):
                st.session_state.queued_prompt = "Tem pilar com esforço de tração?"
                st.rerun()
        with col_aud2:
            if st.button("🏆 'Quais são os pilares mais carregados?'", key="btn_ex_top", use_container_width=True):
                st.session_state.queued_prompt = "Quais são os pilares mais carregados?"
                st.rerun()

    with tab_cap7:
        st.markdown("""
        #### 🌐 Estabilidade Global (NBR 6118) e Auditoria de Lajes
        - **Estabilidade Global:** Audita $\gamma_z$, $FAV_t$, $\alpha$ e drift de vento em ELS ($H/1700$ e $H_i/850$).
        - **Auditoria de Lajes & Grelhas:** Detecta balanços não travados, bordos livres em concavidade e riscos de flecha excessiva.
        """)
        col_es1, col_es2 = st.columns(2)
        with col_es1:
            if st.button("🌐 'Auditar estabilidade global (GamaZ e Drift)'", key="btn_ex_estab", use_container_width=True):
                st.session_state.queued_prompt = f"Auditar a estabilidade global e deslocamentos do edifício {edificio_selecionado}"
                st.rerun()
        with col_es2:
            if st.button("📑 'Auditar lajes, grelhas e flechas'", key="btn_ex_lajes", use_container_width=True):
                st.session_state.queued_prompt = f"Auditar lajes e grelha do edifício {edificio_selecionado}"
                st.rerun()

    with tab_cap8:
        st.markdown("""
        #### 📦 Quantitativos Globais e Memorial Descritivo Automático
        - **Quantitativo Global:** Volume de concreto, fôrmas, consumo de aço, espessura média ($e_m$) e carbono ($kgCO_2$).
        - **Memorial Descritivo:** Gera documentação técnica e justificativa de cálculo em Markdown e HTML pronta para impressão.
        """)
        col_qm1, col_qm2 = st.columns(2)
        with col_qm1:
            if st.button("📊 'Extrair quantitativo global de materiais'", key="btn_ex_quant", use_container_width=True):
                st.session_state.queued_prompt = f"Extrair quantitativo de materiais do edifício {edificio_selecionado}"
                st.rerun()
        with col_qm2:
            if st.button("📄 'Gerar memorial descritivo da obra'", key="btn_ex_memo", use_container_width=True):
                st.session_state.queued_prompt = f"Gerar memorial descritivo do edifício {edificio_selecionado}"
                st.rerun()

    with tab_cap6:
        st.markdown("""
        #### 🤖 Raciocínio de Engenharia e Consultoria Normativa (Google Gemini)
        Quando ativado com uma chave gratuita do Google Gemini, o AUTQS atua como um engenheiro estrutural sênior:

        * **Normas Técnicas Brasileiras:**
          * Orientações detalhadas sobre NBR 6118 (concreto armado), NBR 6122 (fundações) e NBR 8681 (ações e segurança).
        * **Pré-dimensionamento e Boas Práticas:**
          * Estimativa de alturas econômicas para vigas ($h \\approx L/10$ a $L/12$), espessuras de lajes maciças/nervuradas e verificação de flechas em ELS.
        * **Interpretação de Relatórios:**
          * Explicação de esforços, envoltórias e hipóteses de cálculo do TQS.
        """)
        st.caption("👉 Obtenha sua chave gratuita em [Google AI Studio (aistudio.google.com)](https://aistudio.google.com) e cole no campo da barra lateral.")

st.markdown("<br>", unsafe_allow_html=True)

# Renderiza histórico de mensagens
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Se houver dados tabulares anexados à mensagem
        if "dados" in msg and msg["dados"]:
            dados = msg["dados"]
            # Caso 1: Pilares da Fundação (Planta de Cargas)
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

            # Caso 2: Pavimentos do Modelador Estrutural
            elif isinstance(dados, list) and len(dados) > 0 and isinstance(dados[0], dict) and "num_vigas" in dados[0]:
                df_pav = pd.DataFrame(dados)
                st.dataframe(
                    df_pav,
                    use_container_width=True,
                    column_config={
                        "indice": "#",
                        "nome": "Pavimento",
                        "num_vigas": "Total Vigas",
                        "num_lajes": "Total Lajes",
                        "num_pilares": "Total Pilares",
                    }
                )

            # Caso 3: Elementos de Pavimento (Vigas, Lajes, Pilares)
            elif isinstance(dados, dict):
                if "vigas" in dados and dados["vigas"]:
                    df_v = pd.DataFrame(dados["vigas"])
                    st.caption(f"**Tabela Detalhada de Vigas ({len(df_v)} vigas):**")
                    cols_show = [c for c in ["nome", "b_cm", "h_cm", "desnivel_cm", "num_nos"] if c in df_v.columns]
                    st.dataframe(df_v[cols_show], use_container_width=True)

                if "lajes" in dados and dados["lajes"]:
                    df_l = pd.DataFrame(dados["lajes"])
                    st.caption(f"**Tabela Detalhada de Lajes ({len(df_l)} lajes):**")
                    cols_show = [c for c in ["nome", "espessura_cm", "desnivel_cm", "tipo_descricao", "angulo_principal_graus"] if c in df_l.columns]
                    st.dataframe(df_l[cols_show], use_container_width=True)

                if "pilares" in dados and dados["pilares"]:
                    df_p = pd.DataFrame(dados["pilares"])
                    st.caption(f"**Tabela Detalhada de Pilares ({len(df_p)} pilares):**")
                    cols_show = [c for c in ["nome", "secao_cm", "x_m", "y_m"] if c in df_p.columns]
                    st.dataframe(df_p[cols_show], use_container_width=True)

        # Se houver memorial gerado (.html / .md)
        if "arquivo_html" in msg and msg["arquivo_html"] and os.path.exists(msg["arquivo_html"]):
            with open(msg["arquivo_html"], "r", encoding="utf-8") as f_html:
                st.download_button(
                    label="📄 Baixar Memorial Descritivo em HTML (Pronto para PDF/Impressão)",
                    data=f_html.read(),
                    file_name=os.path.basename(msg["arquivo_html"]),
                    mime="text/html",
                    use_container_width=True,
                )

        # Se houver arquivo DWG gerado
        if "arquivo_dwg" in msg and msg["arquivo_dwg"]:
            dwg_path = msg["arquivo_dwg"]
            col_d1, col_d2 = st.columns([1, 2])
            with col_d1:
                if os.path.exists(dwg_path):
                    with open(dwg_path, "rb") as file_dwg:
                        st.download_button(
                            label=f"📥 Baixar Arquivo {os.path.splitext(dwg_path)[1].upper()}",
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
    prompt = st.chat_input("Ex: 'Mude a viga V1 para 20x60 no térreo' ou 'Liste as lajes do 2 pavimento'")

if prompt:
    # 1. Adiciona a mensagem do usuário ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Executa a resposta do Agente de IA com indicador de progresso
    with st.chat_message("assistant"):
        with st.spinner("Processando dados e integrando ao Modelador Estrutural TQS V25..."):
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
                "arquivo_md": resposta.get("arquivo_md"),
                "arquivo_html": resposta.get("arquivo_html"),
            }

            st.session_state.messages.append(item_historico)
            st.rerun()
