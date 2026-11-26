---
description: Regra de formato de saída gráfica no TQS - gerar apenas DWG nativo TQS, nunca DXF
---

# Formato de Desenho de Saída: Apenas DWG TQS

- Ao gerar desenhos de comparação, sobreposição, plantas ou pranchas no projeto AUTQS / TQS, **gerar apenas arquivos `.DWG` nativos do TQS** (via `TQSDwg` / `dwg_overlay.py`).
- **Não gerar arquivos `.DXF`** (`gerar_desenho_diff=False` por padrão), a menos que o usuário solicite explicitamente a exportação em DXF.
- **Local de salvamento:** Salvar os `.DWG` de comparação diretamente na **respectiva pasta de cada pavimento** dentro do edifício TQS (ex: `C:\TQS\<Edificio>\<Pavimento>\OVERLAY_<Pavimento>.DWG`).
- **Padrão de Cores:** Na sobreposição de geometria × forma, **a planta de geometria (`Geo_*.DWG`, `BL1`, `BL2`) será SEMPRE Vermelha (`cor=1`)** e **a planta de formas (`FOR*.DWG`) será SEMPRE Verde (`cor=3`)**.
