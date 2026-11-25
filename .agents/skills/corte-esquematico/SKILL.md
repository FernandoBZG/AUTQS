---
name: corte-esquematico
description: >-
  Gera dinamicamente o arquivo DWG nativo TQS de Corte Esquemático com Resistências dos Materiais
  (GERAIS\CORTE ESQUEMÁTICO.DWG) para qualquer edifício no TQS V25, adaptando pavimentos,
  repetições, cotas acumuladas, pés-direitos, sistema estrutural (AE ou CA), fck do concreto e
  resistências da alvenaria (bloco, argamassa, graute e prisma oco). Use quando o usuário pedir
  para criar, gerar ou atualizar o corte esquemático de um edifício.
---

# Corte Esquemático com Resistências dos Materiais (TQS V25)

Esta skill gera automaticamente o desenho nativo TQS `GERAIS\CORTE ESQUEMÁTICO.DWG` para cada edifício, seguindo o padrão visual de referência de `D:\TQS\Flexinc - [054] Visconde do Herval AE\GERAIS\CORTE ESQUEMÁTICO.DWG`, sem textos genéricos ou macros não compiladas (`%Valor da cota`, `%Pavimento`).

---

## 🔍 Fontes de Dados Lidas Automaticamente

1. **Estrutura de Pavimentos (`TQSBuild.Building.floorsplan`):**
   - Nomes, ordem vertical, repetições (`GetRepetition`, expandindo pavimentos `TIPO` em `3o PAVTO`, `4o PAVTO`, etc.), pé-direito (`GetFloorHeight`) e cota acumulada.
2. **Materiais Gerais (`TQSBuild.Building.materials`):**
   - Tipo de alvenaria (`masonryMaterial`: `BLOCOS CERÂMICOS` ou `BLOCOS DE CONCRETO`).
   - Resistência do concreto de vigas/lajes e pilares (`beamConcreteStrength`, `columnConcreteStrength`, `GetFloorPlanConcreteStrength`).
3. **Resistências de Alvenaria por Pavimento (`<pavimento>\AEDIMALV.REP`):**
   - Extrai automaticamente `FBK` (bloco), `FAK` (argamassa), `FGK` (graute), `FPK` (prisma oco) e `FPKG` (prisma grauteado) para cada pavimento e nível de repetição.
   - Pavimentos sem `AEDIMALV.REP` são classificados automaticamente como **Concreto Armado (`CA`)**.

---

## 📋 Padrão de Camadas (Layers) no DWG Gerado

- **Nível 249 (Cor 3 - Verde):** Caixas dos pavimentos em Alvenaria Estrutural (`AE`).
- **Nível 248 (Cor 7 - Branco):** Caixas dos pavimentos em Concreto Armado (`CA`).
- **Nível 257 (Cor 7):** Especificações de materiais por pavimento (`BLOCO`, `ARGAMASSA`, `GRAUTE`, `PRISMA (OCO)`) e notas normativas (NBR 16868-3).
- **Nível 200 (Cor 7) & Nível 221 (Cor 11):** Linhas de nível e símbolo triangular de cota.
- **Nível 18 (Cor 2 - Amarelo):** Faixas verticais laterais indicando o sistema estrutural (`ALVENARIA ESTRUTURAL` / `PÓRTICO DE CONCRETO ARMADO`).
- **Formato de saída:** Gera **apenas `.DWG` nativo do TQS** (nunca `.DXF`), salvando em `<edificio>\GERAIS\CORTE ESQUEMÁTICO.DWG` (com backup `.BAK` se já existir).

---

## 🚀 Como Invocar via Python

```python
from src.skills.case_14_corte_esquematico.skill import CorteEsquematicoSkill

skill = CorteEsquematicoSkill()
resultado = skill.executar(
    edificio_nome="Casa Tua - Modificação",
    cota_base_m=0.0,
)
```
