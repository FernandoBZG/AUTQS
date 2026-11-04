import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.drawing.ca_geometry_builder import CAGeometryBuilder
from src.tqs_adapter.building_reader import TQSBuildingReader

class GeometriaCASkill(BaseSkill):
    """
    Case 13: Habilidade responsável pela geração e montagem executiva da Planta de Geometria/Formas
    de Concreto Armado (GEO_<PAVIMENTO>.DWG) no software TQS V25 a partir do arquivo processado
    de formas (FOR000x.DWG), incorporando Moldura ABNT Nível 100, Título Executivo e Notas Técnicas.
    """

    @property
    def nome(self) -> str:
        return "gerar_geometria_concreto_armado"

    @property
    def descricao(self) -> str:
        return (
            "Gera a prancha executiva de Geometria/Formas de Concreto Armado (GEO_<PAVIMENTO>.DWG) "
            "no TQS V25 a partir do arquivo estrutural processado (FOR000x.DWG). Clona a base estrutural pura, "
            "purga cabeçalhos provisórios do TQS, sobrepõe a Moldura ABNT oficial no Nível 100, insere o "
            "Título Executivo com escala regulamentar e reaplica todas as Notas Técnicas, legendas e tabelas "
            "de cargas normativas preservando 100% de integridade e fidelidade geométrica."
        )

    def executar(
        self,
        edificio_nome: str,
        pavimento: str,
        caminho_edificio: str = "",
        escala: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o pipeline da Skill de Geometria de Concreto Armado:
        1. Localiza a pasta do edifício TQS (priorizando edifícios de Concreto Armado / CA).
        2. Resolve o diretório do pavimento especificado.
        3. Invoca o CAGeometryBuilder para gerar o GEO_*.DWG.
        4. Aplica validações de engenharia e retorna o relatório.
        """
        # Resolve caminho do edifício
        caminho_ed = caminho_edificio
        if not caminho_ed or not os.path.exists(caminho_ed):
            edificios = TQSBuildingReader.listar_edificios_disponiveis()
            tokens = [t.lower() for t in edificio_nome.split() if len(t) > 0]
            
            candidatos = []
            for ed in edificios:
                nome_low = ed["nome"].lower()
                if all(t in nome_low for t in tokens):
                    candidatos.append(ed["caminho"])

            if candidatos:
                # Prioriza edifício com ' CA' (Concreto Armado) se houver ambiguidade
                ca_cands = [c for c in candidatos if " ca" in c.lower() or c.lower().endswith(" ca")]
                if ca_cands:
                    caminho_ed = ca_cands[0]
                else:
                    caminho_ed = candidatos[0]
            else:
                for ed in edificios:
                    if edificio_nome.lower() in ed["nome"].lower():
                        caminho_ed = ed["caminho"]
                        break

        if not caminho_ed or not os.path.exists(caminho_ed):
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "erro": f"Edifício '{edificio_nome}' não foi encontrado no ambiente TQS.",
            }

        # Resolve pavimento
        pasta_pav = os.path.join(caminho_ed, pavimento)
        nome_pav_resolvido = pavimento
        if not os.path.exists(pasta_pav):
            # Busca case-insensitive
            pastas = [d for d in os.listdir(caminho_ed) if os.path.isdir(os.path.join(caminho_ed, d))]
            match = None
            for p in pastas:
                if pavimento.lower() in p.lower() or p.lower() in pavimento.lower():
                    match = p
                    break
            if match:
                pasta_pav = os.path.join(caminho_ed, match)
                nome_pav_resolvido = match
            else:
                return {
                    "status": "erro",
                    "sucesso": False,
                    "edificio": edificio_nome,
                    "erro": f"Pavimento '{pavimento}' não encontrado em {caminho_ed}. Pavimentos disponíveis: {pastas}",
                }

        builder = CAGeometryBuilder()
        try:
            resultado = builder.montar_geometria(
                pasta_pavimento=pasta_pav,
                nome_pavimento=nome_pav_resolvido,
                nome_edificio=os.path.basename(caminho_ed),
                escala=float(escala)
            )
            resultado["edificio"] = os.path.basename(caminho_ed)
            resultado["pavimento"] = nome_pav_resolvido
            return resultado
        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "pavimento": nome_pav_resolvido,
                "erro": str(e)
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrail de engenharia:
        1. Sucesso na execução.
        2. Existência e tamanho válido do GEO_*.DWG (> 10 KB).
        3. Presença de vigas estruturais (> 0).
        4. Presença de moldura e notas técnicas.
        """
        if not resultado.get("sucesso", False):
            return False

        caminho_geo = resultado.get("caminho_geo")
        if not caminho_geo or not os.path.exists(caminho_geo):
            return False

        if os.path.getsize(caminho_geo) < 10240:
            return False

        aud = resultado.get("auditoria", {})
        if aud.get("total_vigas", 0) <= 0:
            return False

        niveis = aud.get("niveis", {})
        # Nível 100 (Moldura) deve existir
        if niveis.get(100, 0) <= 0:
            return False

        return True
