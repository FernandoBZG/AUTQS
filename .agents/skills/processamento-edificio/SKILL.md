---
name: processamento-edificio
description: >-
  Executa o processamento estrutural completo ou de pórtico espacial de edifícios no TQS V25.
  Dispara as rotinas batch de consistência de plantas, grelha de lajes, pórtico espacial
  e extração de cargas/esforços, permitindo recálculo automático da estrutura.
  Use quando o usuário pedir para processar o edifício, calcular o pórtico espacial, rodar processamento global ou atualizar o modelo.
---

# Processamento de Edifícios no TQS V25

Esta habilidade controla a execução em lote (batch) dos motores de cálculo estrutural do TQS V25.

---

## 🎯 Quando Utilizar Esta Skill

1. **Processar Pórtico e Cargas**: Calcular o modelo espacial para obter as reações de fundação e envoltórias de pilares.
2. **Processamento Global**: Executar a análise estrutural completa incluindo armaduras de vigas, lajes e pilares.
3. **Pós-edição no Modelador**: Atualizar os resultados após modificar dimensões ou cargas no `TQSModelEditor`.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_02_processamento.skill import ProcessamentoEdificioSkill

skill = ProcessamentoEdificioSkill()
resultado = skill.executar(
    edificio_nome="054",
    tipo_processamento="portico_cargas",
    gerar_planta_apos_processar=True
)
```
