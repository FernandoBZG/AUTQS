---
name: formas-alvenaria
description: >-
  Gera a prancha executiva de pré-formas de alvenaria estrutural (1ª fiada) no software TQS Alvest.
  A base é sempre o DesFiad1.DWG, sobrepondo contornos de lajes exteriores e sacadas no Nível 237,
  limpando elementos de armaduras verticais poluídos, cotando aberturas e vãos ($BLVAO), inserindo
  resumo de materiais (LISTMELV), corte esquemático de resistências e moldura oficial ABNT.
  Use quando o usuário pedir para gerar pré-forma de alvenaria, desenhar a 1ª fiada, emitir formas do Alvest ou modular blocos.
---

# Pré-Formas de Alvenaria Estrutural (1ª Fiada) no TQS Alvest

Esta habilidade transforma o desenho bruto de 1ª fiada de alvenaria estrutural do TQS Alvest (`DesFiad1.DWG`) em uma prancha executiva de pré-formas (`PRE_FOR_1aFIADA_*.DWG`) oficial, padronizada e pronta para emissão conforme as normas ABNT e práticas de engenharia estrutural.

---

## 🎯 Regras Obrigatórias de Projeto & Guardrails Anti-Conflito

Para evitar contaminação de geometria, linhas duplicadas e conflitos visuais no CAD, o pipeline segue rigorosamente os seguintes guardrails:

### 1. Base da Planta e Geometria Fiel
* A base geométrica deve ser **sempre** o `DesFiad1.DWG` do pavimento correspondente.
* Jamais reconstruir ou redesenhar blocos a partir de esboços quando o desenho nativo do Alvest estiver disponível.
* Realizar backup automático antes de sobrescrever qualquer arquivo existente.

### 2. Isolamento Estrito de Pavimentos Diferenciados (Regra Anti-Conflito)
* **Pavimentos Diferenciados** (ex: 2º Pavimento, 1º Pavimento, Térreo, Transição, Cobertura) possuem balanços de sacada e contornos de laje específicos que diferem do Pavimento Tipo.
* **PROIBIÇÃO ESTRITA:** É terminantemente proibido utilizar arquivos de referência que contenham `_Tipo` (`PRE_FOR_1aFIADA_Tipo.DWG`, revisões `Tipo-R01`, etc.) para extrair contornos de lajes em pavimentos não-tipo (`"TIPO" not in pavimento.upper()`).
* Para pavimentos diferenciados, os contornos de laje devem ser extraídos exclusivamente do arquivo nativo do próprio pavimento (`{pavimento}.DWG`, ex: `2^ PAVIMENTO.DWG`).
* Somente pavimentos que sejam explicitamente do tipo Tipo (`"TIPO" in pavimento.upper()`) podem consultar referências de Pavimento Tipo.

### 3. Princípio da Fonte Única Autoritativa (Single Source of Truth)
* Os contornos de lajes externas e sacadas (Nível 237) devem ser importados de um **único** arquivo de referência (o mais completo e consistente).
* **NUNCA mesclar ou acumular linhas de múltiplos arquivos de referência**, pois isso gera linhas duplicadas, sobreposição de contornos com pequenas variações dimensionais e conflitos no CAD.

### 4. Diferenciação Estrita de Camadas (Layers)
* **Nível 237 (Cor 6 / Magenta ou Ciano):** Exclusivo para contornos exteriores de lajes, bordas de sacadas e 'X' em shafts.
  - **PROIBIÇÃO ESTRITA:** NUNCA converter vigas de concreto (`FOR*.DWG` Nível 1) ou divisórias internas de laje (`LAJ*.DWG` Nível 0) para o Nível 237. Vigas e malhas de laje interna pertencem exclusivamente aos seus respectivos subsistemas e geram poluição crítica se projetadas no Nível 237.
  - **PROIBIÇÃO ESTRITA:** NUNCA converter o Nível 231 (eixos/paredes do modelador) para o Nível 237, sob risco de desenhar contornos de parede sobrepostos aos blocos de alvenaria.
* **Níveis 10 e 13:** Identificador de lajes (`L#`) e espessuras (`h=...`), importados estritamente do `LAJ*.DWG` nativo do pavimento.
* **Nível 239:** Cotas e dimensões modulares dos vãos ($BLVAO).
* **Nível 221:** Juntas de dilatação/movimentação e modulação de blocos.
* **Nível 222:** Título oficial da prancha executiva.
* **Nível 230 / Nível 0:** Moldura técnica oficial TQS/ABNT, carimbo/selo e marcas de dobra.

### 5. Isolamento Espacial da Coluna Técnica Lateral
* Resumo de materiais (`LISTMELV`), Legenda de Blocos Cerâmicos e Notas Técnicas de Projeto devem ser posicionados exclusivamente na coluna lateral técnica à direita da planta útil ($X > X_{max} + 50.0$).
* Nenhum elemento da coluna técnica pode ter coordenadas sobrepostas à área útil da planta de alvenaria.

