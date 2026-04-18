"""Conversão ODT/ODS → Markdown via Pandoc (determinístico, sem LLM)."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from grantsage.ingest.paths import figuras_dir, garante_layout_edital, md_dir

_EXT_IMAGEM = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".tif",
    ".tiff",
}


def _contar_imagens_em(pasta: Path) -> int:
    if not pasta.is_dir():
        return 0
    n = 0
    for p in pasta.rglob("*"):
        if p.is_file() and p.suffix.lower() in _EXT_IMAGEM:
            n += 1
    return n


def _avisos_de_subprocess(completed: subprocess.CompletedProcess[str]) -> list[str]:
    avisos: list[str] = []
    if completed.stderr and completed.stderr.strip():
        avisos.extend(
            line.strip() for line in completed.stderr.splitlines() if line.strip()
        )
    return avisos


def _pandoc_odf_para_md(
    caminho: Path,
    edital_id: str,
    nome_base: str,
    formato: str,
) -> dict:
    """Converte ODT ou ODS com Pandoc; ``formato`` é ``odt`` ou ``ods`` (formato de leitura do Pandoc)."""
    doc = Path(caminho)
    if not doc.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {doc}")

    suf = doc.suffix.lower()
    if formato == "odt" and suf != ".odt":
        raise ValueError(f"Esperado .odt, obtido: {doc.suffix!r}")
    if formato == "ods" and suf != ".ods":
        raise ValueError(f"Esperado .ods, obtido: {doc.suffix!r}")

    nb = nome_base.strip()
    if not nb:
        raise ValueError("nome_base não pode ser vazio.")

    if not shutil.which("pandoc"):
        raise RuntimeError(
            "Pandoc não está no PATH. Instale (ex.: `sudo apt install pandoc` no WSL) "
            "e confira com `pandoc --version`."
        )

    garante_layout_edital(edital_id)

    dest_md = md_dir(edital_id) / f"{nb}.md"
    dest_fig = figuras_dir(edital_id, nb)
    # ODT/ODS guardam ``media/...`` dentro do ZIP. O Pandoc procura esses
    # caminhos no disco; sem ``--resource-path`` apontando para o pacote
    # descompactado, ocorre "Could not fetch resource media/...".
    dest_md.parent.mkdir(parents=True, exist_ok=True)
    dest_fig.parent.mkdir(parents=True, exist_ok=True)
    if dest_fig.exists():
        shutil.rmtree(dest_fig)

    sep = ";" if os.name == "nt" else ":"
    with tempfile.TemporaryDirectory(prefix="grantsage_odf_") as tmp:
        unpacked = Path(tmp) / "unpacked"
        try:
            with zipfile.ZipFile(doc, "r") as zf:
                zf.extractall(unpacked)
        except zipfile.BadZipFile as e:
            raise ValueError(f"Arquivo ZIP inválido ({formato.upper()}): {doc}") from e

        resource_path = sep.join([str(unpacked.resolve()), str(doc.parent.resolve())])

        cmd = [
            "pandoc",
            str(doc.resolve()),
            "-f",
            formato,
            "-t",
            "markdown",
            "--resource-path",
            resource_path,
            f"--extract-media={dest_fig.resolve()}",
            "-o",
            str(dest_md.resolve()),
        ]

        try:
            proc = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=600,
                cwd=str(doc.parent),
            )
        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip() if e.stderr else str(e)
            raise RuntimeError(f"Pandoc falhou ({formato}): {msg}") from e
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"Tempo máximo do Pandoc esgotado ({formato}).") from e

    avisos = _avisos_de_subprocess(proc)
    num_imagens = _contar_imagens_em(dest_fig)

    return {
        "formato": formato,
        "fonte": str(doc.resolve()),
        "edital_id": edital_id,
        "nome_base": nb,
        "caminho_md": str(dest_md.resolve()),
        "caminho_figuras": str(dest_fig.resolve()),
        "imagens": num_imagens,
        "paginas": None,
        "avisos": avisos,
    }


def odt_para_md(caminho_odt: Path, edital_id: str, nome_base: str) -> dict:
    """Converte OpenDocument Text (.odt) para Markdown (Pandoc)."""
    return _pandoc_odf_para_md(Path(caminho_odt), edital_id, nome_base, "odt")


def ods_para_md(caminho_ods: Path, edital_id: str, nome_base: str) -> dict:
    """Converte OpenDocument Spreadsheet (.ods) para Markdown (Pandoc).

    A qualidade depende do Pandoc e da complexidade da planilha; em caso de falha,
    confira ``pandoc --list-input-formats`` e a versão instalada.
    """
    return _pandoc_odf_para_md(Path(caminho_ods), edital_id, nome_base, "ods")
