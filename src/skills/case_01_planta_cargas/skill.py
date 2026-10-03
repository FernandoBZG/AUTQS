import os
from typing import Any, Dict, List, Optional
from src.skills.base_skill import BaseSkill
from src.core.models import PlantaDeCargasModel, PilarFundacao
from src.skills.case_01_planta_cargas.geometry import calcular_baricentro_pilar
from src.drawing.sheet_builder import PlantaDeCargasDwgBuilder
from src.drawing.tqs_dwg_builder import TQSDwgPlantaDeCargasBuilder
from src.tqs_adapter.grid_adapter import GridTabelaCargasAdapter

class PlantaDeCargasSkill(BaseSkill):
    """
    Case 1: Habilidade responsável pela extração dos pilares que nascem na fundação,
    cálculo do baricentro analítico e montagem da prancha gráfica e tabela de cargas.
    """

    @property
    def nome(self) -> str:
        return "gerar_planta_de_cargas"

    @property
    def descricao(self) -> str:
        return (
            "Gera a Planta de Cargas e Locação de fundações do edifício TQS. "
            "Identifica todos os pilares que nascem na fundação, calcula as "
            "coordenadas absolutas de seus baricentros (CG), extrai as envoltórias "
            "de esforços característicos (Nk_max, Nk_min, Mx, My, Hx, Hy) e "
            "gera a prancha de desenho (DWG nativo do TQS ou DXF) com a locação dos pilares, baricentros e tabela."
        )

    def executar(
        self,
        edificio_nome: str,
        caminho_edificio: str = "",
        pavimento_fundacao: str = "FUNDACAO",
        pilares_input: Optional[List[PilarFundacao]] = None,
        gerar_desenho: bool = True,
        caminho_saida_desenho: Optional[str] = "GABARITO.DWG",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o pipeline completo do Case 1:
        1. Cálculo dos baricentros analíticos (CG).
        2. Montagem do modelo agregado da Planta de Cargas.
        3. Geração da prancha vetorial contendo o desenho dos pilares, CG e tabela de cargas.
        """
        pilares = pilares_input or []
        if not pilares:
            from src.tqs_adapter.building_reader import TQSBuildingReader
            leitor = TQSBuildingReader(caminho_edificio or edificio_nome)
            planta_lida = leitor.carregar_planta_de_cargas()
            pilares = planta_lida.pilares
            edificio_nome = planta_lida.edificio_nome
            caminho_edificio = planta_lida.caminho_edificio

        # 1. Passo: Cálculo do Baricentro para cada pilar (se ainda não calculado)
        pilares_processados: List[PilarFundacao] = []
        for p in pilares:
            if not p.baricentro or (p.baricentro.x == 0.0 and p.baricentro.y == 0.0):
                p.baricentro = calcular_baricentro_pilar(p.geometria)
            pilares_processados.append(p)

        # 2. Passo: Montagem do Modelo Unificado da Planta de Cargas
        dados_porlid = getattr(planta_lida, "dados_porlid", None) if not pilares_input else None
        planta = PlantaDeCargasModel(
            edificio_nome=edificio_nome,
            caminho_edificio=caminho_edificio,
            pavimento_fundacao=pavimento_fundacao,
            pilares=pilares_processados,
            dados_porlid=dados_porlid,
        )


        # 3. Passo: Geração da Prancha de Desenho com Pilares + Tabela
        arquivo_desenho_gerado = None
        caminho_espacial_gerado = None
        if gerar_desenho and len(pilares_processados) > 0:
            caminho_alvo = caminho_saida_desenho or "GABARITO.DWG"
            escala_req = kwargs.get("escala")
            if caminho_alvo.lower().endswith(".dwg"):
                builder_dwg = TQSDwgPlantaDeCargasBuilder()
                arquivo_desenho_gerado = builder_dwg.construir_planta_de_cargas(planta, caminho_alvo, escala=escala_req)
            else:
                builder_dxf = PlantaDeCargasDwgBuilder(escala=escala_req or 50)
                arquivo_desenho_gerado = builder_dxf.construir_planta_completa(planta, caminho_alvo)

            # A planta de cargas SEMPRE deve ficar na pasta ESPACIAL do edifício no TQS como GABARITO.DWG
            caminho_backup_gerado = None
            if caminho_edificio and os.path.exists(caminho_edificio) and arquivo_desenho_gerado:
                import shutil
                from datetime import datetime
                pasta_espacial = os.path.join(caminho_edificio, "ESPACIAL")
                os.makedirs(pasta_espacial, exist_ok=True)
                nome_arq = "GABARITO.DWG" if caminho_alvo.upper().endswith(".DWG") else os.path.basename(arquivo_desenho_gerado)
                caminho_espacial_gerado = os.path.join(pasta_espacial, nome_arq)

                # Backup automático de segurança da versão anterior caso já exista
                if os.path.exists(caminho_espacial_gerado) and os.path.isfile(caminho_espacial_gerado):
                    nome_base, ext = os.path.splitext(nome_arq)
                    try:
                        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                        bkp_ts = os.path.join(pasta_espacial, f"{nome_base}_BKP_{ts}{ext}")
                        shutil.copy2(caminho_espacial_gerado, bkp_ts)
                        caminho_backup_gerado = bkp_ts
                    except Exception:
                        pass
                    try:
                        bkp_direto = os.path.join(pasta_espacial, f"{nome_base}_BKP{ext}")
                        shutil.copy2(caminho_espacial_gerado, bkp_direto)
                    except Exception:
                        pass

                try:
                    shutil.copyfile(arquivo_desenho_gerado, caminho_espacial_gerado)
                except Exception:
                    for nome_alt in ["GABARITO_ATUALIZADO.DWG", "GABARITO_NOVO.DWG"]:
                        caminho_alt = os.path.join(pasta_espacial, nome_alt)
                        try:
                            shutil.copyfile(arquivo_desenho_gerado, caminho_alt)
                            caminho_espacial_gerado = caminho_alt
                            break
                        except Exception:
                            continue

        # 4. Resumo estruturado para o Agente Cognitivo
        resumo_pilares = [
            {
                "pilar": p.nome,
                "secao_cm": f"{p.geometria.b:.1f}x{p.geometria.h:.1f}",
                "xcg_m": round(p.baricentro.x / 100.0, 3) if p.baricentro else None,
                "ycg_m": round(p.baricentro.y / 100.0, 3) if p.baricentro else None,
                "nk_max_tf": p.esforcos.nk_max if p.esforcos else 0.0,
                "nk_min_tf": p.esforcos.nk_min if p.esforcos else 0.0,
                "mxk_tfm": p.esforcos.mxk if p.esforcos else 0.0,
                "myk_tfm": p.esforcos.myk if p.esforcos else 0.0,
                "hx_tf": p.esforcos.hx if p.esforcos else 0.0,
                "hy_tf": p.esforcos.hy if p.esforcos else 0.0,
            }
            for p in pilares_processados
        ]

        resultado = {
            "status": "sucesso",
            "edificio": edificio_nome,
            "caminho_edificio": caminho_edificio,
            "caminho_espacial": caminho_espacial_gerado,
            "caminho_backup": caminho_backup_gerado,
            "pavimento": pavimento_fundacao,
            "total_pilares_fundacao": len(pilares_processados),
            "pilares": resumo_pilares,
            "dados_porlid": dados_porlid,
            "arquivo_desenho_gerado": arquivo_desenho_gerado,
        }


        # Executa guardrails de validação
        if not self.validar(resultado):
            resultado["status"] = "alerta_consistencia"

        return resultado

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia:
        - Verifica se há pilares com tração excessiva na fundação.
        """
        pilares = resultado.get("pilares", [])
        for p in pilares:
            if p.get("nk_min_tf", 0.0) < -5.0:
                print(f"[ALERTA ESTRUTURAL] Pilar {p['pilar']} com tração na fundação: {p['nk_min_tf']} tf")
        return True
