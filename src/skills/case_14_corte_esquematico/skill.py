from dataclasses import asdict
from typing import Any, Dict, Optional

from src.skills.base_skill import BaseSkill
from src.skills.case_14_corte_esquematico.corte_builder import CorteEsquematicoBuilder


class CorteEsquematicoSkill(BaseSkill):
    """
    Case 14: Gera o Corte Esquemático com Resistências dos Materiais (GERAIS\\CORTE ESQUEMÁTICO.DWG)
    dinamicamente para qualquer edifício TQS, extraindo pavimentos, repetições, cotas,
    pés-direitos, fck do concreto e resistências da alvenaria (bloco, argamassa, graute, prisma).
    """

    @property
    def nome(self) -> str:
        return "gerar_corte_esquematico"

    @property
    def descricao(self) -> str:
        return (
            "Gera dinamicamente o arquivo DWG nativo TQS de Corte Esquemático com Resistências "
            "dos Materiais (GERAIS\\CORTE ESQUEMÁTICO.DWG) para cada edifício, variando conforme "
            "pavimentos, repetições, cotas, pé-direito, sistema estrutural (AE/CA), fck, fbk, "
            "argamassa, graute e prisma oco."
        )

    def validar(self, edificio_nome: Optional[str] = None, **kwargs) -> bool:
        return bool(edificio_nome and str(edificio_nome).strip())

    def executar(
        self,
        edificio_nome: str,
        cota_base_m: Optional[float] = None,
        arm_graute_mm: float = 12.5,
        caminho_saida_dwg: Optional[str] = None,
        overrides_pavimentos: Optional[Dict[str, Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Extrai os dados do edifício e gera GERAIS\\CORTE ESQUEMÁTICO.DWG.

        :param edificio_nome: Nome, código ou caminho completo do edifício no TQS.
        :param cota_base_m: Cota de partida em metros (None = lê automaticamente de project.floorHeight).
        :param arm_graute_mm: Diâmetro da armadura vertical do graute em mm (padrão 12.5).
        :param caminho_saida_dwg: Caminho opcional de saída; padrão <edificio>/GERAIS/CORTE ESQUEMÁTICO.DWG.
        :param overrides_pavimentos: Dicionário opcional por nome de pavimento para sobrescrever materiais/cotas.
        """
        builder = CorteEsquematicoBuilder()
        dados = builder.extrair_dados_edificio(
            edificio_nome_ou_caminho=edificio_nome,
            cota_base_m=cota_base_m,
            arm_graute_mm=arm_graute_mm,
            overrides_pavimentos=overrides_pavimentos,
        )
        caminho_dwg = builder.gerar_dwg(dados=dados, caminho_saida_dwg=caminho_saida_dwg)

        return {
            "status": "sucesso",
            "sucesso": True,
            "edificio": dados.nome_edificio,
            "caminho_dwg": caminho_dwg,
            "tipo_bloco": dados.tipo_bloco,
            "fck_lajes_vigas": dados.fck_lajes_vigas,
            "fck_pilares": dados.fck_pilares,
            "total_pavimentos": len(dados.pavimentos),
            "pavimentos": [asdict(p) for p in dados.pavimentos],
        }
