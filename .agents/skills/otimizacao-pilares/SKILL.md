---
name: otimizacao-pilares
description: >-
  Audita os pilares já dimensionados pelo TQS V25 (SELEC/LISPIL/CARPIL/INICIA) conforme a NBR 6118:2023;
  não redimensiona: só diagnostica e sugere seções.
  Analisa esforços axiais máximos (Nk), momentos fletores (Mx, My), calcula esbeltez (λ),
  avalia armadura longitudinal necessária e taxa de aço (As/Ac), e recomenda ajustes de seção
  quando a taxa de armadura ultrapassa os limites econômicos ou normativos (hiper-armado: ρ ≥ 2,5%; esbelto: λ > 90; superdimensionado: ρ ≤ 0,7% e ν ≤ 0,28).
  Volume de concreto e peso de aço usam o pé-direito real de cada lance (PD do PILAR/INICIA.LST).
  Use quando o usuário pedir para analisar pilares, dimensionar pilares, otimizar seções de pilares ou verificar taxas de armadura.
---

# Auditoria e Otimização de Pilares no TQS V25

Esta habilidade audita a segurança e a economia dos pilares da estrutura contra critérios da NBR 6118.

---

## 🎯 Quando Utilizar Esta Skill

1. **Auditoria de Esbeltez e Taxa de Aço**: Identificar pilares hiper-solicitados ou com taxa de armadura ρ ≥ 2,5% (critério econômico do AUTQS; o limite da NBR é 4% fora da emenda).
2. **Recomendação de Redimensionamento**: Sugerir aumento de seção $(\Delta b, \Delta h)$ para baratear o consumo de aço.
3. **Restrição de Largura Fixa**: Avaliar expansões apenas no comprimento $h$ quando a arquitetura não permite aumentar a largura $b$.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_04_otimizacao_pilares.skill import OtimizacaoPilaresSkill

skill = OtimizacaoPilaresSkill()
resultado = skill.executar(
    edificio_nome="054",
    pilar="P4",
    formato="resumo"
)
```
