import os
import unittest
from src.skills.case_03_formas_alvenaria.skill import FormasAlvenariaSkill
from src.drawing.alvenaria_dwg_builder import AlvenariaDwgBuilder

class TestFormasAlvenaria(unittest.TestCase):
    def test_formas_alvenaria_skill_metadata(self):
        skill = FormasAlvenariaSkill()
        self.assertEqual(skill.nome, "gerar_planta_formas_alvenaria")
        self.assertIn("alvenaria estrutural", skill.descricao.lower())
        self.assertIn("desfiad1", skill.descricao.lower())

    def test_formas_alvenaria_executar_054(self):
        skill = FormasAlvenariaSkill()
        pasta_ed = r"C:\TQS\Flexinc - [054] Visconde do Herval AE"
        if not os.path.exists(pasta_ed):
            self.skipTest("Edifício 054 não disponível neste ambiente.")

        saida_teste = os.path.join(pasta_ed, "TIPO A", "PRE_FOR_1aFIADA_TEST_UNIT.DWG")
        try:
            resultado = skill.executar(
                edificio_nome="054",
                pavimento="TIPO A",
                caminho_saida_dwg=saida_teste,
                escala=50,
            )

            self.assertEqual(resultado["status"], "sucesso")
            self.assertTrue(resultado["sucesso"])
            self.assertTrue(os.path.exists(saida_teste))
            self.assertGreater(os.path.getsize(saida_teste), 10000)

            # Valida lajes e vãos
            self.assertGreaterEqual(resultado["total_lajes"], 20)
            self.assertGreaterEqual(resultado["total_vaos"], 40)

            # Valida auditoria DWG
            aud = resultado["auditoria"]
            self.assertEqual(aud["escala"], 50.0)
            self.assertGreater(aud["total_textos"], 300)
            niveis = aud["niveis_utilizados"]
            for lvl in [10, 13, 222, 230, 239, 247]:
                self.assertIn(lvl, niveis)

            # Valida que todos os textos de vãos (239) e lajes (10, 13) estão estritamente no edifício
            # e que o contorno das lajes externas (Nível 237) está desenhado ao redor do edifício
            from TQS import TQSDwg
            dwg = TQSDwg.Dwg(pedmv=0)
            dwg.file.Open(saida_teste)
            it = dwg.iterator
            it.Begin()
            linhas_237 = 0
            while True:
                pos = it.GetElementReadPosition()
                if pos:
                    lvl = it.level
                    if it.elementName == "Texto":
                        if lvl in [10, 13, 239]:
                            self.assertGreaterEqual(it.x1, -1200.0, f"Texto nível {lvl} com X={it.x1} fora do edifício!")
                            self.assertLessEqual(it.x1, 2300.0, f"Texto nível {lvl} com X={it.x1} fora do edifício!")
                            self.assertGreaterEqual(it.y1, -1600.0, f"Texto nível {lvl} com Y={it.y1} fora do edifício!")
                            self.assertLessEqual(it.y1, 100.0, f"Texto nível {lvl} com Y={it.y1} fora do edifício!")
                        self.assertLessEqual(it.x1, 5000.0, f"Texto disperso em X={it.x1}!")
                    elif lvl == 237 and it.elementName in ["Linha", "Polyline"]:
                        linhas_237 += 1
                        self.assertGreaterEqual(it.x1, -1200.0, f"Linha 237 com X={it.x1} fora do edifício!")
                        self.assertLessEqual(it.x1, 2300.0, f"Linha 237 com X={it.x1} fora do edifício!")
                if not it.Next():
                    break
            dwg.file.Close()

            # Assegura que todas as lajes externas estão desenhadas (não apenas uma linha isolada à direita)
            self.assertGreaterEqual(linhas_237, 100, f"Contorno de lajes externas incompleto: {linhas_237} linhas!")

        finally:
            if os.path.exists(saida_teste):
                try:
                    os.remove(saida_teste)
                except Exception:
                    pass

    def test_precarregar_referencia_isolamento_pavimento_nao_tipo(self):
        """
        Garante que pavimentos diferenciados (ex: 2º Pavimento do 055)
        utilizam EXCLUSIVAMENTE a geometria nativa do pavimento (2^ PAVIMENTO.DWG)
        e JAMAIS carregam contornos de pavimentos Tipo ou convertem nivel 231 (alvenaria) em laje.
        """
        pasta_055 = r"C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\2^ PAVIMENTO"
        pasta_gerais_055 = r"C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\GERAIS"
        if not os.path.exists(pasta_055):
            self.skipTest("Edificio 055 nao disponivel neste ambiente.")

        builder = AlvenariaDwgBuilder()
        bounds = [10072.0, 16842.5, -3806.1, -2577.3]
        saida_falsa = os.path.join(pasta_055, "PRE_FOR_1aFIADA_2^ PAVIMENTO.DWG")

        res = builder._precarregar_elementos_referencia(
            pasta_055, pasta_gerais_055, bounds, caminho_saida_dwg=saida_falsa
        )

        lajes = res["lajes_externas"]
        # Deve carregar exatamente as 125 linhas limpas do 2^ PAVIMENTO.DWG
        self.assertEqual(len(lajes), 125, f"Esperado 125 linhas de laje no 2º Pavimento, obtido {len(lajes)}")

        # Todos os itens de lajes externas devem ser estritamente Nivel 237
        for item in lajes:
            self.assertEqual(item["nivel"], 237)

        # Coluna lateral deve ter os blocos e notas técnicas carregados
        laterais = res["laterais"]
        self.assertGreaterEqual(len(laterais), 30)

    def test_desenhar_x_shafts_retangulares(self):
        """
        Valida que shafts retangulares (furos / vazios de laje) recebem as diagonais cruzadas
        em 'X' no Nível 237 (Cor 6), indicando buraco de laje conforme padrão executivo.
        """
        pasta_055 = r"C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\16PV"
        if not os.path.exists(pasta_055):
            self.skipTest("Edificio 055 16PV nao disponivel neste ambiente.")

        dwg_16 = os.path.join(pasta_055, "PRE_FOR_1aFIADA_16PV.DWG")
        self.assertTrue(os.path.exists(dwg_16), f"Arquivo não encontrado: {dwg_16}")

        from TQS import TQSDwg
        d = TQSDwg.Dwg(pedmv=0)
        res_open = d.file.Open(dwg_16)
        self.assertEqual(res_open, 0, f"Erro ao abrir DWG: {res_open}")

        it = d.iterator
        it.Begin()
        diagonais_237 = []
        while True:
            pos = it.GetElementReadPosition()
            if pos and it.level == 237 and it.elementName in ["Linha", "Polyline"]:
                dx = abs(it.x2 - it.x1)
                dy = abs(it.y2 - it.y1)
                if dx > 10.0 and dy > 10.0:
                    diagonais_237.append((it.x1, it.y1, it.x2, it.y2, it.color))
            if not it.Next():
                break
        d.file.Close()

        # Deve conter pelo menos 100 linhas diagonais formando os pares de 'X' dos shafts
        self.assertGreaterEqual(len(diagonais_237), 100, f"Poucas diagonais de shafts encontradas: {len(diagonais_237)}")
        # Todas devem ser Cor 6 (ciano/magenta)
        for dl in diagonais_237:
            self.assertEqual(dl[4], 6, f"Cor da diagonal de shaft incorreta: {dl[4]} (esperado 6)")

    def test_cobertura_nivel_237_limpo(self):
        """
        Valida que na Cobertura (pavimento técnico de topo) o Nível 237 está estritamente limpo:
        - JAMAIS converte vigas de concreto (FOR*.DWG) para o Nível 237;
        - JAMAIS converte divisórias de lajes internas (LAJ*.DWG) para o Nível 237;
        - JAMAIS importa shafts residenciais de apartamentos do Pavimento Tipo;
        - Contém exclusivamente as linhas nativas válidas (<= 10 linhas).
        """
        pasta_055_cob = r"C:\TQS\Flexinc - [055] Jardim Europa AE Ceramica\COBERTURA"
        if not os.path.exists(pasta_055_cob):
            self.skipTest("Edifício 055 COBERTURA não disponível neste ambiente.")

        dwg_cob = os.path.join(pasta_055_cob, "PRE_FOR_1aFIADA_COBERTURA.DWG")
        self.assertTrue(os.path.exists(dwg_cob), f"Arquivo não encontrado: {dwg_cob}")

        from TQS import TQSDwg
        d = TQSDwg.Dwg(pedmv=0)
        res_open = d.file.Open(dwg_cob)
        self.assertEqual(res_open, 0, f"Erro ao abrir DWG: {res_open}")

        it = d.iterator
        it.Begin()
        linhas_237 = 0
        diagonais_x = 0
        niveis = set()
        while True:
            pos = it.GetElementReadPosition()
            if pos:
                niveis.add(it.level)
                if it.level == 237 and it.elementName in ["Linha", "Polyline"]:
                    linhas_237 += 1
                    dx = abs(it.x2 - it.x1)
                    dy = abs(it.y2 - it.y1)
                    if dx > 15.0 and dy > 15.0:
                        diagonais_x += 1
            if not it.Next():
                break
        d.file.Close()

        # Camadas estruturais essenciais devem estar presentes
        for lvl in [10, 13, 222, 230, 239, 247]:
            self.assertIn(lvl, niveis, f"Camada essencial {lvl} ausente na Cobertura!")

        # Nível 237 deve ser estritamente limpo (<= 10 linhas) e conter ZERO shafts/diagonais de apartamentos
        self.assertLessEqual(linhas_237, 10, f"Nível 237 contaminado com excesso de linhas: {linhas_237}")
        self.assertEqual(diagonais_x, 0, f"Shafts de apartamentos foram indevidamente importados para a Cobertura: {diagonais_x} diagonais!")

if __name__ == "__main__":
    unittest.main()
