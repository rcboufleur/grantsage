"""Conversão determinística de DOCX para Markdown e extração de figuras (sem LLM)."""

from __future__ import annotations
from pathlib import Path
import mammoth
from markdownify import markdownify as html_para_md
from grantsage.ingest.paths import figuras_dir, md_dir, garante_layout_edital

def docx_para_md(caminho_docx: Path, edital_id: str, nome_base: str) -> dict:
    """Extrai texto e imagens de um DOCX

    Parâmetros:
    -----------
    caminho_docx: Path
        Caminho para o arquivo DOCX a ser processado.
    edital_id: str
        ID do edital.
    nome_base: str
        Nome base para os artefatos gerados.

    Retorna:
    --------
    Dicionário com chaveis úteis para o CLI, por exemplo:
    {
        "caminho_docx": caminho_docx,
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
    docx = Path(caminho_docx)
    if not docx.is_file():
        raise FileNotFoundError(f"Arquivo DOCX não encontrado: {docx}")
    if docx.suffix.lower() != ".docx":
        raise ValueError(f"Arquivo DOCX inválido: {docx}")
    
    nb = nome_base.strip()
    if not nb:
        raise ValueError("nome_base não pode ser vazio.")
    garante_layout_edital(edital_id)
    
    dest_md = md_dir(edital_id) / f"{nb}.md"
    dest_figuras = figuras_dir(edital_id, nb)
    dest_figuras.mkdir(parents=True, exist_ok=True)
    
    contador = [0]

    def gravar_imagem(image) -> dict[str,str]:
        contador[0] += 1
        ext = (image.content_type.split("/")[-1] if image.content_type else "png") or "png"
        if ext == "jpeg":
            ext = "jpg"
        nome_img = f"img_{contador[0]:03d}.{ext}"
        caminho = dest_figuras / nome_img
        with image.open() as f:
            caminho.write_bytes(f.read())
        # Caminho que o HTML usará; depois no md deve bater com _figuras/{nb}/{nome_img}
        return {"src": f"_figuras/{nb}/{nome_img}"}
    
    with docx.open("rb") as f:
        resultado = mammoth.convert_to_html(
            f,
            convert_image=mammoth.images.img_element(gravar_imagem),
        )
    html = resultado.value # string HTML
    avisos = [str(m) for m in resultado.messages] # avisos do mammoth

    md = html_para_md(html, heading_style="ATX")
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_md.write_text(md.strip() + "\n", encoding="utf-8")

    return {
        "formato": "docx",
        "fonte": str(docx.resolve()),
        "edital_id": edital_id,
        "nome_base": nb,
        "caminho_md": str(dest_md.resolve()),
        "caminho_figuras": str(dest_figuras.resolve()),
        "imagens": contador[0],
        "paginas": None,
        "avisos": avisos,
    }