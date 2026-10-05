import unittest
from unittest.mock import patch
from src.ui.cli import solicitar_aprovacao_modificacao
from src.agent.chat_agent import AutqsChatAgent

class TestAprovacaoModificacoes(unittest.TestCase):
    def test_solicitar_aprovacao_flag_auto(self):
        """Testa aprovacao automatica via flag --sim / -y."""
        params = [("Largura (b)", "25 cm", "30 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Pilar", "P8", params, auto_aprovar=True
        )
        self.assertTrue(aprovado)

    @patch("builtins.input", return_value="s")
    def test_solicitar_aprovacao_usuario_sim(self, mock_input):
        """Testa resposta 's' do usuario aprovando a alteracao."""
        params = [("Largura (b)", "25 cm", "30 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Pilar", "P8", params, auto_aprovar=False
        )
        self.assertTrue(aprovado)

    @patch("builtins.input", return_value="sim")
    def test_solicitar_aprovacao_usuario_sim_extenso(self, mock_input):
        """Testa resposta 'sim' do usuario aprovando a alteracao."""
        params = [("Altura (h)", "60 cm", "70 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Viga", "V1", params, auto_aprovar=False
        )
        self.assertTrue(aprovado)

    @patch("builtins.input", return_value="n")
    def test_solicitar_aprovacao_usuario_nao(self, mock_input):
        """Testa resposta 'n' do usuario rejeitando a alteracao."""
        params = [("Largura (b)", "25 cm", "30 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Pilar", "P8", params, auto_aprovar=False
        )
        self.assertFalse(aprovado)

    @patch("builtins.input", return_value="")
    def test_solicitar_aprovacao_usuario_enter_padrao_nao(self, mock_input):
        """Testa tecla Enter vazia assumindo cancelamento padrao."""
        params = [("Largura (b)", "25 cm", "30 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Pilar", "P8", params, auto_aprovar=False
        )
        self.assertFalse(aprovado)

    @patch("builtins.input", side_effect=EOFError)
    def test_solicitar_aprovacao_eof(self, mock_input):
        """Testa comportamento seguro ao receber EOF / fluxo nao interativo."""
        params = [("Largura (b)", "25 cm", "30 cm")]
        aprovado = solicitar_aprovacao_modificacao(
            "054", "terreo", "Pilar", "P8", params, auto_aprovar=False
        )
        self.assertFalse(aprovado)

    def test_chat_agent_fluxo_aprovacao(self):
        """Testa o fluxo de seguranca com solicitacao de aprovacao no chat interativo."""
        agent = AutqsChatAgent()
        
        # 1. Usuário pede alteração -> Agente deve solicitar confirmação sem gravar
        r1 = agent.responder("mude o pilar P8 para 30x80 no terreo")
        self.assertEqual(r1.get("tipo"), "solicitacao_aprovacao")
        self.assertIn("Solicitação de Aprovação", r1.get("texto", "") or "")
        self.assertIsNotNone(agent.modificacao_pendente)

        # 2. Usuário cancela com 'não' -> Agente deve abortar sem gravar
        r2 = agent.responder("não")
        self.assertEqual(r2.get("tipo"), "texto")
        self.assertIn("Modificação cancelada", r2.get("texto", "") or "")
        self.assertIsNone(agent.modificacao_pendente)

if __name__ == "__main__":
    unittest.main()
