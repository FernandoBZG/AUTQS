import os
import sys
import struct

# TQS V25 requer Python 64-bit para carregar as DLLs nativas (X64)
if struct.calcsize("P") * 8 == 32:
    import subprocess
    import shutil
    raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env = os.environ.copy()
    env["PYTHONPATH"] = raiz_projeto + os.pathsep + env.get("PYTHONPATH", "")

    # 1. Tenta o launcher oficial do Windows 'py -3-64'
    if shutil.which("py"):
        try:
            res = subprocess.run(["py", "-3-64"] + sys.argv, cwd=os.getcwd(), env=env)
            sys.exit(res.returncode)
        except Exception:
            pass

    # 2. Varredura dinâmica de interpretadores Python 64-bit no sistema
    local_app = os.environ.get("LOCALAPPDATA", "")
    prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    py64_candidatos = [
        os.path.join(local_app, r"Programs\Python\Python311\python.exe"),
        os.path.join(local_app, r"Programs\Python\Python312\python.exe"),
        os.path.join(local_app, r"Programs\Python\Python313\python.exe"),
        os.path.join(prog_files, r"Python311\python.exe"),
        os.path.join(prog_files, r"Python312\python.exe"),
        os.path.join(prog_files, r"Python313\python.exe"),
        r"C:\Program Files\Python311\python.exe",
        r"C:\Program Files\Python312\python.exe",
    ]
    for py64 in py64_candidatos:
        if py64 and os.path.exists(py64):
            res = subprocess.run([py64] + sys.argv, cwd=os.getcwd(), env=env)
            sys.exit(res.returncode)

    print("[ERRO CRÍTICO] As DLLs do TQS V25 requerem Python de 64 bits (x64).")
    print("O processo atual está sendo executado em 32 bits e nenhum Python 64-bit foi localizado.")
    print("Instale o Python 3.10+ (64-bit) ou execute via: py -3-64 -m src.ui.cli")
    sys.exit(1)

# Garante que a raiz do projeto esteja no sys.path
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Configura stdout e stderr para UTF-8 no Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import argparse
import json
import shutil

from src.agent.orchestrator import AutqsAgentOrchestrator
from src.tqs_adapter.building_reader import TQSBuildingReader
from src.tqs_adapter.model_editor import TQSModelEditor
from src.drawing.sheet_builder import PlantaDeCargasDwgBuilder
from src.core.models import PilarFundacao, GeometriaPilar, TipoSecao, EsforcosFundacao

def solicitar_aprovacao_modificacao(
    edificio: str,
    pavimento: str,
    elemento_tipo: str,
    elemento_nome: str,
    parametros: list,
    auto_aprovar: bool = False
) -> bool:
    """
    Exibe um resumo detalhado da modificação proposta no modelo estrutural e
    solicita aprovação explícita do usuário antes de aplicar qualquer alteração.

    Retorna True se aprovado, False se cancelado.
    """
    print("\n" + "=" * 75)
    print("   SOLICITAÇÃO DE APROVAÇÃO: MODIFICAÇÃO NO MODELO ESTRUTURAL TQS")
    print("=" * 75)
    print(f"Edifício:  {edificio}")
    print(f"Pavimento: {pavimento.upper()}")
    print(f"Elemento:  {elemento_tipo.capitalize()} {elemento_nome}\n")
    print("ALTERAÇÕES PROPOSTAS:")
    print(f"{'Parâmetro':<24} | {'Atual':<16} | {'Proposto':<16}")
    print("-" * 62)
    for param, atual, proposto in parametros:
        print(f"{param:<24} | {atual:<16} | {proposto:<16}")
    print("-" * 62)
    print("REGRA DE SEGURANÇA: Toda modificação no modelo estrutural deve ser aprovada pelo usuário.")

    if auto_aprovar:
        print("\n[AUTO-APROVADO] Confirmação concedida via flag (--sim / -y). Aplicando alteração...")
        return True

    try:
        resp = input("\nDeseja aprovar e aplicar esta modificação no modelo? [s/N]: ").strip().lower()
        aprovado = resp in ["s", "sim", "y", "yes"]
        if aprovado:
            print("[APROVADO] Modificação autorizada pelo usuário. Gravando no modelo estrutural...\n")
            return True
        else:
            print("\n[CANCELADO] Modificação rejeitada pelo usuário. O modelo estrutural permanece inalterado.\n")
            return False
    except (KeyboardInterrupt, EOFError):
        print("\n[CANCELADO] Operação interrompida. Nenhuma modificação foi aplicada ao modelo.\n")
        return False

