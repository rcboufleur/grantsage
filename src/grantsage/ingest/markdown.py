"""Cópia determinística de Markdown de ``fontes/`` para ``artefatos/md/`` (sem LLM)."""

from __future__ import annotations

import re
from pathlib import Path

from grantsage.ingest.paths import figuras_dir, garante_layout_edital, md_dir

# ``![](...)`` cujo destino não é URL remota típica (MVP não copia ficheiros locais).
_RE_IMG_LOCAL = re.compile(
    r"!\[[^\]]*\]\(\s*(?!https?://|data:)([^)]+)\s*\)",
    re.IGNORECASE,
)


def md_fonte_para_md(caminho_md_fonte: Path, edital_id: str, nome_base: str) -> dict:
    """Copia um Markdown já em UTF-8 de ``fontes/`` para ``artefatos/md/``.

    Parâmetros:
    -----------
    caminho_md_fonte: Path
        Caminho para o arquivo Markdown em ``fontes/`` a ser processado.
    edital_id: str
        ID do edital.
    nome_base: str
        Nome base para os artefatos gerados.

    Retorna:
    --------
    Dicionário com chaveis úteis para o CLI, por exemplo:
    {
        "caminho_md_fonte": caminho_md_fonte,
        "edital_id": edital_id,
        "nome_base": nome_base,
    }

    Saídas:
    -------
    - ``editais/<edital_id>/artefatos/md/<nome_base>.md``
    - ``editais/<edital_id>/artefatos/md/_figuras/<nome_base>/`` (pasta criada vazia; MVP sem imagens)

    Limitação do MVP: não copia imagens referenciadas por caminhos locais em ``fontes/``;
    se existirem, um aviso é acrescentado em ``avisos``.
    """
    src = Path(caminho_md_fonte)
    if not src.is_file():
        raise FileNotFoundError(f"Arquivo Markdown não encontrado: {src}")
    if src.suffix.lower() != ".md":
        raise ValueError(f"Arquivo Markdown inválido: {src}")

    nb = nome_base.strip()
    if not nb:
        raise ValueError("nome_base não pode ser vazio.")
    garante_layout_edital(edital_id)

    dest_md = md_dir(edital_id) / f"{nb}.md"
    dest_figuras = figuras_dir(edital_id, nb)
    dest_figuras.mkdir(parents=True, exist_ok=True)

    texto = src.read_text(encoding="utf-8")
    avisos: list[str] = []
    if _RE_IMG_LOCAL.search(texto):
        avisos.append(
            "Markdown fonte contém imagens com caminho local; o MVP não copia ficheiros — use PDF/DOCX/ODT ou normalize sem imagens locais."
        )

    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_md.write_text(texto.strip() + "\n", encoding="utf-8")

    return {
        "formato": "md",
        "fonte": str(src.resolve()),
        "edital_id": edital_id,
        "nome_base": nb,
        "caminho_md": str(dest_md.resolve()),
        "caminho_figuras": str(dest_figuras.resolve()),
        "imagens": 0,
        "paginas": None,
        "avisos": avisos,
    }
