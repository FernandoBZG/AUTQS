---
name: planta-de-cargas
description: >-
  Emite pranchas executivas completas de Planta de Cargas e Locação de Fundações em DWG nativo
  no software TQS V25. Extrai as reações e momentos diretamente do PORLID/PORLIS, calcula baricentros
  exatos dos pilares, desenha linhas de centro com cotas dinâmicas, gera tabelas com os casos
  críticos configurados no PORLID3.DAT e aplica molduras oficiais conforme NBR 6118 e NBR 6122.
  Use quando o usuário solicitar planta de cargas, gabarito de fundações, locação de pilares ou exportação DWG.
---

# Planta de Cargas e Locação de Fundações no TQS V25

Esta habilidade automatiza a extração de dados de reações da fundação e gera pranchas `.DWG` nativas completas e oficiais prontas para emissão e plotagem.

---

## 🎯 Quando Utilizar Esta Skill

1. **Geração de Planta de Cargas**: Emitir a prancha técnica oficial de cargas da fundação.
2. **Locação de Pilares**: Calcular e plotar as coordenadas analíticas $(X_{cg}, Y_{cg})$ dos baricentros.
3. **Extração de Tabela de Cargas**: Montar a tabela de cargas com as 7 colunas normativas ($Pilar, F_z, F_x, F_y, M_x, M_y, M_z$) para cada caso crítico.
4. **Verificação de Tração**: Identificar pilares com $F_z < 0$ no caso **FZ MIN** do PORLID (lista `alertas` do resultado). Se o PORLID não tiver o caso FZ MIN, o resultado avisa que a tração não foi verificada; pilares sem reação no TQS aparecem como "-" e também geram alerta.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_01_planta_cargas.skill import PlantaDeCargasSkill

skill = PlantaDeCargasSkill()
resultado = skill.executar(
    edificio_nome="054",
    escala=50,
    # Caminho relativo é gerado numa pasta temporária; a prancha final sempre vai para
    # <edifício>\ESPACIAL\GABARITO.DWG (com backup em ESPACIAL\backup_claude)
    caminho_saida_desenho="GABARITO.DWG"
)
```