def main():
    parser = argparse.ArgumentParser(description="AUTQS CLI - Plataforma de IA e Automação para TQS V25")
    parser.add_argument("--edificio", type=str, default=None, help="Nome ou código do edifício TQS (ex: '054' ou nome completo)")
    parser.add_argument("--desenho", type=str, default=None, help="Caminho do arquivo de desenho de saída (DWG/DXF)")
    parser.add_argument("--origem-x", type=float, default=None, help="Coordenada X (cm) da origem (0,0) das cotas relativas")
    parser.add_argument("--origem-y", type=float, default=None, help="Coordenada Y (cm) da origem (0,0) das cotas relativas")
    parser.add_argument("--listar", "-l", action="store_true", help="Lista todos os edifícios encontrados no sistema TQS")
    parser.add_argument("--chat", "-c", action="store_true", help="Inicia o chat interativo no terminal com o Agente AUTQS")
    parser.add_argument("--processar", "-p", nargs="?", const="portico_cargas", default=None, help="Executa o processamento do edifício no TQS (opções: 'portico_cargas' ou 'global')")
    parser.add_argument("--formas-alvenaria", action="store_true", help="Gera a Planta de Formas de Alvenaria Estrutural (1ª Fiada) executiva")
    parser.add_argument("--geometria-ca", "--geo-ca", action="store_true", help="Gera a prancha executiva de Geometria/Formas de Concreto Armado (GEO_<PAVIMENTO>.DWG)")
    parser.add_argument("--tools", action="store_true", help="Lista as ferramentas disponíveis para o Agente de IA")

    # Opções do Modelador Estrutural
    parser.add_argument("--pavimentos", action="store_true", help="Lista todos os pavimentos do modelo estrutural")
    parser.add_argument("--pavimento", type=str, default=None, help="Nome do pavimento a inspecionar/editar (ex: 'terreo', '2')")
    parser.add_argument("--vigas", action="store_true", help="Lista vigas do pavimento selecionado")
    parser.add_argument("--lajes", action="store_true", help="Lista lajes do pavimento selecionado")
    parser.add_argument("--pilares", action="store_true", help="Lista pilares do pavimento selecionado")
    parser.add_argument("--analisar-pilares", "-ap", action="store_true", help="Analisa e diagnostica os pilares do edifício (erros, taxas de armadura, superdimensionamento)")
    parser.add_argument("--otimizar-pilares", "-op", action="store_true", help="Gera propostas de otimização de seções dos pilares e cálculo de economia")
    parser.add_argument("--pilar", type=str, default=None, help="Filtra a análise ou edição para um pilar específico (ex: 'P4')")
    parser.add_argument("--largura-fixa", action="store_true", help="Na otimização de pilares, mantém a largura b e altera só o comprimento h")
    parser.add_argument("--json", action="store_true", help="Retorna a saída da análise estrutural em formato JSON serializável")
    parser.add_argument("--editar-viga", type=str, default=None, help="Nome da viga para editar (ex: 'V1')")
    parser.add_argument("--editar-laje", type=str, default=None, help="Nome da laje para editar (ex: 'L3')")
    parser.add_argument("--editar-pilar", type=str, default=None, help="Nome do pilar para editar (ex: 'P4')")
    parser.add_argument("--b", type=float, default=None, help="Largura b da viga ou pilar em cm")
    parser.add_argument("--h", type=float, default=None, help="Altura h da viga ou pilar em cm")
    parser.add_argument("--espessura", type=float, default=None, help="Espessura da laje em cm")
    parser.add_argument("--desnivel", type=float, default=None, help="Desnível / rebaixo em cm")
    parser.add_argument("--carga-perm", type=float, default=None, help="Carga permanente g em tf/m²")
    parser.add_argument("--consistencia", "--verificar-consistencia", "-vc", action="store_true", help="Verifica e audita a consistência da planta de formas no TQS (apoios nulos, nós fora do pilar, vigas sem apoio)")
    parser.add_argument("--sem-processar", action="store_true", help="Na verificação de consistência, analisa listagens existentes sem redisparar o cálculo batch do TQS")
    parser.add_argument("--analisar-vigas", "-av", action="store_true", help="Analisa e audita esforços, dimensionamento e bielas das vigas no TQS (RELGER, ESTRIB, RESESTERR)")
    parser.add_argument("--viga", type=str, default=None, help="Filtra a análise para uma viga específica (ex: 'V21')")
    parser.add_argument("--comparar-formas", "--diff-formas", "-cf", action="store_true", help="Compara duas plantas de formas/geometrias no TQS para auditar o que mudou no software")
    parser.add_argument("--edificio-comp", type=str, default=None, help="Nome do edifício comparado (revisão R01, pasta de teste ou comparada)")
    parser.add_argument("--pavimento-comp", type=str, default=None, help="Nome do pavimento comparado no edifício comparado")
    parser.add_argument("--sem-desenho", action="store_true", help="Não gera o desenho DXF de sobreposição gráfica comparativa")
    parser.add_argument("--sim", "-y", "--yes", action="store_true", help="Aprova automaticamente qualquer modificação no modelo estrutural sem solicitar confirmação interativa")
    parser.add_argument("--estabilidade", "-eg", action="store_true", help="Audita a estabilidade global (GamaZ, FAVt, Alfa) e deslocamentos de vento em ELS conforme a NBR 6118")
    parser.add_argument("--auditar-lajes", "--lajes-audit", "-al", action="store_true", help="Audita lajes, grelhas, balanços e riscos de flechas excessivas no edifício")
    parser.add_argument("--quantitativos", "-qm", action="store_true", help="Extrai o quantitativo global de materiais (concreto, formas, aço) e pegada de carbono")
    parser.add_argument("--memorial", action="store_true", help="Gera o Memorial Descritivo e Justificativo de Cálculo Estrutural em Markdown e HTML")
    parser.add_argument("--limpar-arq", action="store_true", help="Higieniza e padroniza DWG/DXF de arquitetura para referência externa Geo_*.DWG")
    parser.add_argument("--arquivo-arq", type=str, default=None, help="Caminho do arquivo CAD de arquitetura a ser higienizado")

    args = parser.parse_args()
    orchestrator = AutqsAgentOrchestrator()

    # 1. Auditoria de Estabilidade Global (Case 08)
    if args.estabilidade:
        ed = args.edificio or "054"
        res = orchestrator.registry.executar_ferramenta("auditar_estabilidade_global", {"edificio_nome": ed, "formato": "resumo"})
        if res.get("sucesso") or res.get("status") == "sucesso":
            print(res.get("resumo_executivo"))
        else:
            print(f"[ERRO] {res.get('mensagem', 'Falha ao auditar estabilidade.')}")
        return

    # 2. Auditoria de Lajes e Grelhas (Case 09)
    if args.auditar_lajes:
        ed = args.edificio or "054"
        params = {"edificio_nome": ed, "formato": "resumo"}
        if args.pavimento:
            params["pavimento"] = args.pavimento
        res = orchestrator.registry.executar_ferramenta("auditar_lajes_edificio", params)
        if res.get("sucesso") or res.get("status") == "sucesso":
            print(res.get("resumo_executivo"))
        else:
            print(f"[ERRO] {res.get('mensagem', 'Falha ao auditar lajes.')}")
        return

    # 3. Quantitativo Global de Materiais e Índices de Consumo (Case 10)
    if args.quantitativos:
        ed = args.edificio or "054"
        res = orchestrator.registry.executar_ferramenta("extrair_quantitativo_materiais", {"edificio_nome": ed, "formato": "resumo"})
        if res.get("sucesso") or res.get("status") == "sucesso":
            print(res.get("resumo_executivo"))
        else:
            print(f"[ERRO] {res.get('mensagem', 'Falha ao extrair quantitativos.')}")
        return

    # 4. Memorial Descritivo e Justificativo de Cálculo (Case 11)
    if args.memorial:
        ed = args.edificio or "054"
        p_md = f"memorial_{ed}.md"
        p_html = f"memorial_{ed}.html"
        res = orchestrator.registry.executar_ferramenta("gerar_memorial_descritivo", {
            "edificio_nome": ed,
            "caminho_saida_md": p_md,
            "caminho_saida_html": p_html
        })
        if res.get("sucesso") or res.get("status") == "sucesso":
            print(res.get("resumo_executivo"))
            print(f"\n[OK] Arquivos salvos com sucesso:")
            print(f"     - Markdown: {os.path.abspath(p_md)}")
            print(f"     - HTML:     {os.path.abspath(p_html)}")
        else:
            print(f"[ERRO] {res.get('mensagem', 'Falha ao gerar memorial.')}")
        return

    # 5. Limpeza e Padronização de Arquitetura CAD (Case 12)
    if args.limpar_arq:
        caminho_in = args.arquivo_arq or args.desenho
        if not caminho_in:
            print("[ERRO] Informe o arquivo de arquitetura com --arquivo-arq <caminho.dxf>")
            return
        res = orchestrator.registry.executar_ferramenta("padronizar_arquitetura_tqs", {"caminho_arquivo": caminho_in})
        if res.get("sucesso") or res.get("status") == "sucesso":
            print(res.get("resumo_executivo"))
            print(f"\n[OK] Desenho limpo gerado: {res.get('arquivo_gerado')}")
        else:
            print(f"[ERRO] {res.get('mensagem', 'Falha ao limpar arquitetura.')}")
        return

    # Chat Interativo no Terminal
    if args.chat:
        from src.agent.chat_agent import AutqsChatAgent
        print("\n" + "=" * 65)
        print("   AUTQS AGENT - CHAT INTERATIVO DE ENGENHARIA ESTRUTURAL")
        print("=" * 65)
        print("Converse em linguagem natural com o TQS V25.")
        print("Digite 'sair' para encerrar a sessão.\n")

        agent = AutqsChatAgent()
        if args.edificio:
            agent.edificio_ativo = args.edificio
        while True:
            try:
                user_msg = input("\n[Engenheiro] > ").strip()
                if not user_msg or user_msg.lower() in ["sair", "exit", "quit", "q"]:
                    print("\nEncerrando sessão do AUTQS. Até logo!")
                    break
                resp = agent.responder(user_msg)
                print("\n[AUTQS Agent]:\n" + resp["texto"])
            except (KeyboardInterrupt, EOFError):
                print("\nSessão finalizada.")
                break
        return

    # Listagem de Edifícios
    if args.listar:
        print("\n=========================================================")
        print("          EDIFÍCIOS DETECTADOS NO SISTEMA TQS            ")
        print("=========================================================")
        eds = TQSBuildingReader.listar_edificios_disponiveis()
        if not eds:
            print("Nenhum edifício foi localizado nas pastas padrão (C:\\TQS, D:\\TQS).")
        else:
            print(f"{'Edifício':<45} | {'Pronto para Emissão?':<22}")
            print("-" * 72)
            for e in eds:
                status = "SIM (Pórtico OK)" if e["processado"] else "NÃO (Requer Processamento)"
                print(f"{e['nome']:<45} | {status:<22}")
            print("\nPara gerar a planta de cargas de qualquer um dos edifícios acima, use:")
            print("  python -m src.ui.cli --edificio <NOME_OU_CODIGO>")
        return

    # Listagem de Ferramentas Function Calling
    if args.tools:
        print("\n=== FERRAMENTAS DISPONÍVEIS NO AUTQS (FUNCTION CALLING) ===")
        print(json.dumps(orchestrator.listar_ferramentas(), indent=2, ensure_ascii=False))
        return

    # Análise e Diagnóstico de Pilares
    if args.analisar_pilares or args.otimizar_pilares:
        ed = args.edificio or "054"
        formato = "json" if args.json else "terminal"
        res = orchestrator.registry.executar_ferramenta("analisar_pilares_edificio", {
            "edificio_nome": ed,
            "pilar": args.pilar,
            "formato": formato,
            "largura_fixa": args.largura_fixa
        })
        if args.json:
            print(json.dumps(res.get("dados_completos", res), indent=2, ensure_ascii=False))
        else:
            print(res.get("resumo_executivo", ""))
        return

    # Geração de Geometria de Concreto Armado (GEO_<PAVIMENTO>.DWG)
    if getattr(args, "geometria_ca", False):
        ed = args.edificio or "055"
        pav = args.pavimento or "PISO DO SUBSOLO 1"
        print(f"\n=========================================================")
        print(f"   AUTQS - GEOMETRIA DE CONCRETO ARMADO (GEO)")
        print(f"=========================================================")
        print(f"Edifício:  {ed}")
        print(f"Pavimento: {pav}\n")
        res = orchestrator.registry.executar_ferramenta("gerar_geometria_concreto_armado", {
            "edificio_nome": ed,
            "pavimento": pav,
            "escala": 50
        })
        if res.get("status") == "sucesso":
            aud = res.get("auditoria", {})
            print(f"[OK] GEOMETRIA DE CONCRETO ARMADO GERADA COM SUCESSO:")
            print(f"     Arquivo:   {res.get('caminho_geo')}")
            print(f"     Vigas:     {aud.get('total_vigas')} vigas identificadas")
            print(f"     Elementos: {aud.get('total_elementos')} elementos gráficos")
            print(f"     Moldura:   180-70 Nível 100 ({aud.get('moldura_elementos')} elementos)")
            print(f"     Notas:     {aud.get('notas_elementos')} elementos de notas técnicas e legendas")
            print(f"\nAbra o desenho diretamente no TQS (Menu Arquivo > Abrir Desenho) para visualização e plotagem.")
        else:
            print(f"[ERRO] Falha ao gerar geometria: {res.get('erro')}")
        return

    # Geração de Planta de Formas de Alvenaria Estrutural (1ª Fiada)
    if args.formas_alvenaria:
        ed = args.edificio or "054"
        pav = (args.pavimento or "TIPO A").upper()
        print(f"\n=========================================================")
        print(f"   AUTQS - FORMAS DE ALVENARIA ESTRUTURAL (1ª FIADA)")
        print(f"=========================================================")
        print(f"Edifício:  {ed}")
        print(f"Pavimento: {pav}\n")
        res = orchestrator.registry.executar_ferramenta("gerar_planta_formas_alvenaria", {
            "edificio_nome": ed,
            "pavimento": pav,
            "caminho_saida_dwg": args.desenho
        })
        if res.get("status") == "sucesso":
            aud = res.get("auditoria", {})
            print(f"[OK] PLANTA DE FORMAS GERADA COM SUCESSO:")
            print(f"     Arquivo:   {res.get('caminho_dwg')}")
            print(f"     Lajes:     {res.get('total_lajes')} identificadas e sobrepostas")
            print(f"     Vãos:      {res.get('total_vaos')} aberturas cotadas")
            print(f"     Textos:    {aud.get('total_textos')} textos normativos (h_min = {aud.get('min_text_height_papel_cm'):.2f} cm no papel)")
            print(f"     Moldura:   {res.get('moldura')} (Escala 1:{res.get('escala')})")
            print(f"\nAbra o desenho diretamente no TQS (Menu Arquivo > Abrir Desenho) para visualização e plotagem.")
        else:
            print(f"[ERRO] Falha ao gerar formas: {res.get('erro')}")
        return

    # Verificação e Auditoria de Consistência de Formas no TQS
    if args.consistencia:
        ed = args.edificio or "054"
        formato = "json" if args.json else "terminal"
        executar_tqs = not args.sem_processar
        pav_str = args.pavimento.upper() if args.pavimento else "TODOS"
        print(f"\n=========================================================")
        print(f"   AUTQS - AUDITORIA DE CONSISTÊNCIA DE FORMAS TQS")
        print(f"=========================================================")
        print(f"Edifício:   {ed}")
        print(f"Pavimento:  {pav_str}")
        print(f"Processamento: {'Recalcular via TQS (PROC FORMAS 2 1)' if executar_tqs else 'Leitura rápida de relatórios existentes'}\n")

        res = orchestrator.registry.executar_ferramenta("verificar_consistencia_planta", {
            "edificio_nome": ed,
            "pavimento": args.pavimento,
            "executar_tqs": executar_tqs,
            "formato": formato
        })

        if args.json:
            print(json.dumps(res.get("dados_pavimentos", res), indent=2, ensure_ascii=False))
        else:
            print(res.get("resumo_executivo", ""))
        return

    # Análise Estrutural e Auditoria de Vigas (Esforços, Bielas e Detalhamento)
    if args.analisar_vigas:
        ed = args.edificio or "054"
        formato = "json" if args.json else "terminal"
        pav_str = args.pavimento.upper() if args.pavimento else "TODOS"
        print(f"\n=========================================================")
        print(f"   AUTQS - AUDITORIA ESTRUTURAL DE VIGAS CAD/TQS")
        print(f"=========================================================")
        print(f"Edifício:   {ed}")
        print(f"Pavimento:  {pav_str}")
        if args.viga:
            print(f"Filtro:     Viga {args.viga.upper()}")
        print(f"Listagens:  RELGER.LST, ESTRIB.LST, RESESTERR.LST, ORDCON.LST\n")

        res = orchestrator.registry.executar_ferramenta("analisar_vigas_pavimento", {
            "edificio_nome": ed,
            "pavimento": args.pavimento,
            "viga": args.viga,
            "formato": formato
        })

        if args.json:
            print(json.dumps(res.get("dados_completos", res), indent=2, ensure_ascii=False))
        else:
            print(res.get("resumo_executivo", ""))
        return

    # Comparação de Geometrias e Plantas de Formas (Diff / O que alterou no software)
    if args.comparar_formas:
        ed_base = args.edificio or "054"
        pav_base = args.pavimento or "terreo"
        ed_comp = args.edificio_comp or ed_base
        pav_comp = args.pavimento_comp or pav_base
        formato = "json" if args.json else "terminal"
        gerar_desenho = not args.sem_desenho

        res = orchestrator.registry.executar_ferramenta("comparar_geometrias_formas", {
            "edificio_base": ed_base,
            "pavimento_base": pav_base,
            "edificio_comparado": ed_comp,
            "pavimento_comparado": pav_comp,
            "gerar_desenho_diff": gerar_desenho,
            "caminho_saida_diff": args.desenho,
            "formato": formato
        })

        if args.json:
            print(json.dumps(res.get("dados_completos", res), indent=2, ensure_ascii=False))
        else:
            print(res.get("resumo_executivo", ""))
        return

    # Operações do Modelador Estrutural via CLI
    tem_op_modelo = (
        args.pavimentos or args.vigas or args.lajes or args.pilares
        or args.editar_viga or args.editar_laje or args.editar_pilar
    )
    if tem_op_modelo:
        ed = args.edificio or "054"
        pav = args.pavimento or "terreo"
        print(f"\n=========================================================")
        print(f"   AUTQS - MODELADOR ESTRUTURAL TQS: EDIFÍCIO {ed}")
        print(f"=========================================================")

        try:
            with TQSModelEditor(ed) as editor:
                print(f"Edifício: {editor.nome_edificio}")
                print(f"Pasta:    {editor.caminho_edificio}\n")

                if args.pavimentos:
                    pavs = editor.listar_pavimentos()
                    print(f"{'#':<3} | {'Pavimento':<30} | {'Vigas':<7} | {'Lajes':<7} | {'Pilares':<7}")
                    print("-" * 62)
                    for p in pavs:
                        print(f"{p['indice']:<3} | {p['nome']:<30} | {p['num_vigas']:<7} | {p['num_lajes']:<7} | {p['num_pilares']:<7}")
                    return

                if args.editar_viga:
                    viga_atual = editor.obter_viga(pav, args.editar_viga)
                    if not viga_atual:
                        print(f"[ERRO] Viga '{args.editar_viga}' não foi encontrada no pavimento '{pav}'.")
                        return

                    b_atual = viga_atual.get("b_cm", 0.0)
                    h_atual = viga_atual.get("h_cm", 0.0)
                    desn_atual = viga_atual.get("desnivel_cm", 0.0)

                    b_novo = args.b if args.b is not None else b_atual
                    h_novo = args.h if args.h is not None else h_atual
                    desn_novo = args.desnivel if args.desnivel is not None else desn_atual

                    alteracoes = []
                    if args.b is not None:
                        alteracoes.append(("Largura (b)", f"{b_atual:.0f} cm", f"{b_novo:.0f} cm"))
                    if args.h is not None:
                        alteracoes.append(("Altura (h)", f"{h_atual:.0f} cm", f"{h_novo:.0f} cm"))
                    if args.desnivel is not None:
                        alteracoes.append(("Desnível", f"{desn_atual:.1f} cm", f"{desn_novo:.1f} cm"))

                    if not alteracoes:
                        print("[AVISO] Nenhuma alteração informada (--b, --h ou --desnivel).")
                        return

                    if not solicitar_aprovacao_modificacao(
                        editor.nome_edificio, pav, "Viga", viga_atual["nome"], alteracoes, auto_aprovar=args.sim
                    ):
                        return

                    res_ed = editor.editar_viga(pav, args.editar_viga, b_cm=args.b, h_cm=args.h, desnivel_cm=args.desnivel)
                    print(f"✅ {res_ed['mensagem']}")
                    print(f"   Dimensões Anteriores: {res_ed['antes']['b_cm']:.0f}x{res_ed['antes']['h_cm']:.0f} cm")
                    print(f"   Novas Dimensões:     {res_ed['depois']['b_cm']:.0f}x{res_ed['depois']['h_cm']:.0f} cm")
                    return

                if args.editar_laje:
                    laje_atual = editor.obter_laje(pav, args.editar_laje)
                    if not laje_atual:
                        print(f"[ERRO] Laje '{args.editar_laje}' não foi encontrada no pavimento '{pav}'.")
                        return

                    esp_atual = laje_atual.get("espessura_cm", 0.0)
                    desn_atual = laje_atual.get("desnivel_cm", 0.0)

                    esp_novo = args.espessura if args.espessura is not None else esp_atual
                    desn_novo = args.desnivel if args.desnivel is not None else desn_atual

                    alteracoes = []
                    if args.espessura is not None:
                        alteracoes.append(("Espessura (h)", f"{esp_atual:.1f} cm", f"{esp_novo:.1f} cm"))
                    if args.desnivel is not None:
                        alteracoes.append(("Desnível", f"{desn_atual:.1f} cm", f"{desn_novo:.1f} cm"))
                    if args.carga_perm is not None:
                        alteracoes.append(("Carga Perm. (g)", "-", f"{args.carga_perm:.2f} tf/m²"))
                    if args.carga_acid is not None:
                        alteracoes.append(("Carga Acid. (q)", "-", f"{args.carga_acid:.2f} tf/m²"))

                    if not alteracoes:
                        print("[AVISO] Nenhuma alteração informada (--espessura, --desnivel, --carga-perm ou --carga-acid).")
                        return

                    if not solicitar_aprovacao_modificacao(
                        editor.nome_edificio, pav, "Laje", laje_atual["nome"], alteracoes, auto_aprovar=args.sim
                    ):
                        return

                    res_ed = editor.editar_laje(
                        pav, args.editar_laje,
                        espessura_cm=args.espessura,
                        desnivel_cm=args.desnivel,
                        carga_permanente_tf_m2=args.carga_perm,
                        carga_acidental_tf_m2=args.carga_acid
                    )
                    print(f"✅ {res_ed['mensagem']}")
                    print(f"   Espessura Anterior: {res_ed['antes']['espessura_cm']:.1f} cm")
                    print(f"   Nova Espessura:     {res_ed['depois']['espessura_cm']:.1f} cm")
                    if res_ed.get("cargas_aplicadas"):
                        print(f"   Cargas Atualizadas: {res_ed['cargas_aplicadas']}")
                    return

                if args.editar_pilar:
                    pilar_atual = editor.obter_pilar(pav, args.editar_pilar)
                    if not pilar_atual:
                        print(f"[ERRO] Pilar '{args.editar_pilar}' não foi encontrado no pavimento '{pav}'.")
                        return

                    b_atual = pilar_atual.get("b_cm", 0.0)
                    h_atual = pilar_atual.get("h_cm", 0.0)

                    b_novo = args.b if args.b is not None else b_atual
                    h_novo = args.h if args.h is not None else h_atual

                    alteracoes = []
                    if args.b is not None:
                        alteracoes.append(("Largura (b)", f"{b_atual:.0f} cm", f"{b_novo:.0f} cm"))
                    if args.h is not None:
                        alteracoes.append(("Comprimento (h)", f"{h_atual:.0f} cm", f"{h_novo:.0f} cm"))

                    if not alteracoes:
                        print("[AVISO] Nenhuma dimensão informada (--b ou --h).")
                        return

                    if not solicitar_aprovacao_modificacao(
                        editor.nome_edificio, pav, "Pilar", pilar_atual["nome"], alteracoes, auto_aprovar=args.sim
                    ):
                        return

                    res_ed = editor.editar_pilar(pav, args.editar_pilar, b_cm=args.b, h_cm=args.h)
                    print(f"✅ {res_ed['mensagem']}")
                    print(f"   Dimensões Anteriores: {res_ed['antes']['b_cm']:.0f}x{res_ed['antes']['h_cm']:.0f} cm")
                    print(f"   Novas Dimensões:     {res_ed['depois']['b_cm']:.0f}x{res_ed['depois']['h_cm']:.0f} cm")
                    return

                if args.vigas:
                    vigas = editor.listar_vigas(pav)
                    print(f"VIGAS DO PAVIMENTO '{pav.upper()}' (Total: {len(vigas)}):")
                    print(f"{'Viga':<8} | {'Seção (cm)':<12} | {'Desnível':<10} | {'Nós':<5} | {'Extensão':<10}")
                    print("-" * 55)
                    for v in vigas:
                        ext = "-"
                        if len(v["coordenadas"]) >= 2:
                            x0, y0 = v["coordenadas"][0]["x_m"], v["coordenadas"][0]["y_m"]
                            x1, y1 = v["coordenadas"][-1]["x_m"], v["coordenadas"][-1]["y_m"]
                            ext = f"{((x1-x0)**2 + (y1-y0)**2)**0.5:.2f} m"
                        print(f"{v['nome']:<8} | {v['b_cm']:.0f}x{v['h_cm']:.0f} cm    | {v['desnivel_cm']:<10.1f} | {v['num_nos']:<5} | {ext:<10}")
                    return

                if args.lajes:
                    lajes = editor.listar_lajes(pav)
                    print(f"LAJES DO PAVIMENTO '{pav.upper()}' (Total: {len(lajes)}):")
                    print(f"{'Laje':<8} | {'Espessura':<12} | {'Desnível':<10} | {'Tipo':<12} | {'Ângulo':<8}")
                    print("-" * 55)
                    for l in lajes:
                        print(f"{l['nome']:<8} | {l['espessura_cm']:.1f} cm     | {l['desnivel_cm']:<10.1f} | {l['tipo_descricao']:<12} | {l['angulo_principal_graus']:.0f}°")
                    return

                if args.pilares:
                    pilares = editor.listar_pilares(pav)
                    print(f"PILARES DO PAVIMENTO '{pav.upper()}' (Total: {len(pilares)}):")
                    print(f"{'Pilar':<8} | {'Seção (cm)':<12} | {'X (m)':<10} | {'Y (m)':<10}")
                    print("-" * 45)
                    for p in pilares:
                        print(f"{p['nome']:<8} | {p['secao_cm']:<12} | {p['x_m']:<10.2f} | {p['y_m']:<10.2f}")
                    return

        except Exception as e:
            print(f"[ERRO] Falha no Modelador Estrutural: {e}")
            import traceback
            traceback.print_exc()
        return

    # Processamento Estrutural do Edifício (Pórtico Espacial ou Global)
    if args.processar:
        if not args.edificio:
            print("[ERRO] Para processar o edifício, informe o código ou nome através de --edificio <cod>.")
            return

        tipo_p = "global" if "global" in str(args.processar).lower() else "portico_cargas"
        print(f"\n=========================================================")
        print(f"   AUTQS - PROCESSAMENTO ESTRUTURAL TQS: EDIFÍCIO {args.edificio}")
        print(f"   Modo de Análise: {tipo_p.upper()}")
        print(f"=========================================================")
        print("Disparando rotinas em lote no TQS V25...")

        res = orchestrator.registry.executar_ferramenta(
            "processar_edificio",
            {
                "edificio_nome": args.edificio,
                "tipo_processamento": tipo_p,
                "gerar_planta_apos_processar": True
            }
        )

        planta_gerada = res.get("planta_gerada")

        if not res.get("sucesso"):
            print(f"\n[FALHA] Processamento estrutural incompleto:")
            if res.get("erro"):
                print(f"  * {res.get('erro')}")
            for tarefa in res.get("tarefas_com_falha", []):
                print(f"  * Tarefa não concluída: {tarefa}")
            for pav in res.get("pavimentos_sem_vigas_dimensionadas", []):
                print(f"  * Vigas não dimensionadas no pavimento: {pav}")
            for msg in res.get("mensagens_tqs", []):
                print(f"  * {msg}")
            if planta_gerada and planta_gerada.get("sucesso"):
                print(f"  * Planta de Cargas emitida (depende apenas do pórtico): {planta_gerada.get('caminho_dwg')}")
            return

        print(f"\n[SUCESSO] Processamento do edifício concluído em {res.get('duracao_segundos', 0):.1f}s!")
        print(f"  * Pórtico Espacial e Reações (PORLIS): {'OK' if res.get('tem_porlis') else 'Não detectado'}")
        print(f"  * Cargas nos pilares (CARDWG):        {'OK' if res.get('tem_cardwg') else 'Não detectado'}")

        if planta_gerada and planta_gerada.get("sucesso"):
            print(f"  * Planta de Cargas (GABARITO.DWG) emitida com sucesso!")
            print(f"    Caminho: {planta_gerada.get('caminho_dwg')}")
            print(f"    Total de Pilares: {planta_gerada.get('total_pilares')}")
        return

    # Emissão de Planta de Cargas (Fluxo Padrão quando --edificio é fornecido sem flags de modelo)
    if args.edificio:
        print(f"\n=========================================================")
        print(f"   AUTQS - EMISSÃO DE PLANTA DE CARGAS: EDIFÍCIO {args.edificio}")
        print(f"=========================================================")
        
        try:
            reader = TQSBuildingReader(args.edificio)
            print(f"Edifício localizado: {reader.nome_edificio}")
            print(f"Pasta do projeto: {reader.caminho_edificio}")
            print("Lendo geometria dos pilares e reações do pórtico espacial...")
            
            planta = reader.carregar_planta_de_cargas()
            print(f"[OK] Total de pilares que nascem na fundação: {len(planta.pilares)}\n")

            # Exibe prévia da tabela no console
            print(f"{'Pilar':<6} | {'Seção (cm)':<12} | {'Xcg (m)':<8} | {'Ycg (m)':<8} | {'Nk (tf)':<10} | {'Mx (tf.m)':<9} | {'My (tf.m)':<9}")
            print("-" * 75)
            for p in planta.pilares[:15]:
                xcg = p.baricentro.x / 100.0 if p.baricentro else 0.0
                ycg = p.baricentro.y / 100.0 if p.baricentro else 0.0
                nk = p.esforcos.nk_max if p.esforcos else 0.0
                mx = p.esforcos.mxk if p.esforcos else 0.0
                my = p.esforcos.myk if p.esforcos else 0.0
                print(f"{p.nome:<6} | {p.geometria.b:.0f}x{p.geometria.h:.0f} cm    | {xcg:<8.2f} | {ycg:<8.2f} | {nk:<10.1f} | {mx:<9.2f} | {my:<9.2f}")
            
            if len(planta.pilares) > 15:
                print(f"... e mais {len(planta.pilares) - 15} pilares adicionais catalogados.")

            if planta.dados_porlid and planta.dados_porlid.get("linhas"):
                por = planta.dados_porlid
                num_c = por.get("num_casos", 1)
                if num_c > 1:
                    print(f"\n[OK] Tabela Oficial PORLID ({num_c} CASOS CRÍTICOS, {len(por['linhas'])} elementos)")
                    for c in por.get("casos", []):
                        print(f"     * {c['nome']}: {c['titulo']}")
                else:
                    print(f"\n[OK] Tabela Oficial PORLID (Caso Único, {len(por['linhas'])} elementos)")
                    print(f"     Combinação: {por.get('titulo')}")

                print(f"\n     Prévia do Caso 1 ({por.get('casos', [{}])[0].get('nome', 'CASO 1')}):")
                print(f"     {'Elem':<7} | {'Fz (tf)':<8} | {'Fx (tf)':<8} | {'Fy (tf)':<8} | {'Mx (tfm)':<9} | {'My (tfm)':<9} | {'Mz (tfm)':<9}")
                print("     " + "-" * 65)
                for row in por["linhas"][:6]:
                    print(f"     {row[0]:<7} | {row[1]:<8} | {row[2]:<8} | {row[3]:<8} | {row[4]:<9} | {row[5]:<9} | {row[6]:<9}")
                if len(por["linhas"]) > 6:
                    print(f"     ... e mais {len(por['linhas']) - 6} elementos oficiais de fundação catalogados.")

            # Geração da Prancha de Desenho
            caminho_saida = args.desenho or "GABARITO.DWG"
            origem_cotas = (args.origem_x, args.origem_y) if (args.origem_x is not None and args.origem_y is not None) else None
            if caminho_saida.lower().endswith(".dwg"):
                from src.drawing.tqs_dwg_builder import TQSDwgPlantaDeCargasBuilder
                builder = TQSDwgPlantaDeCargasBuilder()
                arquivo_gerado = builder.construir_planta_de_cargas(planta, caminho_saida, origem_cotas=origem_cotas)
            else:
                from src.drawing.sheet_builder import PlantaDeCargasDwgBuilder
                builder = PlantaDeCargasDwgBuilder(escala=50)
                arquivo_gerado = builder.construir_planta_completa(planta, caminho_saida)

            pasta_espacial = os.path.join(reader.caminho_edificio, "ESPACIAL")
            os.makedirs(pasta_espacial, exist_ok=True)
            nome_dwg_espacial = "GABARITO.DWG" if caminho_saida.upper().endswith(".DWG") else os.path.basename(arquivo_gerado)
            copia_espacial = os.path.join(pasta_espacial, nome_dwg_espacial)
            caminho_final_tqs = copia_espacial

            # Backup de segurança da versão anterior caso já exista
            if os.path.exists(copia_espacial) and os.path.isfile(copia_espacial):
                try:
                    from datetime import datetime
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    nome_base, ext = os.path.splitext(nome_dwg_espacial)
                    bkp_ts = os.path.join(pasta_espacial, f"{nome_base}_BKP_{ts}{ext}")
                    shutil.copy2(copia_espacial, bkp_ts)
                    print(f"[BACKUP] Backup da versão anterior salvo em: '{os.path.basename(bkp_ts)}'.")
                except Exception:
                    pass

            try:
                shutil.copyfile(arquivo_gerado, copia_espacial)
            except Exception:
                salvo = False
                for nome_alt in ["GABARITO_ATUALIZADO.DWG", "GABARITO_NOVO.DWG"]:
                    caminho_alt = os.path.join(pasta_espacial, nome_alt)
                    try:
                        shutil.copyfile(arquivo_gerado, caminho_alt)
                        caminho_final_tqs = caminho_alt
                        salvo = True
                        print(f"[AVISO] '{os.path.basename(copia_espacial)}' está atualmente aberto no TQS EAGW.")
                        print(f"        Cópia atualizada gravada com sucesso em: '{os.path.basename(caminho_alt)}'.")
                        print(f"        (Para sobrescrever o arquivo original, basta fechá-lo no TQS).")
                        break
                    except Exception:
                        continue
                if not salvo:
                    print(f"[AVISO] Arquivo aberto no TQS EAGW; feche-o para atualizar a cópia da pasta da obra.")

            print(f"\n[OK] PRANCHA NATIVA TQS .DWG GERADA COM SUCESSO:")
            print(f"     1. No diretório local:       {os.path.abspath(arquivo_gerado)}")
            print(f"     2. Na pasta ESPACIAL do TQS: {copia_espacial}")
            print(f"\nAbra o arquivo diretamente no TQS V25 (Menu Arquivo > Abrir Desenho na pasta ESPACIAL) para visualizar.")

        except Exception as e:
            print(f"[ERRO] Falha ao processar edifício: {e}")
            import traceback
            traceback.print_exc()
        return

    print("AUTQS CLI inicializado. Use --edificio 054 para gerar a planta de cargas ou --pavimentos / --vigas / --lajes para o Modelador.")

if __name__ == "__main__":
    main()
