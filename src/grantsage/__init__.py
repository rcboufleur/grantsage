"""Núcleo do GrantSage - lógica compartilhada; a UI em `ui/` so consome isto."""

__version__ = "0.1.0"

from grantsage.ui_copy import APP_TITLE, APP_SUBTITLE


def get_version() -> str:
    """Retorna a versão do GrantSage."""
    return __version__
