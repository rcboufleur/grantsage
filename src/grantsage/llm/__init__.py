"""Integração com modelos de IA (LLM)."""

from grantsage.llm.cadastro import (
    cadastrar_config_perfil,
    limpar_config_perfil,
    listar_config_perfil,
    listar_perfis_cadastrados,
)

from grantsage.llm.cliente import (
    descrever_imagem,
    gerar_texto,
    gerar_texto_simples,
)

from grantsage.llm.config import (
    PerfilLLMConfig,
    carregar_config_perfil,
    limpar_cache_config_llm,
)

__all__ = [
    "PerfilLLMConfig",
    "carregar_config_perfil",
    "limpar_cache_config_llm",
    "cadastrar_config_perfil",
    "limpar_config_perfil",
    "listar_config_perfil",
    "listar_perfis_cadastrados",
    "descrever_imagem",
    "gerar_texto",
    "gerar_texto_simples",
]
