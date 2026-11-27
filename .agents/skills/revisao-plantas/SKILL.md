---
name: revisao-plantas
description: >-
  Emite revisões de pranchas do Editor de Plantas do TQS V25 (.CPL): lista as pranchas com a
  revisão atual e o que está pendente, registra a próxima revisão (nº, data, autor e descrição
  sugerida a partir do que mudou desde a última plotagem) na tabela de revisões do selo, abre a
  prancha da nova fase em R00 quando a fase muda, preenche o carimbo, plota o PDF e o DXF da revisão com o
  motor de plotagem do TQS e confere a plotagem. Use quando o usuário pedir para emitir, registrar,
  listar, plotar ou conferir revisões de pranchas/plantas.
---

# Revisões de Pranchas do Editor de Plantas (TQS V25)

O TQS guarda o histórico de revisões de cada prancha no arquivo `<edifício>\PLANTAS\<ID>.CPL`
do Editor de Plantas. Na plotagem, o editor usa o carimbo preenchido `<ID>_CR.DWG` (tabela de
revisões `%REVISAO_TXTnn`, `%REVISAO_DATnn`, `%REVISAO_AUTnn`, `%REVISAO`...) e grava
`<ID>-Rnn.PDF` (e, conforme a opção usada, `.DXF/.PLW/.TXT`) em `PLANTAS`. Esta skill faz o ciclo
completo sem abrir o TQS: registra a revisão no `.CPL`, preenche o carimbo e plota o PDF.

---

## 🔁 Fluxo

1. **Listar** (`acao="listar"`): pranchas do edifício com fase, nº, título, revisão atual, última
   revisão e status: `em dia`, `pendente` (desenho alterado depois da última plotagem),
   `aguardando plotagem` (revisão registrada sem `-Rnn.PDF`).
2. **Emitir** (`acao="emitir"`): calcula a próxima revisão, sugere a descrição, mostra a prévia e
   só grava com `aprovado=True` (backup `<ID>.CPL_BKP_<timestamp>` antes).
   - **Troca de fase** (`fase="PE"`): cria `054-EST-PE-0601-....CPL` a partir da prancha atual,
     com a tabela zerada em R00 e o carimbo `_CR` duplicado; a prancha antiga fica intacta.
     O valor de `_FASE` é atualizado pelo usuário nas variáveis do Editor de Plantas.
   - Recusa emitir se a revisão atual ainda não foi plotada (use `forcar=True` se for intencional).
3. **Preencher** (`acao="preencher"`): gera `<ID>_CR.DWG` como o botão "Preencher" do Editor de
   Plantas — moldura do formato (PLANTAS.DAT) com cada `%VARIAVEL` trocada pelo valor no mesmo
   nível/posição/altura, variáveis vazias apagadas e `%PECASDET` quebrado em linhas de ~40
   caracteres a cada 0,3 cm. Valores: carimbo anterior (inclui `_FASE`, `_PAVIMENTO`,
   `_DISCIPLINA`) + `.CPL` (tabela de revisões, `%REVISAO`, `%PLANTA`, `%NUM_PLANTA`) + títulos
   (nível 222) dos desenhos. Mesma prévia/aprovação/backup da emissão.
4. **Plotar** (`acao="plotar"`): plota a revisão atual em PDF e DXF com o **motor de plotagem do TQS**
   (`NCVRPLD.EXE`, o mesmo que o Editor de Plantas usa) numa pasta temporária
   `%TEMP%\AUTQS_plot_*`: carimbo preenchido + cópia do `.CPL` com caminhos absolutos. Confere
   o PDF (carimbo de plotagem `<ID>-Rnn.PLT`, tamanho da folha, nenhuma `%VARIAVEL` sobrando,
   todas as linhas da tabela de revisões, DXF completo) e, com `aprovado=True`, grava `<ID>-Rnn.PDF`,
   `<ID>-Rnn.DXF` e o `<ID>_CR.DWG` em `PLANTAS` (backup `_BKP_<timestamp>` do que existir). Com divergência nas
   checagens não grava (salvo `forcar=True`).
   - Validado na R05 da `054-EST-PB-0601-TP-1FIA`: PDF idêntico ao do Editor de Plantas a
     1200 dpi; só muda a hora do carimbo de plotagem.
   - O motor não gera o `.TXT` de variáveis: a conferência usa o conteúdo do PDF.
   - O `-Rnn.DXF` gerado é a base da descrição sugerida na revisão seguinte (contra os desenhos
     inalterados dá "REEMISSÃO SEM ALTERAÇÕES").
