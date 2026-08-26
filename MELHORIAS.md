# Melhorias e próximas versões

O que **já** está no código (híbrido TF-IDF+BM25, RRF, explode de tabela, quadro da pergunta, quality gate, agente extrativo, schema MCP) está no [README](README.md#técnicas-o-que-torna-isto-um-produto). Este arquivo é só o que ainda falta para a próxima versão.

## Ingestão

- **Ingest incremental.** Hoje o `ingest` reconstrói o índice inteiro. Passar a atualizar só arquivos novos ou alterados.
- **Caminhos relativos no índice.** Os chunks gravam path absoluto da máquina; quebra ao clonar o repo. Gravar relativo a `data/documents`.
- **Watcher da inbox.** Detectar arquivo novo em `data/inbox`, converter para `.md` e perguntar se entra no índice.
- **Tabelas em PDF/DOCX.** O chunker já explode tabela Markdown por célula/período. Falta preservar tabela na conversão a partir de PDF e Word, não só virar parágrafo.
- **Metadados na ingestão.** Data do documento, owner, classificação e vigência como campos de filtro na busca (não só texto).

## Busca e qualidade

- **Filtro por período e fonte.** Pergunta “Q1 2025” já empurra o rerank; ainda não dá para restringir a um arquivo ou a um intervalo de datas na CLI.
- **Conjunto de regressão.** Script com perguntas fixas (`Meta de 2025?`, `Faturamento na Q1 de 2026?`, `Quantas pessoas trabalham na Aurora`) e a frase/fonte esperada. Rodar depois de cada mudança no chunker ou no rewriter.
- **Cobertura de termos mais honesta.** O quality gate ainda mistura termo da pergunta com termo expandido; avaliar só o que o usuário disse.
- **Embeddings densos (opcional).** TF-IDF resolve o corpus atual. Quando o volume crescer ou a pergunta for semântica demais (“risco de caixa”), plugar um vetor local sem tirar o BM25.

## Agente

- **Memória que muda a busca.** O histórico existe, mas quase não entra na query da próxima pergunta. Usar as últimas falas para resolver “e no ano anterior?”.
- **Recusa mais clara.** Separar “não achei no índice” de “achei trecho, mas não fecha o período/quantidade”.
- **Citações no chat.** Mostrar arquivo + seção + score sem precisar de `--trace`.
- **Mais de um agente de verdade.** `AgentRegistry` e `MessageBus` são esqueleto. Um agente de ingestão e um de chat, com mensagem entre eles, só vale quando o ingest incremental existir.

## MCP e integração

- **Servidor MCP.** `tools_to_mcp` só serializa schema. Falta processar JSON-RPC (stdio ou HTTP) para o Cursor/outro cliente chamar `rewrite_and_retrieve` de fora.
- **CLI `tools` alinhada ao schema publicado.** Qualquer campo novo na tool precisa aparecer no dump MCP no mesmo commit.

## Produto

- **UI mínima.** Tela com pergunta, resposta, fontes e botão de ingest da inbox. A CLI continua sendo o caminho principal.
- **`.env.example` versionado.** Template sem segredo; `.env` local continua fora do git.
- **Testes unitários.** Chunker de tabela, `parse_frame` (Q1 vs incidente P1), explode de célula por trimestre.

## Fora de escopo por enquanto

- LLM na geração da resposta (o contrato desta versão é extrativo).
- API paga de embedding.
- Auth multi-tenant em produção.

Quando um item acima entrar, atualizar este arquivo: mover para “feito” com a data e o que mudou na CLI.
