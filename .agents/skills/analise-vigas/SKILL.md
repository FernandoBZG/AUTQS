---
name: analise-vigas
description: >-
  Audita e dimensiona vigas de concreto armado conforme a NBR 6118:2023 no software TQS V25.
  Analisa momentos fletores (Mk), força cortante (Vk), verifica esmagamento da biela comprimida de concreto
  (VSd ≤ VRd2), calcula armadura transversal mínima/necessária (Asw/s) e flechas em ELS.
  Use quando o usuário pedir para analisar vigas, dimensionar vigas, verificar bielas de concreto, auditar cortante ou checar flechas.
---

# Auditoria e Análise de Vigas no TQS V25

Esta habilidade audita os esforços solicitantes e as condições de resistência e serviço das vigas de concreto armado.

---

## 🎯 Quando Utilizar Esta Skill

1. **Verificação de Ruptura de Biela Comprimida ($V_{Sd} \le V_{Rd2}$)**: Identificar vigas sob risco de esmagamento do concreto junto aos apoios.
2. **Dimensionamento ao Cortante ($A_{sw}/s$)**: Avaliar a taxa de estribos necessária para equilibrar a força cortante máxima.
3. **Flechas e Deformações (ELS)**: Alertar quando o vão-altura ($L/d$) for excessivo e gerar risco de fissuração em alvenarias apoiadas.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_06_analise_vigas.skill import AnaliseVigasSkill

skill = AnaliseVigasSkill()
resultado = skill.executar(
    edificio_nome="054",
    pavimento="terreo",
    viga="V1",
    formato="resumo"
)
```
