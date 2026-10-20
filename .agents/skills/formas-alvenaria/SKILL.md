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

Esta habilidade transforma o desenho bruto de alvenaria estrutural do TQS Alvest (`DesFiad1.DWG`) em uma prancha executiva de pré-formas completa e normatizada.

---

## 🎯 Regras Obrigatórias de Projeto

1. **Base da Planta**: A base geométrica deve ser **sempre** o `DesFiad1.DWG` do pavimento correspondente.
2. **Contorno de Lajes Externas e Sacadas**: Devem ser desenhadas no **Nível 237** com cor ciano/magenta em todo o perímetro do edifício.
3. **Vãos e Aberturas**: Mapear `$BLVAO` para posicionar cotas modulares (portas no nível 251, janelas no nível 252).
4. **Purga de Poluição**: Remover blocos de ferro vertical (`$PFERV`), cotas numéricas internas excessivas e tags brutas.
5. **Moldura e Documentação**: Incluir resumo de materiais (LISTMELV), bloco de corte esquemático e carimbo técnico.

---

## 🚀 Como Invocar via Python ou Chat

```python
from src.skills.case_03_formas_alvenaria.skill import FormasAlvenariaSkill

skill = FormasAlvenariaSkill()
resultado = skill.executar(
    edificio_nome="054",
    pavimento="TIPO A",
    escala=50
)
```
