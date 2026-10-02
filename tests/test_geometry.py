import unittest
from src.core.models import GeometriaPilar, TipoSecao
from src.skills.case_01_planta_cargas.geometry import calcular_baricentro_pilar

class TestGeometriaBaricentro(unittest.TestCase):
    def test_pilar_retangular_ponto_fixo_1_sem_rotacao(self):
        # Pilar 20x50 cm com PF no canto inferior esquerdo (1) em (100, 200) cm
        geom = GeometriaPilar(
            tipo=TipoSecao.RETANGULAR,
            b=20.0,
            h=50.0,
            angulo_rotacao_graus=0.0,
            ponto_fixo_coord=(100.0, 200.0),
            ponto_fixo_indice=1
        )
        cg = calcular_baricentro_pilar(geom)
        self.assertAlmostEqual(cg.x, 110.0) # 100 + 20/2
        self.assertAlmostEqual(cg.y, 225.0) # 200 + 50/2

    def test_pilar_retangular_ponto_fixo_centro(self):
        # Pilar 25x60 cm com PF no centro (5) em (500, 500)
        geom = GeometriaPilar(
            tipo=TipoSecao.RETANGULAR,
            b=25.0,
            h=60.0,
            angulo_rotacao_graus=0.0,
            ponto_fixo_coord=(500.0, 500.0),
            ponto_fixo_indice=5
        )
        cg = calcular_baricentro_pilar(geom)
        self.assertAlmostEqual(cg.x, 500.0)
        self.assertAlmostEqual(cg.y, 500.0)

    def test_pilar_retangular_rotacionado_90_graus(self):
        # Pilar 20x60 com PF no canto inferior esquerdo (1) em (0, 0), rotacionado 90 graus
        # Offset local: dx=10, dy=30
        # Apos rotacao de 90 graus:
        # dx_glob = 10*cos(90) - 30*sin(90) = -30
        # dy_glob = 10*sin(90) + 30*cos(90) = +10
        geom = GeometriaPilar(
            tipo=TipoSecao.RETANGULAR,
            b=20.0,
            h=60.0,
            angulo_rotacao_graus=90.0,
            ponto_fixo_coord=(0.0, 0.0),
            ponto_fixo_indice=1
        )
        cg = calcular_baricentro_pilar(geom)
        self.assertAlmostEqual(cg.x, -30.0)
        self.assertAlmostEqual(cg.y, 10.0)

if __name__ == "__main__":
    unittest.main()