5. **Conferir** (`acao="conferir"`): confere o `<ID>-Rnn.PDF` e, se houver, o `<ID>-Rnn.TXT`
   (`REVISAO`, linha da tabela, `_FASE`).

## 🧩 Fontes e regras

- **`.CPL`**: cabeçalho (token 13 = revisão atual, token 14 = nº de revisões), título, blocos de
  4 linhas por revisão e a lista de desenhos (escala, janela, inserção, máscara de níveis).
  Edição cirúrgica byte a byte em CP1252; ler e salvar sem alteração devolve o mesmo arquivo.
- **`NMCARQ.DAT`** (raiz do edifício): fases (EP, AP, PB, PE...) e o sufixo de revisão (`-R` + 2
  dígitos). O ID da prancha segue `projeto-agente-fase-nº-pavimento-elemento`.
- **Tabela da moldura**: 11 linhas (R00 a R10). Descrição recomendada até 60 caracteres, em MAIÚSCULAS.
- **Descrição sugerida**: compara os desenhos da prancha com o `-Rnn.DXF` da última plotagem.
- **Motor de plotagem** (`<TQSW>\EXEC\X64\NCVRPLD.EXE`): roda na pasta de trabalho e lê
  `SELDWG.TMP` (lista de `.CPL`) e `NCVRPLD.TMP` (formato: `1/1` PDF, `0/1` DXF, `1/0` PLT/PLW,
  `1/2` DWF, `1/3` SVG; o motor roda uma vez por formato); grava `OK` em `EXTDWG.TMP` e o PDF ao lado do
  `.CPL`. Não preenche as variáveis da moldura: o carimbo precisa estar preenchido antes.

## 🚀 Como Invocar

```powershell
.\autqs.bat --revisoes --edificio "054 AE"
.\autqs.bat --emitir-revisao --edificio "054 AE" --prancha 0601 --simular
.\autqs.bat --emitir-revisao --edificio "054 AE" --prancha 0601 --descricao "AJUSTE DO ELEVADOR"
.\autqs.bat --emitir-revisao --edificio "054 AE" --prancha 0601 --fase PE
.\autqs.bat --preencher-carimbo --edificio "054 AE" --prancha 0601 --simular
.\autqs.bat --plotar-revisao --edificio "054 AE" --prancha 0601 --simular
.\autqs.bat --plotar-revisao --edificio "054 AE" --prancha 0601
.\autqs.bat --conferir-revisao --edificio "054 AE" --prancha 0601
```

```python
from src.skills.case_15_revisao_plantas import RevisaoPlantasSkill

skill = RevisaoPlantasSkill()
previa = skill.executar(edificio_nome="054 AE", acao="emitir", prancha="0601")   # só prévia
gravado = skill.executar(edificio_nome="054 AE", acao="emitir", prancha="0601",
                         descricao=previa["revisao"]["descricao"], aprovado=True)
pdf = skill.executar(edificio_nome="054 AE", acao="plotar", prancha="0601", aprovado=True)
```

No chat: "emitir revisão da prancha 0601 do 054 AE", "plotar a prancha 0601 do 054 AE",
"listar revisões das pranchas do 054 AE", "conferir revisão da 0601". A gravação sempre pede
confirmação ("sim"/"não").
