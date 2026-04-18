"""Interface de linha de comando para a ingestão de editais."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

from grantsage.ingest.pdf import pdf_para_md
from grantsage.ingest.docx import docx_para_md
from grantsage.ingest.opendocument import odt_para_md, ods_para_md
from grantsage.ingest.markdown import md_fonte_para_md
from grantsage.ingest.paths import (
    fontes_dir,
    garante_layout_edital,
    padronizar_nome_base,
)

_CONVERSORES = {
    "pdf": pdf_para_md,
    "docx": docx_para_md,
    "odt": odt_para_md,
    "ods": ods_para_md,
    "md": md_fonte_para_md,
}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Ingestão: fontes/ -> artefatos/md")
    p.add_argument("edital_id", help="ID do pacote (editais/<id>/)")
    p.add_argument(
        "--dry-run", action="store_true", help="Não processar, apenas simular"
    )
    args = p.parse_args(argv)
    eid = args.edital_id.strip()
    if not eid:
        p.error("edital_id vazio")

    fontes = fontes_dir(eid)
    if not fontes.is_dir():
        print(f"Erro: pasta de fontes não encontrada: {fontes}", file=sys.stderr)
        return 1

    garante_layout_edital(eid)
    linhas: list[dict] = []
    erros = 0

    for f in sorted(fontes.iterdir()):
        if not f.is_file():
            continue
        conv = _CONVERSORES.get(f.suffix.lower().lstrip("."))
        if conv is None:
            linhas.append(
                {
                    "arquivo": f.name,
                    "ignorado": True,
                    "motivo": f.suffix or "sem extensão",
                }
            )
            continue
        nb = padronizar_nome_base(f.name)
        if args.dry_run:
            linhas.append({"arquivo": f.name, "nome_base": nb})
            continue
        try:
            linhas.append({"arquivo": f.name, "nome_base": nb, **conv(f, eid, nb)})
        except Exception as e:
            erros += 1
            linhas.append({"arquivo": f.name, "erro": str(e)})

    print(json.dumps(linhas, ensure_ascii=False, indent=2))
    return 1 if erros else 0
