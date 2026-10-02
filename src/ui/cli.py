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
from src.drawing.sheet_builder import PlantaDeCargasDwgBuilder
from src.core.models import PilarFundacao, GeometriaPilar, TipoSecao, EsforcosFundacao

def main():
    parser = argparse.ArgumentParser(description="AUTQS CLI - Plataforma de IA para TQS V25")
    parser.add_argument("--edificio", type=str, default=None, help="Nome ou código do edifício TQS (ex: '054' ou nome completo)")
    parser.add_argument("--desenho", type=str, default=None, help="Caminho do arquivo de desenho de saída (DWG/DXF)")
    parser.add_argument("--listar", "-l", action="store_true", help="Lista todos os edifícios encontrados no sistema TQS")
    parser.add_argument("--chat", "-c", action="store_true", help="Inicia o chat interativo no terminal com o Agente AUTQS")
    parser.add_argument("--demo", action="store_true", help="Executa com dados de teste em vez de um edifício real")
    parser.add_argument("--tools", action="store_true", help="Lista as ferramentas disponíveis para o Agente de IA")
    args = parser.parse_args()

    orchestrator = AutqsAgentOrchestrator()

    if args.chat:
        from src.agent.chat_agent import AutqsChatAgent
        print("\n" + "=" * 65)
        print("   AUTQS AGENT - CHAT INTERATIVO DE ENGENHARIA ESTRUTURAL")
        print("=" * 65)
        print("Converse em linguagem natural com o TQS V25.")
        print("Digite 'sair' para encerrar a sessão.\n")

        agent = AutqsChatAgent()
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

    if args.tools:
        print("\n=== FERRAMENTAS DISPONÍVEIS NO AUTQS (FUNCTION CALLING) ===")
        print(json.dumps(orchestrator.listar_ferramentas(), indent=2, ensure_ascii=False))
        return

    # Processamento de Edifício Real do TQS
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
                origem = "PORLID.TXT / PORLID.DWG"
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
            caminho_saida = args.desenho or f"PLANTA_DE_CARGAS_{args.edificio}.dwg"
            if caminho_saida.lower().endswith(".dwg"):
                from src.drawing.tqs_dwg_builder import TQSDwgPlantaDeCargasBuilder
                builder = TQSDwgPlantaDeCargasBuilder()
                arquivo_gerado = builder.construir_planta_de_cargas(planta, caminho_saida)
            else:
                from src.drawing.sheet_builder import PlantaDeCargasDwgBuilder
                builder = PlantaDeCargasDwgBuilder(escala=50)
                arquivo_gerado = builder.construir_planta_completa(planta, caminho_saida)

            # Também salva uma cópia diretamente na pasta do edifício para conveniência
            copia_edificio = os.path.join(reader.caminho_edificio, os.path.basename(arquivo_gerado))
            caminho_final_tqs = copia_edificio
            try:
                shutil.copyfile(arquivo_gerado, copia_edificio)
            except Exception:
                # Se o arquivo estiver aberto e travado no TQS EAGW pelo usuário
                caminho_alt = os.path.join(reader.caminho_edificio, "PLANTA_DE_CARGAS.dwg")
                try:
                    shutil.copyfile(arquivo_gerado, caminho_alt)
                    caminho_final_tqs = caminho_alt
                    print(f"[AVISO] '{os.path.basename(copia_edificio)}' está atualmente aberto no TQS EAGW.")
                    print(f"        Cópia atualizada gravada com sucesso em: '{os.path.basename(caminho_alt)}'.")
                    print(f"        (Para sobrescrever o arquivo original, basta fechá-lo no TQS).")
                except Exception:
                    print(f"[AVISO] Arquivo aberto no TQS EAGW; feche-o para atualizar a cópia da pasta da obra.")


            print(f"\n[OK] PRANCHA NATIVA TQS .DWG GERADA COM SUCESSO:")
            print(f"     1. No diretório local: {os.path.abspath(arquivo_gerado)}")
            print(f"     2. Na pasta do TQS:    {copia_edificio}")
            print(f"\nAbra o arquivo diretamente no TQS V25 (Menu Arquivo > Abrir Desenho) para visualizar.")

        except Exception as e:
            print(f"[ERRO] Falha ao processar edifício: {e}")
            import traceback
            traceback.print_exc()
        return

    if args.demo:
        print("Use --edificio 054 para rodar no projeto real do TQS.")
        return

    print("AUTQS CLI inicializado. Use --edificio 054 para gerar a planta de cargas real ou --tools para listar as ferramentas.")

if __name__ == "__main__":
    main()
