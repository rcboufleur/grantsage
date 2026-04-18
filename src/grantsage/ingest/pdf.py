"""Conversão determinística de PDF para Markdown e extração de figuras (sem LLM)."""

from __future__ import annotations
from pathlib import Path
import fitz
from grantsage.ingest.paths import figuras_dir, md_dir


def pdf_para_md(caminho_pdf: Path, edital_id: str, nome_base: str) -> dict:
    """Extrai texto e imagens de um PDF

    Parâmetros:
    -----------
    caminho_pdf: Path
        Caminho para o arquivo PDF a ser processado.
    edital_id: str
        ID do edital.
    nome_base: str
        Nome base para os artefatos gerados.

    Retorna:
    --------
    Dicionário com chaveis úteis para o CLI, por exemplo:
    {
        "caminho_pdf": caminho_pdf,
        "edital_id": edital_id,
        "nome_base": nome_base,
    }

    Saídas:
    -------
    - ``editais/<edital_id>/artefatos/md/<nome_base>.md``
    - ``editais/<edital_id>/artefatos/md/_figuras/<nome_base>/pNNN_imgMM.<ext>``

    No Markdown, cada imagem usa caminho relatio ao ``.md``:
        ``![](_figuras/<nome_base>/nome_arquivo)``.
    """
    pdf = Path(caminho_pdf)
    if not pdf.is_file():
        raise FileNotFoundError(f"Arquivo PDF não encontrado: {pdf}")
    if pdf.suffix.lower() != ".pdf":
        raise ValueError(f"Arquivo PDF inválido: {pdf}")

    nb = nome_base.strip()
    if not nb:
        raise ValueError("nome_base não pode ser vazio.")

    dest_md = md_dir(edital_id) / f"{nb}.md"
    dest_figuras = figuras_dir(edital_id, nb)
    dest_figuras.mkdir(parents=True, exist_ok=True)

    linhas: list[str] = []
    total_imagens = 0

    with fitz.open(pdf) as doc:
        num_paginas = len(doc)
        for i in range(num_paginas):
            page = doc.load_page(i)
            n = i + 1
            linhas.append(f"## Página {n} / {num_paginas}\n\n")

            texto = (page.get_text("text") or "").strip()
            if texto:
                linhas.append(texto + "\n\n")

            for idx, info in enumerate(page.get_images(full=True), start=1):
                xref = info[0]
                data = doc.extract_image(xref)
                raw = data["image"]
                ext = (data.get("ext") or "png").lower()
                nome_img = f"p{n:03d}_img{idx:02d}.{ext}"
                caminho_img = dest_figuras / nome_img
                caminho_img.write_bytes(raw)
                total_imagens += 1
                linhas.append(f"![](_figuras/{nb}/{nome_img})\n\n")

    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_md.write_text("".join(linhas), encoding="utf-8")

    return {
        "formato": "pdf",
        "fonte": str(pdf.resolve()),
        "edital_id": edital_id,
        "nome_base": nb,
        "caminho_md": str(dest_md.resolve()),
        "caminho_figuras": str(dest_figuras.resolve()),
        "imagens": total_imagens,
        "paginas": num_paginas,
        "avisos": [],
    }
