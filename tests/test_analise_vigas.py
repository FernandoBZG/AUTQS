import os
import unittest
from src.skills.case_06_analise_vigas.skill import AnaliseVigasSkill
from src.skills.case_06_analise_vigas.beam_analyzer import (
    TQSBeamAnalyzer,
    VigaVao,
    VigaDiagnostico,
    AuditoriaVigasResultado,
)
from src.agent.tools import ToolsRegistry


class TestAnaliseVigas(unittest.TestCase):
    def setUp(self):
        self.skill = AnaliseVigasSkill()

    def test_skill_metadata(self):
        self.assertEqual(self.skill.nome, "analisar_vigas_pavimento")
        self.assertIn("vigas", self.skill.descricao.lower())
        self.assertIn("biela", self.skill.descricao.lower())
        self.assertIn("vrd2", self.skill.descricao.lower())

    def test_registry_contains_skill(self):
        reg = ToolsRegistry()
        self.assertIn("analisar_vigas_pavimento", reg._skills)
        tools = reg.listar_ferramentas_para_llm()
        tool_names = [t["function"]["name"] for t in tools]
        self.assertIn("analisar_vigas_pavimento", tool_names)

    def test_consolidacao_viga_critica_esmagamento(self):
        analyzer = TQSBeamAnalyzer("054")
        # Simula viga com biela excedida (V21)
        v_estrib = {
            "num": 21,
            "nome": "V21",
            "vaos": [
                {
                    "vao_id": "1",
                    "comp_m": 2.23,
                    "bw_cm": 19.0,
                    "h_cm": 50.0,
                    "vsd_max": 85.06,
                    "vrd2": 44.14,
                    "biela_ratio": 1.927,
                    "bitola_estribo": 50.0,
                    "espacamento_estribo": 14.0,
                    "ramos_estribo": 2,
                    "eh_biela_excedida": True,
                    "eh_bitola_invalida": True,
                    "eh_vao_curto_espurio": False,
                }
            ]
        }
        v_relger = {
            "num": 21,
            "nome": "V21",
            "vaos": [{"vao_id": "1", "comp_m": 2.23, "bw_cm": 19.0, "h_cm": 50.0}],
            "m_neg_max": 0.8,
            "m_pos_max": 20.1,
            "as_max": 17.8,
            "detalhes_barras": "6 B 20.0mm",
        }

        diag = analyzer._consolidar_viga(21, v_estrib, v_relger, fck_kgf_cm2=300.0)
        self.assertEqual(diag.nome, "V21")
        self.assertEqual(diag.status, "CRITICO")
        self.assertAlmostEqual(diag.vsd_max_tf, 85.06, places=1)
        self.assertAlmostEqual(diag.vrd2_tf, 44.14, places=1)
        self.assertTrue(any("biela comprimida" in f.lower() for f in diag.falhas))
        self.assertTrue(any("50.0mm" in f.lower() for f in diag.falhas))
        self.assertIsNotNone(diag.sugestao_correcao)
        self.assertIn("Alargar", diag.sugestao_correcao)

    def test_consolidacao_viga_vao_curto(self):
        analyzer = TQSBeamAnalyzer("054")
        # Simula viga com vão de 10cm (V1)
        v_estrib = {
            "num": 1,
            "nome": "V1",
            "vaos": [
                {
                    "vao_id": "1",
                    "comp_m": 6.07,
                    "bw_cm": 19.0,
                    "h_cm": 50.0,
                    "vsd_max": 4.33,
                    "vrd2": 44.74,
                    "biela_ratio": 0.09,
                    "bitola_estribo": 5.0,
                    "espacamento_estribo": 17.0,
                    "ramos_estribo": 2,
                    "eh_biela_excedida": False,
                    "eh_bitola_invalida": False,
                    "eh_vao_curto_espurio": False,
                },
                {
                    "vao_id": "2",
                    "comp_m": 0.10,
                    "bw_cm": 19.0,
                    "h_cm": 50.0,
                    "vsd_max": 3.43,
                    "vrd2": 44.74,
                    "biela_ratio": 0.08,
                    "bitola_estribo": 50.0,
                    "espacamento_estribo": 1.0,
                    "ramos_estribo": 2,
                    "eh_biela_excedida": False,
                    "eh_bitola_invalida": True,
                    "eh_vao_curto_espurio": True,
                }
            ]
        }
        v_relger = {
            "num": 1,
            "nome": "V1",
            "vaos": [],
            "m_neg_max": 3.3,
            "m_pos_max": 3.4,
            "as_max": 2.4,
            "detalhes_barras": "2 B 12.5mm",
        }

        diag = analyzer._consolidar_viga(1, v_estrib, v_relger, fck_kgf_cm2=300.0)
        self.assertEqual(diag.nome, "V1")
        self.assertEqual(diag.num_vaos, 2)
        self.assertTrue(any("espurio" in f.lower() for f in diag.falhas))

    def test_execucao_real_054_piso2(self):
        caminho_054 = r"C:\TQS\Flexinc - [054] Visconde do Herval CA"
        if not os.path.exists(caminho_054):
            self.skipTest("Pasta do edifício 054 não acessível no ambiente.")

        res = self.skill.executar("054", pavimento="2", formato="resumo")
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["status"], "critico")
        self.assertIn("PISO DO 2^PAVIMENTO", res["pavimentos_analisados"])

        metricas = res["metricas"]
        self.assertEqual(metricas["total_vigas"], 61)
        self.assertGreaterEqual(metricas["vigas_criticas"], 4)

        # Verifica vigas críticas identificadas
        dados = res["dados_completos"][0]["vigas"]
        mapa_v = {v["nome"]: v for v in dados}

        self.assertIn("V21", mapa_v)
        self.assertEqual(mapa_v["V21"]["status"], "CRITICO")
        self.assertAlmostEqual(mapa_v["V21"]["vsd_max_tf"], 85.1, delta=1.0)

        self.assertIn("V8", mapa_v)
        self.assertEqual(mapa_v["V8"]["status"], "CRITICO")

        self.assertIn("V3", mapa_v)
        self.assertEqual(mapa_v["V3"]["status"], "CRITICO")

        self.assertIn("V10", mapa_v)
        self.assertGreater(mapa_v["V10"]["m_neg_max_tfm"], 300.0)
        self.assertGreater(mapa_v["V10"]["as_max_cm2"], 100.0)


if __name__ == "__main__":
    unittest.main()
