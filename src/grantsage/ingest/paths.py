"""Caminhos do pacote de edital e normalização de nome (pathlib)."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def repo_root() -> Path:
    """Devolve a raiz do repositório GrantSage.

    Retornat `RuntimeError` se não encontrar o diretório `grantsage/`
    """
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    raise RuntimeError("Não foi possível encontrar a raiz do repositório GrantSage.")


def edital_root(edital_id: str) -> Path:
    """Devolve a raiz do diretório do edital."""
    eid = edital_id.strip()
    if not eid:
        raise ValueError("O ID do edital não pode ser vazio.")
    return repo_root() / "editais" / eid


def fontes_dir(edital_id: str) -> Path:
    """Documentos originais (PDF, DOCX, etc.) do edital."""
    return edital_root(edital_id) / "fontes"


def md_dir(edital_id: str) -> Path:
    """Markdown normalizado do edital."""
    return edital_root(edital_id) / "artefatos" / "md"


def figuras_dir(edital_id: str, nome_base: str) -> Path:
    """Pasta de figuras extraídas do edital."""
    nb = nome_base.strip()
    if not nb:
        raise ValueError("nome_base não pode ser vazio.")
    return md_dir(edital_id) / "_figuras" / nb


def padronizar_nome_base(nome_arquivo: str) -> str:
    """Nome estável para saídas, a partir do nome do arquvivo em `fontes/`."""
    stem = Path(nome_arquivo).stem  # obtem o nome do arquivo sem a extensao
    s = unicodedata.normalize("NFKD", stem)  # normaliza o nome do arquivo
    s = s.encode("ascii", "ignore").decode("ascii")  # remove caracteres nao ascii
    s = s.lower().strip()  # converte para minusculo e remove espaços extras
    s = re.sub(r"[\s]+", "_", s)  # substitui espaços por underscores
    s = re.sub(
        r"[^a-z0-9_]+", "", s
    )  # remove caracteres nao alfanumericos e nao underscore
    s = re.sub(r"_+", "_", s).strip("_")  # remove underscores extras
    if not s:
        raise ValueError(f"{nome_arquivo} inválido ou não pôde ser padronizado.")
    return s


def garante_layout_edital(edital_id: str) -> None:
    """Cria pastas do edital se ainda não existirem.

    Cria:
    - `editais/<edital_id>/fontes/`
    - `editais/<edital_id>/artefatos/md/`
    - `editais/<edital_id>/artefatos/md/_figuras/`
    - `editais/<edital_id>/artefatos/chunks/`
    """
    fontes_dir(edital_id).mkdir(parents=True, exist_ok=True)
    md_dir(edital_id).mkdir(parents=True, exist_ok=True)
    (md_dir(edital_id) / "_figuras").mkdir(parents=True, exist_ok=True)
    (edital_root(edital_id) / "artefatos" / "chunks").mkdir(parents=True, exist_ok=True)
    return None
