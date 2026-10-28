---
name: estabilidade-global
description: Audita a estabilidade global (GamaZ, FAVt, Alfa) e deslocamentos de vento em ELS (drift de topo H/1700 e interpiso Hi/850) conforme a NBR 6118:2023 no TQS V25. Classifica a estrutura em nós fixos ou móveis e diagnostica deslocamentos excessivos. Use quando o usuário pedir para verificar estabilidade global, auditar GamaZ, checar deslocamentos de vento, drift ou estabilidade do edifício.
---

# Auditoria de Estabilidade Global e ELS (NBR 6118:2023)

Esta skill audita os resultados do pórtico espacial do TQS V25, extraindo automaticamente os parâmetros de não-linearidade geométrica e deslocamentos horizontais.

## Arquivos Processados no TQS
- `ESPACIAL/PORALF.LST` ou `ESPACIAL/PORGAMZ.LST`:
  - Parâmetro GamaZ ($\gamma_z$) para os casos simples de vento (0°, 90°, 180°, 270°).
  - Parâmetro $FAV_t$ para combinações de ELU (Equações 11.1 e 11.2 da NBR 6118).
  - Parâmetro Alfa ($\alpha$) de estabilidade global.
  - Tabela de deslocamentos máximos de topo ($H/1700$).
  - Tabela de deslocamentos máximos entre pisos consecutivos ($H_i/850$).

## Critérios Normativos da NBR 6118:2023
1. **Classificação da Estrutura:**
   - $\gamma_z \le 1.10$: Estrutura de **Nós Fixos** (efeitos de 2ª ordem globais desprezíveis $< 10\%$).
   - $1.10 < \gamma_z \le 1.30$: Estrutura de **Nós Móveis** (efeitos de 2ª ordem obrigatórios, estimáveis por $0.95 \cdot \gamma_z$ ou análise P-Delta).
   - $\gamma_z > 1.30$: **Instabilidade Excessiva** (proibido dimensionamento simplificado; exige enrijecimento da estrutura).
2. **Deslocamento Horizontal no Topo (ELS-DEF):**
   - Limite: $d_{topo} \le H / 1700$.
3. **Deslocamento Horizontal Interpavimentos (Dano a Alvenarias):**
   - Limite: $\Delta d_i \le H_i / 850$.

## Como Executar
Pelo orquestrador do Agente:
`auditar_estabilidade_global(edificio_nome="054")`
