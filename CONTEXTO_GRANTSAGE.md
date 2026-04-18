# GrantSage — memória de contexto para o assistente (Cursor)

## Identidade do projeto

- **Nome do produto:** GrantSage
- **Caminho do repositório:** `~/projetos/grantsage`
- **Pacote Python (previsto):** `src/grantsage/` (nome do pacote em minúsculas: `grantsage`)
- **Papel:** copiloto técnico para **um edital/chamada por pacote de dados** — não substitui validação humana, jurídica ou institucional.

## Objetivo funcional (o que o sistema deve fazer)

Especialista em análise de proposta frente a um **corpus normativo** (edital + anexos + retificações/rerratificações + comunicados + FAQ/guias + outros oficiais + figuras quando existirem).

Três capacidades principais (três “modos” de uso):

1. **Modo 1 — Q&A sobre o edital:** responder dúvidas com **grounding** no corpus; se não houver suporte, declarar **não localizado no corpus**; evitar inferências de prazo/valor/regra não explícitos.
2. **Modo 2 — Revisão / alinhamento / gaps:** cruzar **requisitos** (obrigatórios/recomendados) com a **proposta**; listar atendido / parcial / ausente / desalinhado; priorizar por impacto (desclassificação > penalidade > competitividade).
3. **Modo 3 — Parecer / pontuação simulada:** aplicar **rubrica** do edital (critérios, pesos, escalas) de forma **auditável**; cada nota ou conclusão deve vir com **justificativa ligada a trechos** do edital e da proposta; incluir **disclaimer** de IA + necessidade de validação humana.

## Dois corpus (sempre separados)

- **Corpus A — Normativo (edital):** documentos oficiais da chamada.
- **Corpus B — Proposta (candidato):** texto da proposta do usuário.

O sistema opera fazendo **ponte A ↔ B** (recuperação + comparação estruturada), não misturando papéis conceituais.

## Formato da proposta (decisão do usuário)

- A proposta é escrita em **Google Docs** e exportada para **Markdown** (`.md`).
- Exemplo real de formato: formulário longo com **títulos**, **tabelas rótulo → conteúdo**, perguntas numeradas, seções (dados gerais, equipe, infra, orçamento), **links** para Drive/Docs/Sheets e eventualmente figuras.
- **Riscos conhecidos:** conteúdo crítico **só como URL** não é analisável sem exportar anexos para arquivos locais; **base64 gigante** no Markdown deve ser evitado (preferir `figuras/foo.png`).

## Estratégia de raciocínio (arquitetura de alto nível, acordada)

Ordem correta para análise séria (especialmente modos 2 e 3):

1. **Pré-processamento determinístico:** chunking com **overlap** nos textos longos; isso é **pipeline/código**, não “intuição” do modelo a cada pergunta.
2. **Passo de mapa da proposta:** gerar um **`proposal_outline`** (seções, lacunas, links externos sem conteúdo local, rascunhos/placeholders).
3. **Passo de esquema do edital:** manter um **`schema_edital`** (critérios, obrigatórios, prazos, desclassificações, rubrica) — primeira versão pode ser **semi-manual** (extração assistida + revisão humana).
4. **Só então** avaliação **item a item** (ou por requisito), com recuperação **restrita** aos trechos relevantes + **citações** (`chunk_id` ou equivalente).

## RAG e stack (MVP vs depois)

**MVP (primeiro edital, ~20 documentos — manter simples):**

- **Sem Vector DB** no início: `chunks.jsonl` + `embeddings.npy` (ou similar) + **top-k por similaridade** em memória costuma ser suficiente.
- **Sem LangChain/LlamaIndex/DSPy** no início: primeiro dominar **dados + retrieval + prompts + logs**.
- **UI:** **Streamlit** em `ui/`; a UI só chama funções do núcleo (`src/grantsage/`), sem duplicar lógica.

**Deixar para fase posterior (quando complexidade exigir):**

- Vector DB (Qdrant/Chroma/Weaviate), frameworks de orquestração, DSPy, validador automático “cada frase tem fonte” (difícil), UI mais pesada, OCR/visão em massa.

## Reutilização entre editais (como “trocar de projeto” sem reescrever código)

- Um **diretório por edital** sob `editais/<edital_id>/`.
- Cada pacote contém: `fontes/` (originais), `artefatos/md/` (Markdown normalizado), `artefatos/chunks/` (chunks/embeddings/meta), e um **`catalogo.yaml`** (ou `manifest.json`) listando documentos com **metadados** (tipo, data, papel na vigência).
- Template inicial sugerido: `editais/_template/` para copiar ao criar um novo edital.

## Auditoria e confiabilidade (requisitos transversais)

- Logar: **timestamp**, **versão/hash** do corpus usado, **modelo**, **lista de chunk_ids recuperados** (e idealmente trechos curtos).
- **Versionamento normativo:** nunca misturar retificação antiga com vigente sem regra explícita.
- **Conflitos no corpus:** se detectados, sinalizar explicitamente.
- **Temperatura baixa** para respostas factuais; prompts com negação explícita de alucinação.

## Saídas estruturadas

- Preferir **JSON ou Markdown padronizado** para modos 2 e 3 (facilita download na Streamlit e revisão humana).
- Campos típicos do modo 3 incluem: critério, peso, pontuação estimada, justificativa, `chunk_ids` do edital e da proposta, nível de conformidade, recomendações, disclaimer.

## Passos de implementação já planejados com o usuário (orientação manual)

- **Passo 1:** esqueleto do repo (`editais/`, `propostas/`, `src/grantsage/`, `ui/`, `prompts/`), venv, `requirements.txt` mínimo (`streamlit`, `python-dotenv`), `streamlit run ui/streamlit_app.py`, `.gitignore`, `.env.example`.
- **Passo 2 (próximo):** definir e preencher **`catalogo.yaml`** do primeiro edital (molde + ~20 entradas), ainda **sem** embeddings.

## Instruções para o assistente no Cursor

- Responder em **português**.
- Priorizar **orientação passo a passo** se o usuário estiver implementando manualmente; só escrever arquivos inteiros no workspace se ele pedir explicitamente.
- Manter escopo: **não** adicionar Vector DB/frameworks pesados até o usuário concluir o MVP.
- Sempre lembrar: **GrantSage é copiloto**; pareceres e notas são **simulações auditáveis**, não decisão oficial.

---

### Modo de trabalho com o assistente (obrigatório registrar)

- O assistente (**Auto / Composer no Cursor**) **orienta passo a passo**; o usuário **implementa manualmente** (cria pastas, arquivos, funções e commits).
- O assistente **só escreve ou altera arquivos no repositório** quando o usuário **pedir explicitamente** que ele faça isso; caso contrário, limita-se a **instruções, checklists, assinaturas de funções e revisão** do que o usuário colar ou descrever.
- O ritmo é **um passo por vez**: o usuário avisa **“passo N pronto”** (ou envia erro/dúvida) antes de avançar para o passo N+1.
