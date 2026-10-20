import unittest
from src.skills.case_07_comparacao_formas.geometry_comparator import (
    TQSGeometryComparator,
    DiferencaElemento,
    RelatorioComparacaoResultado,
)
from src.skills.case_07_comparacao_formas.skill import ComparacaoFormasSkill
from src.agent.tools import ToolsRegistry


class TestComparacaoFormas(unittest.TestCase):
    def test_relatorio_estruturado_e_metricas(self):
        item1 = DiferencaElemento(
            tipo="PILAR",
            nome="P1",
            status="ALTERADO_SECAO",
            valor_anterior="20x50 cm",
            valor_atual="25x60 cm",
            delta="Δb=+5.0cm, Δh=+10.0cm",
            impacto_estrutural="Atenção: Aumento de inércia e capacidade resistente."
        )
        item2 = DiferencaElemento(
            tipo="VIGA",
            nome="V3",
            status="NOVO",
            valor_anterior="---",
            valor_atual="15x50 cm",
            delta="Inclusão de viga",
            impacto_estrutural="Importante: Novo suporte para lajes."
        )
        item3 = DiferencaElemento(
            tipo="LAJE",
            nome="L2",
            status="INALTERADO",
            valor_anterior="h=10 cm",
            valor_atual="h=10 cm",
            delta="0.0 cm",
            impacto_estrutural="Sem impacto."
        )

        rel = RelatorioComparacaoResultado(
            origem_base="054_R00",
            origem_comparada="054_R01",
            pavimento_base="TERREO",
            pavimento_comparado="TERREO",
            itens=[item1, item2, item3]
        )

        self.assertEqual(rel.total_novos, 1)
        self.assertEqual(rel.total_removidos, 0)
        self.assertEqual(rel.total_alterados, 1)
        self.assertEqual(rel.total_inalterados, 1)
        self.assertTrue(rel.tem_mudancas)

        # Resumo executivo em markdown
        resumo = rel.para_resumo_executivo()
        self.assertIn("Pilares Alterados", resumo)
        self.assertIn("Vigas Alteradas", resumo)
        self.assertIn("P1", resumo)
        self.assertIn("V3", resumo)

        # Tabela terminal
        tab = rel.para_tabela_terminal()
        self.assertIn("AUDITORIA DE DIFERENÇAS", tab)
        self.assertIn("P1", tab)

        # Dicionário serializável
        d = rel.para_dict()
        self.assertEqual(d["metricas"]["novos"], 1)
        self.assertEqual(d["metricas"]["alterados"], 1)

    def test_skill_tools_registry(self):
        registry = ToolsRegistry()
        self.assertIn("comparar_geometrias_formas", registry._skills)
        tools = registry.listar_ferramentas_para_llm()
        tool_names = [t["function"]["name"] for t in tools if t.get("type") == "function"]
        self.assertIn("comparar_geometrias_formas", tool_names)

    def test_execucao_skill_comparacao_identica(self):
        skill = ComparacaoFormasSkill()
        res = skill.executar(
            edificio_base="049",
            pavimento_base="terreo",
            edificio_comparado="049",
            pavimento_comparado="terreo",
            gerar_desenho_diff=False
        )
        self.assertEqual(res["status"], "sucesso")
        self.assertTrue(res["sucesso"])
        self.assertFalse(res["tem_mudancas"])
        self.assertIn("Nenhuma divergência geométrica", res["resumo_executivo"])


if __name__ == "__main__":
    unittest.main()
