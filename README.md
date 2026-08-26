# RAG

Primeira versão do repositório: um pipeline de RAG que ingere documentos internos, busca com técnicas de retrieval de produto e só responde com frases do corpus.

Roadmap: [MELHORIAS.md](MELHORIAS.md)

## Técnicas (o que torna isto um produto)

Não é “embeda o PDF e pergunta ao GPT”. A cadeia abaixo é o que um RAG interno precisa para ir a produção: documento estruturado, busca que não mistura trimestre, resposta citada e recusa quando a evidência não fecha.

| Camada | Técnica | Por que importa |
|---|---|---|
| Ingestão | Conversão para Markdown (`.docx`, `.pdf`, `.txt`, `.html`, `.csv`) com confirmação antes de indexar | O corpus é versionável e auditável; nada entra no índice sem alguém aceitar |
| Chunking | Seção Markdown + **explode de tabela** (linha ou célula por período: Q1, FY, mês) | KPI em tabela deixa de ser um blob; “Q1 2026” acerta a célula, não a hierarquia de clientes |
| Índice | TF-IDF (espaço do próprio corpus) + **BM25 Okapi** | Busca lexical forte em política, SOP e número — sem depender de API de embedding |
| Fusão | **Hybrid search** com **Reciprocal Rank Fusion (RRF)** | Combina overlap de termo (BM25) e perfil TF-IDF; um canal sozinho falha em pergunta curta ou em sinônimo |
| Query | Reescrita + **quadro da pergunta** (quantidade, trimestre, pessoas, definição) + grafo de coocorrência | “Quanto na P1 de 2026” não vira incidente; “funcionários” acha `headcount` |
| Ranking | Rerank (overlap, cobertura, frase) + alinhamento de **período/ano** + **MMR** | Sobe o trecho do trimestre certo e não devolve a mesma frase três vezes |
| Qualidade | **Quality gate** na recuperação, com retry da query | Se a cobertura for fraca, tenta de novo antes de redigir |
| Resposta | Extração de spans (não geração) + verificação de fundamentação | A resposta é citável; se o quadro não fecha, **não confirma** |
| Agente | Loop **think → act → observe** (`rewrite_and_retrieve` → `draft_answer` → `verify_answer`) | Superfície de produto: chat com política fixa, não um prompt solto |
| Integração | Tools com **JSON Schema** (caminho MCP) + registry de agentes | Dá para plugar IDE, outro serviço ou um segundo agente sem reescrever a busca |

Contrato desta versão: **extrativo**. Não há LLM gerando o texto final. Isso é restrição de produto (confiança, custo, dado interno), não falta de feature.

## O que esta versão faz

1. **Ingestão** — arquivos → chunks → vetores TF-IDF + índice BM25.
2. **Query rewrite** — reescreve a pergunta antes do índice.
3. **Hybrid search** — TF-IDF + BM25, fundidos com RRF.
4. **Rerank** — overlap, cobertura, frase, período, MMR.
5. **Quality gate** — trechos fracos → nova query.
6. **Agente** — três tools; só entrega se busca e verificação passarem.
7. **MCP / multiagentes** — schema das tools; `AgentRegistry` + `MessageBus`.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Dependências: numpy, pypdf, python-docx, python-dotenv, rich.

## Uso

```bash
python -m rag ingest
python -m rag ask "quantos dias de férias a Aurora Tech dá?"
python -m rag chat
python -m rag tools
```

`ingest` sem argumento lê `data/documents`.

## Adicionar arquivos ao RAG

Converte `.docx`, `.txt`, `.pdf`, `.html`, `.csv` e `.md` para Markdown no corpus. Só atualiza o índice se você confirmar.

```bash
python -m rag add caminho\manual.docx
python -m rag add data\inbox\reembolso.txt
```

A CLI pergunta: `Incluir N arquivos no índice RAG agora? [s/N]`

- `--ingest` — inclui sem perguntar
- `--no-ingest` — só gera os `.md`
- `--force` — sobrescreve um `.md` que já exista
- `--out pasta` — destino dos markdowns (padrão: `data/documents`)

No chat:

```
/add caminho\manual.docx
```

## Agente

1. `rewrite_and_retrieve` — reescreve a query, hybrid + rerank, mede qualidade (com retry).
2. `draft_answer` — monta a resposta com frases dos trechos.
3. `verify_answer` — se não estiver fundamentado, não confirma.

## Layout

```
rag/
  agent/
  retrieval/
  embeddings/
  store/
  ingest/
  mcp_ready/
  multiagent/
data/documents/
data/inbox/
```
