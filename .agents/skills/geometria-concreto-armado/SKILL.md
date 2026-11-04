---
name: geometria-concreto-armado
description: >-
  Gera e atualiza a prancha executiva oficial de Geometria/Formas de Concreto Armado (GEO_<PAVIMENTO>.DWG)
  no software TQS V25 a partir do arquivo estrutural processado (FOR000x.DWG). Clona a base pura de formas,
  purga cabeçalhos provisórios do TQS, sobrepõe a moldura oficial ABNT (Nível 100), insere o Título Executivo
  (Nível 222/250) e reaplica todas as Notas Técnicas, legendas de projeto e convenções de cobrimento e cargas.
  Use quando o usuário pedir para gerar a geometria, montar prancha de forma, atualizar GEO_*.DWG ou emitir
  desenho de formas de concreto armado no TQS.
---

# Geração de Geometria Executiva de Concreto Armado (TQS CA)

Esta habilidade automatiza a montagem da prancha executiva oficial de **Geometria / Pré-Geometria de Formas** (`GEO_<PAVIMENTO>.DWG`) a partir do arquivo estrutural processado pelo Modelador Estrutural do TQS (`FOR000x.DWG`).

---

## 🎯 Quando Utilizar Esta Skill

Ative esta habilidade sempre que o usuário solicitar:
1. **"Faça a geometria do <pavimento> do <edifício>"**: Ex: Subsolo 1, Térreo, Tipo ou Cobertura em edifícios de Concreto Armado (`CA`).
2. **"Atualize a prancha de formas / GEO"**: Quando o usuário alterou o `Modelo.DWG` e reprocessou as formas, necessitando atualizar o `GEO_*.DWG` oficial mantendo moldura e notas.
3. **"Monte a geometria com a moldura e notas técnicas"**: Integrar a nova malha de vigas, pilares e lajes com a folha padrão ABNT (Moldura 180-70, Nível 100).

---

## 🏗️ Pipeline de Engenharia

```mermaid
flowchart TD
    A["Identificação do Edifício e Pavimento<br/>(Ex: 055 CA / PISO DO SUBSOLO 1)"] --> B["Localização de FOR000x.DWG e GEO_*.DWG existente"]
    B --> C["Backup Preventivo Automático<br/>(GEO_*_BKP_{timestamp}.DWG)"]
    C --> D["Coleta da Prancha de Referência:<br/>* Moldura ABNT (Nível 100)<br/>* Título Executivo (Níveis 222/250)<br/>* Notas Técnicas e Legendas (Níveis 18, 0, 41, 221)"]
    D --> E["Clonagem Estrutural Pura<br/>(FOR000x.DWG -> GEO_*.DWG)"]
    E --> F["Purga de Cabeçalho Provisório do TQS<br/>(Remoção de 'Planta PISO...' e caixas em X < 11000)"]
    F --> G["Reaplicação de Moldura, Título e Notas<br/>(Com níveis, cores e escalas preservadas)"]
    G --> H["Auditoria de Integridade:<br/>* Verificação de 100% das vigas (Nível 8)<br/>* Detecção de linhas duplicadas<br/>* Conformidade de prancha"]
```

---

## 🚀 Como Executar

### Via Python API
```python
from src.skills.case_13_geometria_ca.skill import GeometriaCASkill

skill = GeometriaCASkill()
resultado = skill.executar(
    edificio_nome="055",
    pavimento="PISO DO SUBSOLO 1",
    escala=50
)

print(f"Status: {resultado['status']}")
print(f"Arquivo gerado: {resultado['caminho_geo']}")
print(f"Vigas auditadas: {resultado['auditoria']['total_vigas']}")
```

### Validações de Qualidade Automáticas
O método `validar()` garante:
1. Existência física do arquivo `GEO_*.DWG` com tamanho válido (> 10 KB).
2. Presença íntegra da Moldura ABNT no Nível 100.
3. Fidelidade total da malha estrutural (vigas no Nível 8 e contornos no Nível 235).
4. Zero conflitos ou sobreposições espaciais entre notas técnicas ($Y \ge -2350$) e a estrutura ($Y < -2350$).
