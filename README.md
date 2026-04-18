# GrantSage

Copiloto técnico para edital e proposta (MVP).

## Instalação (Python)

Na raiz do repositório, com ambiente virtual ativado:

```bash
python3 -m pip install -e .
```

## Conversão ODT / ODS

A ingestão de **OpenDocument** (`.odt` e `.ods`) usa o **Pandoc** como programa externo. É preciso ter o executável `pandoc` disponível no **PATH** do sistema (instalar o Pandoc não é feito só com `pip install` das dependências principais do projeto).

Exemplos:

- **Ubuntu / WSL:** `sudo apt install pandoc`
- Confirme com: `pandoc --version`

Sem o Pandoc instalado, PDF e DOCX continuam funcionando com as dependências Python do `pyproject.toml`; apenas a conversão ODT/ODS falhará até o binário existir no ambiente.
