---
name: limpeza-arquitetura-dwg
description: Limpa, purga e padroniza arquivos CAD brutos de arquitetura (DXF/DWG) para criação de bases de referência externas Geo_*.DWG no TQS V25. Remove hachuras pesadas, cotas, blocos de mobiliário e vegetação, e converte escala de metros para centímetros. Use quando o usuário pedir para limpar arquitetura, preparar DWG de arquitetura, gerar Geo_*.DWG, remover hachuras ou ajustar escala de plantas.
---

# Limpeza e Padronização de DWG de Arquitetura (Geo_*.DWG)

Esta skill prepara e higieniza plantas brutas recebidas de escritórios de arquitetura, gerando referências leves e perfeitamente compatibilizadas com o Modelador Estrutural do TQS V25.

## Procedimento de Otimização
1. **Purga de Entidades Pesadas:**
   - Elimina todas as hachuras (`HATCH`), sólidos e preenchimentos densos que causam lentidão gráfica.
   - Elimina cotas (`DIMENSION`), linhas de chamada (`LEADER`) e tabelas de esquadrias.
2. **Filtro de Camadas Parasitárias:**
   - Remove mobiliário (`MOBIL`, `LAYOUT`), paisagismo (`VEGET`), veículos e blocos humanos.
3. **Preservação de Elementos Estruturantes:**
   - Isola alvenarias, paredes, limites de desníveis, eixos e aberturas de portas/janelas.
4. **Conversão de Escala para Centímetros (x100):**
   - Converte automaticamente projetos desenhados em metros para centímetros ($cm$), garantindo encaixe 1:1 com as fôrmas do TQS.
5. **Geração de Arquivo Padrão TQS:**
   - Salva a base limpa com nomenclatura `Geo_<NOME_PAV>.dxf` para importação direta no Modelador.

## Como Executar
Pelo orquestrador do Agente:
`padronizar_arquitetura_tqs(caminho_arquivo="projetos/arq_terreo.dxf", fator_escala="auto")`