### 6. Auto-Proteção contra Leitura do Arquivo de Saída e Anti-Auto-Infecção
* O próprio arquivo que está sendo gerado ou sobrescrito (`caminho_saida_dwg`), backups temporários (`*BKP*`, `*BAK*`) e saídas automáticas anteriores (`PRE_FOR_1aFIADA*.DWG` sem sufixo de revisão oficial `-R` ou `EP`) são sumariamente desconsiderados como candidatos de referência, evitando reimportação recursiva de dados defeituosos.

### 7. Tratamento de Vãos ($BLVAO)
* **Portas (Nível 251):** Blocos de alvenaria no vão devem ser apagados na 1ª fiada; o texto da dimensão modular ($BLVAO) é inserido no centro geométrico da abertura.
* **Janelas (Nível 252):** Os blocos sob o peitoril são preservados na 1ª fiada; o texto da dimensão modular é posicionado externamente (acima ou abaixo da parede) para clareza visual.

### 8. Purga de Poluição Visual
* Apagar textos de armaduras verticais (`pf12.5`, Nível 198).
* Apagar blocos de ferro vertical (`$PFERV`).
* Apagar identificadores brutos de vãos (`$IDnPRT`).
* Apagar cotas numéricas internas modulares repetitivas (Nível 221).
* Apagar textos de exaustão/telas antigas (Nível 7).

### 9. Marcação de Shafts e Furos de Laje com 'X' (Convenção Executiva)
* **Shafts Retangulares:** Furos e aberturas de prumadas através da laje (hidráulica, elétrica, ventilação e ar-condicionado).
* **Indicação Visual:** Dois traços diagonais cruzados formando um "X" conectando os vértices opostos do retângulo:
  - Linha 1: $(x_{min}, y_{min}) \to (x_{max}, y_{max})$
  - Linha 2: $(x_{min}, y_{max}) \to (x_{max}, y_{min})$
* **Camada e Cor:** **Nível 237, Cor 6 (Magenta/Ciano)**.
* **Contorno Retangular:** O perímetro fechado do shaft também deve estar desenhado no Nível 237 (Cor 6), delimitando claramente a abertura contra os blocos de alvenaria e a laje maciça.
* **Prevenção de Duplicatas:** Normalização de segmentos antes da inserção para garantir que o traço do "X" e as bordas ortogonais não sejam duplicados no CAD.

---

## 📋 Tabela de Camadas e Níveis TQS Alvest

| Nível (Layer) | Elemento | Cor Típica | Finalidade no Projeto |
| :---: | :--- | :---: | :--- |
| **0** | Elementos Gerais e Moldura | 7 (Branco) | Borda da folha e divisórias |
| **10** | Identificador de Laje (`L1`, `L2`, ...) | 0 (Padrão) | Identificação das lajes do pavimento |
| **13** | Espessura de Laje (`h=12`, etc.) | 0 (Padrão) | Especificação das espessuras de laje |
| **203/213/241** | Alvenarias e Blocos de 1ª Fiada | Diversas | Geometria dos blocos cerâmicos/concreto |
| **221** | Juntas de Controle / Modulação | 1 (Vermelho) | Juntas secas e juntas de movimentação |
| **222** | Título Oficial da Prancha | 0 (Padrão) | Título executivo padronizado |
| **230** | Margens e Carimbo Oficial TQS | 2 (Amarelo) | Margens ABNT, carimbo e marcas de dobra |
| **237** | Contorno de Lajes Externas, Sacadas e Shafts (X) | 6 (Magenta/Ciano) | Borda livre de lajes, sacadas e 'X' indicativo de buraco/shaft |
| **239** | Dimensões Modulares de Vãos | 4 (Ciano) | Cotas de portas e janelas ($BLVAO) |
| **247** | Paredes Estruturais / Contornos | 4 (Ciano) | Alinhamento e contorno das paredes |
| **251** | Vãos de Portas | - | Marcação interna de vãos de porta |
| **252** | Vãos de Janelas | - | Marcação de vãos de janela |

---

## 🚀 Como Invocar via Python ou Chat

### Execução via Python
```python
from src.skills.case_03_formas_alvenaria.skill import FormasAlvenariaSkill

skill = FormasAlvenariaSkill()

# Para pavimento diferenciado (ex: 2º Pavimento):
resultado = skill.executar(
    edificio_nome="055",
    pavimento="2^ PAVIMENTO",
    escala=50
)

# Para pavimento tipo:
resultado = skill.executar(
    edificio_nome="054",
    pavimento="TIPO A",
    escala=50
)
```

### Validações de Qualidade Automáticas
O método `validar()` da skill garante que:
1. O arquivo `.DWG` gerado exista e possua tamanho válido (> 10 KB).
2. As camadas estruturais e de identificação essenciais estejam presentes: `[10, 13, 222, 230, 239, 247]`.
3. A camada **237** seja obrigatória sempre que houver sacadas externas ou shafts mapeados no pavimento, sem forçar linhas artificiais em pavimentos sem balanço (como coberturas e reservatórios).
4. Lajes e vãos tenham sido quantificados e mapeados com sucesso.
5. A escala seja estritamente 1:50.
