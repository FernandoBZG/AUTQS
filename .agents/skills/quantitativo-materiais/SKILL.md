---
name: quantitativo-materiais
description: Extrai quantitativos globais de materiais (concreto m³, formas m², aço kg, área m² e pegada de carbono kgCO2) e índices de consumo (espessura média em, taxa de formas m²/m², consumo de aço kg/m³) no software TQS V25. Use quando o usuário pedir quantitativos de materiais, consumo de concreto/aço/formas, índices de consumo, taxa de aço ou pegada de carbono.
---

# Quantitativo Global de Materiais e Índices de Consumo

Esta skill extrai as tabelas oficiais de materiais geradas pelo TQS V25 a partir do processamento global do edifício, consolidando os consumos e índices econômicos.

## Arquivos Processados no TQS
- `ESPACIAL/RESEST2.TXT`: Matriz detalhada por pavimento dividida em Pilares, Vigas, Lajes e Fundações.
- `ESPACIAL/RESEST3.TXT`: Totalizador por pavimento de concreto ($m^3$), fôrmas ($m^2$), aço ($kgf$) e área estruturada ($m^2$).
- `ESPACIAL/RESEST4.TXT`: Índices médios calculados pelo sistema ($e_m$, taxa de fôrmas $m^2/m^2$, taxa de aço $kg/m^3$ e $kg/m^2$).
- `ESPACIAL/RESEST8.TXT`: Emissões de Carbono incorporado ($kgCO_2$) por piso e total global do edifício.

## Principais Indicadores Calculados
1. **Espessura Média ($e_m = \text{Volume} / \text{Área}$):**
   - Faixa usual: $0.18\text{ m}$ a $0.25\text{ m}$.
2. **Taxa de Fôrmas ($\text{Fôrma} / \text{Área}$):**
   - Faixa usual: $1.80\text{ m}^2/\text{m}^2$ a $2.50\text{ m}^2/\text{m}^2$.
3. **Consumo de Aço ($\text{kg}/\text{m}^3$ e $\text{kg}/\text{m}^2$):**
   - Faixa usual: $80\text{ a }110\text{ kg}/\text{m}^3$.
4. **Pegada de Carbono ($\text{kgCO}_2/\text{m}^2$):**
   - Mede sustentabilidade e impacto ambiental do concreto e aço empregados.

## Como Executar
Pelo orquestrador do Agente:
`extrair_quantitativo_materiais(edificio_nome="054")`
