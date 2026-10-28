---
name: auditoria-lajes
description: Audita lajes, grelhas, flechas (ELS) e quantitativos de formas e concreto no software TQS V25 conforme a NBR 6118:2023. Detecta balanços desbalanceados, bordos livres em concavidade, lajes delgadas com risco de deformação excessiva e nós hipostáticos. Use quando o usuário pedir para verificar lajes, auditar grelha, checar flechas de lajes ou quantitativo de lajes.
---

# Auditoria de Lajes, Grelhas e Flechas (NBR 6118:2023)

Esta skill realiza o diagnóstico integral das lajes e grelhas espaciais geradas no TQS V25, identificando problemas geométricos, incompatibilidades de nível e patologias potenciais de flechas em serviço.

## Arquivos Processados
- `<PAVIMENTO>.LST`: Quantitativo discriminado por laje ($L_i$), área estruturada ($m^2$), área de fôrmas ($m^2$), volume de concreto ($m^3$) e espessura média.
- `GREEXT.LST`: Avisos de balanços nas coordenadas globais $(X, Y)$ e consistência de nós e barras.
- `GREFOR.LST`: Critérios de rigidez, $f_{ck}$, inércias torcionais e apoios elásticos independentes de pilares.
- `MENAVI.LST`: Mensagens de inconsistências de contorno (bordos livres em concavidades e nivelamento).

## Verificações Realizadas
1. **Consistência de Apoios e Bordos:**
   - Detecção de lajes com bordo livre em concavidade (redistribuição anômala de tensões).
   - Incompatibilidades de nivelamento entre vigas e lajes adjacentes.
2. **Estabilidade de Balanços:**
   - Identificação de balanços não contraventados com risco de rotação ou vibração.
3. **Flechas e Esbeltez (NBR 6118):**
   - Rastreamento de lajes com espessura delgada ($h < 10\text{ cm}$) e vãos representativos, alertando para necessidade de verificação de flechas diferidas com armadura de compressão.

## Como Executar
Pelo orquestrador do Agente:
`auditar_lajes_edificio(edificio_nome="054", pavimento="2")`
