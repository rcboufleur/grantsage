"""Cadastro em memória de configurações de LLM.

Este módulo não persiste em disco por enquanto. A ideia é:
- UI cadastra/edita configurações por perfil em runtime
- resolução final usa: override da UI -> .env do perfil -> .env default.
"""

from __future__ import annotations
from copy import deepcopy
from typing import Any

# Estrutura: {"chat": {"model": "...", "api_key": "...", ...}, "visao": {...}}
_OVERRIDES_UI: dict[str, dict[str, Any]] = {}


def _invalidar_cache_config() -> None:
    from grantsage.llm.config import limpar_cache_config_llm

    limpar_cache_config_llm()


def cadastrar_config_perfil(perfil: str, **campos: Any) -> None:
    """Cadastra/atualiza configurações de um perfil.

    Parâmetros:
    -----------
    perfil: str
        Nome lógico do perfil, ex. "chat", "visao", etc.
    **campos: Any
        Campos opcionais como model, api_key, etc.
    """
    p = perfil.strip().lower()
    if not p:
        raise ValueError("perfil não pode ser vazio")
    atual = _OVERRIDES_UI.get(p, {})
    atual.update(campos)
    _OVERRIDES_UI[p] = atual
    _invalidar_cache_config()


def limpar_config_perfil(perfil: str) -> None:
    """Limpa configurações de um perfil."""
    p = perfil.strip().lower()
    if not p:
        raise ValueError("perfil não pode ser vazio")
    _OVERRIDES_UI.pop(p, None)
    _invalidar_cache_config()


def obter_override_perfil(perfil: str) -> dict[str, Any]:
    """Retorna cópia do override de um perfil (ou dict vazio)"""
    p = perfil.strip().lower()
    return deepcopy(_OVERRIDES_UI.get(p, {}))


def listar_config_perfil(perfil: str) -> dict[str, Any]:
    """Retorna cópia da configuração em memória do perfil (vazio se não cadastrado)."""
    return obter_override_perfil(perfil)


def listar_perfis_cadastrados() -> list[str]:
    """Retorna lista de perfis cadastrados."""
    return sorted(_OVERRIDES_UI.keys())
