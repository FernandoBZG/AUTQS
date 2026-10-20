#!/usr/bin/env python3
"""
Script utilitário para a Skill comparar-geometria-formas.
Executa a comparação analítica e gráfica entre duas geometrias/plantas de formas no TQS.
Uso:
    python comparar.py --base "049" --pav-base "terreo"
    python comparar.py --base "049" --comp "049_TESTE" --pav-base "terreo"
    python comparar.py --base "054" --pav-base "tipo a" --pav-comp "tipo b"
"""

import sys
import os
import argparse

# Adiciona raiz do projeto AUTQS ao sys.path
raiz_projeto = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if raiz_projeto not in sys.path:
    sys.path.insert(0, raiz_projeto)

# Configura stdout e stderr para UTF-8 no Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

from src.skills.case_07_comparacao_formas.geometry_comparator import TQSGeometryComparator


def main():
    parser = argparse.ArgumentParser(description="Comparador de Geometria e Formas CAD/TQS V25")
    parser.add_argument("--base", "-b", required=True, help="Nome ou código do edifício base / anterior (ex: '049', '054')")
    parser.add_argument("--pav-base", "-pb", required=True, help="Nome do pavimento base (ex: 'terreo', '2 pavimento')")
    parser.add_argument("--comp", "-c", default=None, help="Nome ou código do edifício comparado (opcional, padrão: mesmo edifício)")
    parser.add_argument("--pav-comp", "-pc", default=None, help="Nome do pavimento comparado (opcional, padrão: mesmo pavimento)")
    parser.add_argument("--sem-dxf", action="store_true", help="Não gerar o arquivo DXF de sobreposição gráfica")
    parser.add_argument("--saida-dxf", default=None, help="Caminho de saída customizado para o DXF gerado")
    parser.add_argument("--json", action="store_true", help="Imprimir saída em formato JSON estruturado")

    args = parser.parse_args()

    comparator = TQSGeometryComparator()
    resultado = comparator.comparar_pavimentos(
        edificio_base=args.base,
        pavimento_base=args.pav_base,
        edificio_comparado=args.comp,
        pavimento_comparado=args.pav_comp,
        gerar_desenho_diff=not args.sem_dxf,
        caminho_saida_diff=args.saida_dxf
    )

    if args.json:
        import json
        print(json.dumps(resultado.para_dict(), indent=2, ensure_ascii=False))
    else:
        print(resultado.para_tabela_terminal())


if __name__ == "__main__":
    main()
