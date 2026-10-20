---
name: consistencia-planta
description: >-
  Audita a consistência da Planta de Formas no TQS V25 antes do processamento estrutural.
  Detecta vigas sem apoio, lajes sem bordas fechadas, nós desconectados, desníveis incoerentes
  e inconsistências geométricas que impediriam a convergência do pórtico espacial ou grelha de lajes.
  Use quando o usuário pedir para verificar consistência da planta, auditar formas, checar apoios de vigas ou validar o modelo.
---

# Auditoria de Consistência da Planta de Formas no TQS V25

Esta habilidade valida a integridade topológica do modelo estrutural antes de enviar aos motores de cálculo de pórtico e grelha.

---

## 🎯 Quando Utilizar Esta Skill

1. **Pré-verificação de Cálculo**: Evitar erros de execução no TQS identificando nós soltos ou vigas sem apoio.
2. **Checagem de Lajes**: Confirmar que todos os perímetros de lajes estão devidamente delimitados por vigas ou bordas livres.
3. **Conformidade Normativa**: Relatar avisos e inconformidades com sugestões claras de correção.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_05_consistencia_planta.skill import ConsistenciaPlantaSkill

skill = ConsistenciaPlantaSkill()
resultado = skill.executar(
    edificio_nome="054",
    pavimento="terreo",
    formato="resumo"
)
```
