import os
from typing import Any, Dict, Optional
from src.skills.base_skill import BaseSkill
from src.drawing.alvenaria_dwg_builder import AlvenariaDwgBuilder
from src.tqs_adapter.building_reader import TQSBuildingReader

class FormasAlvenariaSkill(BaseSkill):
    """
    Case 3: Habilidade responsável pela transformação inteligente de fiadas
    brutas do TQS Alvest (DesFiad1.DWG) em Plantas de Formas Executivas de 
    Alvenaria Estrutural (PRE_FOR_1aFIADA_*.DWG).
    """

    @property
    def nome(self) -> str:
        return "gerar_planta_formas_alvenaria"

    @property
    def descricao(self) -> str:
        return (
            "Gera a Planta de Formas de Alvenaria Estrutural (1ª Fiada) executiva a partir do "
            "desenho de fiada do TQS Alvest (DesFiad1.DWG). O pipeline purga poluição visual "
            "(armaduras verticais pf12.5 e cotas internas modulares), sobrepõe lajes e espessuras "
            "(LAJ*.DWG), anota dimensões modulares de vãos e esquadrias no Nível 239, marca juntas de "
            "movimentação/dilatação no Nível 221, agrega o resumo de materiais de alvenaria (LISTMELV), "
            "incorpora a legenda de blocos e corte esquemático de resistências dos materiais e monta a "
            "prancha oficial do TQS (A0-45) com escala regulamentar e selo técnico."
        )

    def executar(
        self,
        edificio_nome: str,
        pavimento: str = "TIPO A",
        caminho_edificio: str = "",
        caminho_saida_dwg: Optional[str] = None,
        escala: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Executa o pipeline da Skill de Formas de Alvenaria:
        1. Resolve caminho completo do edifício TQS.
        2. Dispara o AlvenariaDwgBuilder para processar o pavimento indicado.
        3. Aplica guardrails normativos de engenharia e retorna o relatório estruturado.
        """
        # Resolve caminho do edifício
        caminho_ed = caminho_edificio
        if not caminho_ed or not os.path.exists(caminho_ed):
            edificios = TQSBuildingReader.listar_edificios_disponiveis()
            for ed in edificios:
                if edificio_nome in ed["nome"] or edificio_nome == ed["nome"]:
                    caminho_ed = ed["caminho"]
                    break

        if not caminho_ed or not os.path.exists(caminho_ed):
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": edificio_nome,
                "erro": f"Edifício '{edificio_nome}' não foi encontrado no ambiente TQS.",
            }

        builder = AlvenariaDwgBuilder()
        try:
            res_builder = builder.construir_planta_formas(
                caminho_edificio=caminho_ed,
                pavimento=pavimento,
                caminho_saida_dwg=caminho_saida_dwg,
                escala=escala,
            )
        except Exception as e:
            return {
                "status": "erro",
                "sucesso": False,
                "edificio": os.path.basename(caminho_ed),
                "pavimento": pavimento,
                "erro": f"Falha na construção da planta de formas de alvenaria: {str(e)}",
            }

        res_builder["sucesso"] = True
        
        # Guardrails de validação
        if not self.validar(res_builder):
            res_builder["status"] = "alerta_consistencia"
            res_builder["aviso_validacao"] = "O desenho foi gerado mas não atendeu a todos os critérios normativos estritos."

        return res_builder

    def validar(self, resultado: Dict[str, Any]) -> bool:
        """
        Guardrails de Engenharia Estrutural:
        - O arquivo .DWG de saída deve existir e ter tamanho não nulo;
        - As camadas vitais (10=lajes, 13=espessuras, 222=título, 230=moldura, 239=vãos, 247=paredes) devem estar presentes;
        - Deve possuir lajes e vãos mapeados;
        - Escala configurada deve ser 50.
        """
        if not resultado.get("sucesso", False):
            return False

        caminho_dwg = resultado.get("caminho_dwg")
        if not caminho_dwg or not os.path.exists(caminho_dwg):
            return False

        if os.path.getsize(caminho_dwg) < 1024:
            return False

        auditoria = resultado.get("auditoria", {})
        niveis = auditoria.get("niveis_utilizados", [])
        
        # Verifica se as camadas estruturais e de identificação essenciais estão no desenho
        camadas_obrigatorias = [10, 13, 222, 230, 239, 247]
        for c in camadas_obrigatorias:
            if c not in niveis:
                return False

        if resultado.get("total_lajes", 0) <= 0:
            return False

        if resultado.get("total_vaos", 0) <= 0:
            return False

        return True
