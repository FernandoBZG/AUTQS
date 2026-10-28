---
name: memorial-calculo
description: Gera o Memorial Descritivo e Justificativo de Cálculo Estrutural do edifício no TQS V25 conforme a NBR 6118:2023, NBR 6120 e NBR 6123. Consolida estabilidade global (GamaZ, deslocamentos ELS), materiais, lajes, quantitativos de concreto, formas, aço e emissões de carbono em relatórios executivos em Markdown e HTML. Use quando o usuário pedir para gerar memorial descritivo, memorial de cálculo, relatório executivo da obra ou documentação do projeto.
---

# Memorial Descritivo e Justificativo de Cálculo Estrutural

Esta skill consolida e automatiza a geração do Memorial de Cálculo da edificação para entrega a clientes, órgãos fiscalizadores e aprovação técnica.

## Seções Padronizadas do Documento
1. **Identificação da Obra:** Dados do empreendimento, cotas, altura e sistema estrutural.
2. **Normas Técnicas Aplicadas:** NBR 6118:2023, NBR 6120:2019, NBR 6123:2023, NBR 6122:2022.
3. **Especificação de Materiais:** $f_{ck}$, módulo secante $E_{cs}$, aços CA-50 e CA-60.
4. **Estabilidade Global e Ações de Vento:** Verificação de $\gamma_z$, $FAV_t$, $\alpha$, drift de topo ($H/1700$) e drift entre pisos ($H_i/850$).
5. **Sistemas de Piso e Lajes:** Área estruturada, espessuras e modelos de grelha.
6. **Quantitativos e Sustentabilidade:** Balanço de concreto, formas, consumo de aço por volume/área e pegada de carbono ($kgCO_2$).
7. **Responsabilidade Técnica e Fechamento:** Campo para assinatura e registro profissional.

## Formatos Suportados
- **Markdown (.md):** Ideal para visualização inline, integração e edição.
- **HTML Imprimível (.html):** Pré-formatado com CSS para impressão em folha A4 e exportação direta para PDF no navegador.

## Como Executar
Pelo orquestrador do Agente:
`gerar_memorial_descritivo(edificio_nome="054", caminho_saida_md="relatorios/memorial_054.md")`
