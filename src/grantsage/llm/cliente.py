"""Cliente de alto nível para geração de texto e descrição de imagens via LiteLLM."""

from __future__ import annotations

import base64
import mimetypes
from pathlib import Path
from typing import Any

import litellm

from grantsage.llm.config import PerfilLLMConfig, carregar_config_perfil


def _extrair_texto_resposta(response: Any) -> str:
    """Extrai conteúdo textual da primeira escolha da resposta LiteLLM."""
    if not getattr(response, "choices", None):
        raise RuntimeError("Resposta do modelo sem 'choices'.")

    choice = response.choices[0]
    msg = choice.message
    content = (
        msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
    )

    if content is None:
        raise RuntimeError("Resposta do modelo sem conteúdo.")

    if isinstance(content, str):
        texto = content.strip()
        if not texto:
            raise RuntimeError("Resposta textual vazia.")
        return texto

    if isinstance(content, list):
        partes: list[str] = []
        for p in content:
            if isinstance(p, dict) and p.get("type") == "text":
                partes.append(str(p.get("text", "")))
            elif isinstance(p, str):
                partes.append(p)
        texto = "".join(partes).strip()
        if not texto:
            raise RuntimeError("Resposta multimodal sem texto.")
        return texto

    texto = str(content).strip()
    if not texto:
        raise RuntimeError("Resposta com conteúdo não textual vazio.")
    return texto


def _kwargs_base(
    cfg: PerfilLLMConfig,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float | None = None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": cfg.model,
        "temperature": cfg.temperature if temperature is None else float(temperature),
    }
    if cfg.api_key:
        kwargs["api_key"] = cfg.api_key
    if cfg.api_base:
        kwargs["api_base"] = cfg.api_base

    mt = cfg.max_tokens if max_tokens is None else max_tokens
    if mt is not None:
        kwargs["max_tokens"] = int(mt)

    to = cfg.timeout if timeout is None else timeout
    if to is not None:
        kwargs["timeout"] = float(to)

    return kwargs


def gerar_texto(
    mensagens: list[dict[str, Any]],
    *,
    perfil: str = "chat",
    config: PerfilLLMConfig | None = None,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    timeout: float | None = None,
) -> str:
    """Executa chat completion e devolve o texto da primeira resposta.

    Parâmetros:
    -----------
    mensagens:
        Lista no formato chat (roles + conteúdo) compatível com LiteLLM/OpenAI.
    perfil:
        Perfil de configuração (default: "chat").
    config:
        Configuração já resolvida; se `None`, usa `carregar_config_perfil(perfil)`.
    model, temperature, max_tokens, timeout:
        Sobrescritas pontuais para esta chamada.
    """
    cfg = config if config is not None else carregar_config_perfil(perfil)
    if model:
        cfg = PerfilLLMConfig(
            perfil=cfg.perfil,
            model=model.strip(),
            api_key=cfg.api_key,
            api_base=cfg.api_base,
            temperature=cfg.temperature,
            max_tokens=cfg.max_tokens,
            timeout=cfg.timeout,
        )

    kwargs = _kwargs_base(
        cfg,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    kwargs["messages"] = mensagens

    response = litellm.completion(**kwargs)
    return _extrair_texto_resposta(response)


def gerar_texto_simples(
    prompt: str,
    *,
    perfil: str = "chat",
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Atalho para um prompt único de texto."""
    mensagens: list[dict[str, Any]] = []
    if system_prompt:
        mensagens.append({"role": "system", "content": system_prompt})
    mensagens.append({"role": "user", "content": prompt})
    return gerar_texto(
        mensagens,
        perfil=perfil,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _imagem_para_data_url(caminho_imagem: Path) -> str:
    """Converte imagem local em data URL para envio multimodal."""
    if not caminho_imagem.is_file():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho_imagem}")

    mime, _ = mimetypes.guess_type(str(caminho_imagem))
    mime = mime or "image/png"
    raw = caminho_imagem.read_bytes()
    b64 = base64.b64encode(raw).decode("ascii")
    return f"data:{mime};base64,{b64}"


def descrever_imagem(
    caminho_ou_url: str | Path,
    *,
    instrucoes: str,
    perfil: str = "visao",
    system_prompt: str | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Gera descrição textual de uma imagem usando perfil de visão.

    Parâmetros:
    -----------
    caminho_ou_url:
        URL da imagem ou caminho local.
    instrucoes:
        Pedido textual (ex.: "descreva tabela, títulos e números").
    perfil:
        Perfil de visão (default: "visao").
    """
    if isinstance(caminho_ou_url, Path):
        image_url = _imagem_para_data_url(caminho_ou_url)
    else:
        s = str(caminho_ou_url).strip()
        if not s:
            raise ValueError("caminho_ou_url não pode ser vazio.")
        if s.startswith("http://") or s.startswith("https://") or s.startswith("data:"):
            image_url = s
        else:
            image_url = _imagem_para_data_url(Path(s))

    mensagens: list[dict[str, Any]] = []
    if system_prompt:
        mensagens.append({"role": "system", "content": system_prompt})

    mensagens.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instrucoes},
                {"type": "image_url", "image_url": {"url": image_url}},
            ],
        }
    )

    return gerar_texto(
        mensagens,
        perfil=perfil,
        temperature=temperature,
        max_tokens=max_tokens,
    )
