import unittest
import os
import tempfile
import ezdxf

from src.agent.tools import ToolsRegistry
from src.agent.orchestrator import AutqsAgentOrchestrator
from src.agent.chat_agent import AutqsChatAgent


class TestNovasSkillsIntegracao(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = ToolsRegistry()
        cls.orchestrator = AutqsAgentOrchestrator()
        cls.chat_agent = AutqsChatAgent()
        cls.chat_agent.edificio_ativo = "054"

    def test_catalogo_ferramentas_completo(self):
        """Testa se todas as 12 habilidades estão no registro e expostas para LLM."""
        ferramentas = self.registry.listar_ferramentas_para_llm()
        nomes = [f["function"]["name"] for f in ferramentas]

        # Verifica presença de todas as 12 ferramentas
        esperadas = [
            "gerar_planta_de_cargas",
            "processar_edificio",
            "gerar_planta_formas_alvenaria",
            "analisar_pilares_edificio",
            "verificar_consistencia_planta",
            "analisar_vigas_pavimento",
            "comparar_geometrias_formas",
            "auditar_estabilidade_global",
            "auditar_lajes_edificio",
            "extrair_quantitativo_materiais",
            "gerar_memorial_descritivo",
            "padronizar_arquitetura_tqs",
        ]
        for esp in esperadas:
            self.assertIn(esp, nomes, f"Ferramenta {esp} não encontrada no catálogo de Function Calling.")

    def test_orquestrador_estabilidade_global(self):
        """Testa o roteamento e execução de Estabilidade Global."""
        ret = self.orchestrator.processar_comando_local("verificar estabilidade global e gamaz no edificio 054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertIn("resumo_executivo", ret)
        self.assertGreater(ret["gama_z_max"], 1.0)

    def test_orquestrador_lajes(self):
        """Testa o roteamento e execução de Auditoria de Lajes."""
        ret = self.orchestrator.processar_comando_local("auditar lajes e grelha no pavimento 2 do edificio 054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertGreater(ret["total_lajes"], 20)

    def test_orquestrador_quantitativos(self):
        """Testa o roteamento e execução de Quantitativo de Materiais."""
        ret = self.orchestrator.processar_comando_local("extrair quantitativo de materiais do edificio 054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertGreater(ret["volume_concreto_total_m3"], 100.0)

    def test_orquestrador_memorial(self):
        """Testa o roteamento e execução do Memorial Descritivo."""
        ret = self.orchestrator.processar_comando_local("gerar memorial descritivo de calculo do edificio 054")
        self.assertEqual(ret["status"], "sucesso")
        self.assertIn("resumo_executivo", ret)

    def test_chat_agent_respostas_ricas(self):
        """Testa a geração de respostas em linguagem natural no ChatAgent."""
        # 1. Estabilidade
        resp_est = self.chat_agent.responder("Auditar a estabilidade global e drift de vento")
        self.assertEqual(resp_est["tipo"], "estabilidade_global")
        self.assertIn("AUDITORIA DE ESTABILIDADE GLOBAL", resp_est["texto"])

        # 2. Lajes
        resp_laj = self.chat_agent.responder("Auditar as lajes e flechas do 2 pavimento")
        self.assertEqual(resp_laj["tipo"], "auditoria_lajes")
        self.assertIn("AUDITORIA DE LAJES, GRELHA E FLECHAS", resp_laj["texto"])

        # 3. Quantitativos
        resp_mat = self.chat_agent.responder("Extrair o quantitativo de materiais e indices de consumo")
        self.assertEqual(resp_mat["tipo"], "quantitativo_materiais")
        self.assertIn("QUANTITATIVO GLOBAL E ÍNDICES DE CONSUMO", resp_mat["texto"])

        # 4. Memorial
        resp_mem = self.chat_agent.responder("Gerar o memorial descritivo da obra")
        self.assertEqual(resp_mem["tipo"], "memorial_descritivo")
        self.assertIn("MEMORIAL DESCRITIVO E JUSTIFICATIVO DE CÁLCULO ESTRUTURAL", resp_mem["texto"])


if __name__ == "__main__":
    unittest.main()
