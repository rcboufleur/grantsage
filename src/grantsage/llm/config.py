"""Resolução de configuração de LLM por perfil (UI -> .env perfil -> .env default)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

from dotenv import load_dotenv

from grantsage.llm.cadastro import obter_override_perfil


@dataclass(frozen=True)
class PerfilLLMConfig:
    """Configuração final para um perfil de uso de LLM.

    Campos:
    -------
    perfil:
        Nome lógico da atividade (ex.: chat, visao).
    model:
        Modelo LiteLLM a usar (ex.: "gpt-4o-mini", "ollama/llama3.2-vision").
    api_key:
        Chave API opcional.
    api_base:
        Base URL opcional (gateway OpenAI-compatible, servidor local etc.).
    temperature:
        Temperatura padrão para geração.
    max_tokens:
        Limite de tokens de saída (None = padrão do provider).
    timeout:
        Timeout em segundos para chamada remota (None = padrão da biblioteca).
    """

    perfil: str
    model: str
    api_key: str | None
    api_base: str | None
    temperature: float
    max_tokens: int | None
    timeout: float | None


def _env_nome(perfil: str, campo: str) -> str:
    return f"GRANTSAGE_LLM_{perfil.upper()}_{campo}"


def _env_default(campo: str) -> str:
    return f"GRANTSAGE_LLM_DEFAULT_{campo}"


def _str_ou_none(valor: Any) -> str | None:
    if valor is None:
        return None
    s = str(valor).strip()
    return s or None


def _parse_float(nome: str, valor: Any, padrao: float) -> float:
    if valor is None or str(valor).strip() == "":
        return padrao
    try:
        return float(valor)
    except ValueError as e:
        raise ValueError(f"{nome} inválido: {valor!r}") from e


def _parse_int_ou_none(nome: str, valor: Any) -> int | None:
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return int(valor)
    except ValueError as e:
        raise ValueError(f"{nome} inválido: {valor!r}") from e


def _parse_float_ou_none(nome: str, valor: Any) -> float | None:
    if valor is None or str(valor).strip() == "":
        return None
    try:
        return float(valor)
    except ValueError as e:
        raise ValueError(f"{nome} inválido: {valor!r}") from e


def _resolver_campo(
    perfil: str,
    campo: str,
    *,
    override_ui: dict[str, Any],
    fallback_legacy: str | None = None,
) -> str | None:
    # Prioridade:
    # 1) override de UI em memória
    # 2) env específico do perfil: GRANTSAGE_LLM_{PERFIL}_{CAMPO}
    # 3) env default: GRANTSAGE_LLM_DEFAULT_{CAMPO}
    # 4) env legado (opcional)
    if campo.lower() in override_ui:
        return _str_ou_none(override_ui[campo.lower()])
    if campo.upper() in override_ui:
        return _str_ou_none(override_ui[campo.upper()])

    v_perfil = _str_ou_none(os.getenv(_env_nome(perfil, campo), ""))
    if v_perfil:
        return v_perfil

    v_default = _str_ou_none(os.getenv(_env_default(campo), ""))
    if v_default:
        return v_default

    if fallback_legacy:
        return _str_ou_none(os.getenv(fallback_legacy, ""))

    return None


@lru_cache(maxsize=32)
def carregar_config_perfil(perfil: str) -> PerfilLLMConfig:
    """Carrega configuração final de um perfil.

    Parâmetros:
    -----------
    perfil: str
        Nome lógico do perfil. Ex.: "chat", "visao", "embeddings".

    Retorna:
    --------
    `PerfilLLMConfig` com valores resolvidos.
    """
    load_dotenv()

    p = perfil.strip().lower()
    if not p:
        raise ValueError("perfil não pode ser vazio.")

    ov = obter_override_perfil(p)

    model = _resolver_campo(
        p,
        "MODEL",
        override_ui=ov,
        fallback_legacy="GRANTSAGE_LLM_MODEL" if p == "chat" else None,
    )
    if not model:
        raise ValueError(
            f"Modelo não configurado para perfil '{p}'. "
            f"Defina {_env_nome(p, 'MODEL')} (ou override de UI)."
        )

    api_key = _resolver_campo(
        p,
        "API_KEY",
        override_ui=ov,
        fallback_legacy="GRANTSAGE_LLM_API_KEY",
    )
    api_base = _resolver_campo(
        p,
        "API_BASE",
        override_ui=ov,
        fallback_legacy="GRANTSAGE_LLM_API_BASE",
    )

    temp_raw = _resolver_campo(
        p,
        "TEMPERATURE",
        override_ui=ov,
        fallback_legacy="GRANTSAGE_LLM_TEMPERATURE",
    )
    max_raw = _resolver_campo(
        p,
        "MAX_TOKENS",
        override_ui=ov,
        fallback_legacy="GRANTSAGE_LLM_MAX_TOKENS",
    )
    timeout_raw = _resolver_campo(
        p,
        "TIMEOUT",
        override_ui=ov,
    )

    temperature = _parse_float(f"{p}.temperature", temp_raw, 0.2)
    max_tokens = _parse_int_ou_none(f"{p}.max_tokens", max_raw)
    timeout = _parse_float_ou_none(f"{p}.timeout", timeout_raw)

    return PerfilLLMConfig(
        perfil=p,
        model=model,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )


def limpar_cache_config_llm() -> None:
    """Limpa cache de configuração (útil após editar .env ou overrides da UI)."""
    carregar_config_perfil.cache_clear()
