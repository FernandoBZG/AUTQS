import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.skills.case_11_memorial_calculo.memorial_generator import TQSMemorialGenerator


class MemorialCalculoSkill(BaseSkill):
    """
    Case 11: Geração automática e consolidada do Memorial Descritivo e
    Justificativo de Cálculo Estrutural do edifício no CAD/TQS V25
    conforme as normas NBR 6118:2023, NBR 6120:2019 e NBR 6123:2023.

    Integra de forma executiva:
      - Identificação do projeto e premissas normativas.
      - Propriedades de materiais e classes de agressividade ambiental.
      - Parâmetros de estabilidade global (γz, FAVt, α) e limites de ELS (H/1700, Hi/850).
      - Resumo dos modelos de lajes e sistemas estruturais.
      - Quantitativos consolidados de concreto, formas, aço e pegada de carbono.
      - Exportação em formato Markdown (.md) e HTML pronto para impressão/PDF.
    """

    @property
    def nome(self) -> str:
        return "gerar_memorial_descritivo"

    @property
    def descricao(self) -> str:
        return (
            "Gera o Memorial Descritivo e Justificativo de Cálculo Estrutural do edifício no TQS V25 "
            "conforme a NBR 6118. Consolida estabilidade global (GamaZ, deslocamentos de vento), "
            "especificação de materiais, resumo de lajes, quantitativos de concreto/aço/formas "
            "e pegada de carbono em relatórios executivos em Markdown e HTML."
        )

    def executar(
        self,
        edificio_nome: str,
        caminho_saida_md: Optional[str] = None,
        caminho_saida_html: Optional[str] = None,
        pasta_raiz_tqs: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa a geração do Memorial Descritivo do edifício.
        :param edificio_nome: Nome ou código do edifício (ex: '054').
        :param caminho_saida_md: Opcional arquivo de destino .md.
        :param caminho_saida_html: Opcional arquivo de destino .html.
        :param pasta_raiz_tqs: Opcional raiz do TQS (padrão C:\\TQS).
        """
        try:
            gerador = TQSMemorialGenerator(edificio_nome, pasta_raiz_tqs=pasta_raiz_tqs)
            ret = gerador.gerar(
                caminho_saida_md=caminho_saida_md,
                caminho_saida_html=caminho_saida_html
            )

            return {
                "status": "sucesso",
                "sucesso": True,
                "edificio": ret["edificio_nome"],
                "resumo_executivo": ret["conteudo_markdown"],
                "arquivo_md": ret.get("arquivo_md"),
                "arquivo_html": ret.get("arquivo_html"),
            }

        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "mensagem": f"Falha ao gerar memorial do edifício '{edificio_nome}': {str(e)}"
            }

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """Valida se o memorial foi produzido com sucesso e contém conteúdo textual."""
        if not isinstance(resultado, dict):
            return False
        if resultado.get("status") != "sucesso":
            return False
        return "resumo_executivo" in resultado and len(resultado["resumo_executivo"]) > 100
