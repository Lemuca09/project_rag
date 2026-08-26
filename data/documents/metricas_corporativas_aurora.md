# Métricas corporativas Aurora Tech — FY2025 e rolling 12 meses até jun/2026

**Documento:** FIN-KPI-009  
**Emissão:** 10/07/2026  
**Owner:** Controladoria + CFO  
**Fonte:** ERP TOTVS + Snowflake `analytics.corp`  
**Classificação:** interno restrito — diretoria

Consolida indicadores da companhia. Não substitui o relatório de Engenharia Q2 (custos de nuvem detalhados lá) nem o orçamento ORC-2026-118 (preço de um cliente).

## 1. Identificação

Aurora Tech Serviços de Software Ltda.  
CNPJ 23.901.448/0001-77  
Sede: Av. das Nações Unidas 14.401, São Paulo/SP  
Fundação: 2017. Produtos: Helios (RH), Atlas (dados internos), Nimbus (API B2B).

## 2. Receita e lucratividade

| Indicador | FY2024 | FY2025 | R12 até jun/2026 |
|---|---|---|---|
| Receita bruta | R$ 41,2 mi | R$ 58,7 mi | R$ 64,1 mi |
| Receita líquida | R$ 36,8 mi | R$ 52,4 mi | R$ 57,2 mi |
| ARR (fim do período) | R$ 39,5 mi | R$ 55,0 mi | R$ 61,8 mi |
| NRR (net revenue retention) | 108% | 114% | 116% |
| Churn logo (clientes) | 9,4% | 7,1% | 6,6% |
| Gross margin SaaS | 71% | 73% | 72% |
| EBITDA | R$ 2,1 mi | R$ 5,8 mi | R$ 6,4 mi |
| EBITDA margin | 5,7% | 11,1% | 11,2% |
| Caixa + aplicações | R$ 8,4 mi | R$ 11,9 mi | R$ 10,2 mi |

Mix de receita (não é ARR; soma 100% da receita bruta do período):

| Mix | FY2024 | FY2025 | R12 até jun/2026 |
|---|---|---|---|
| Helios | 68% | 61% | 59% |
| Nimbus | 22% | 28% | 30% |
| Serviços profissionais | 10% | 11% | 11% |

Atlas não é produto vendável; custo alocado em COGS de dados em todos os anos.

## 2.1 Hierarquia de receita (não somar duas vezes)

A Aurora é o **cliente principal** (nível 1). Em **2024** havia **um** subcliente (Lumen). Em **mar/2025** entra o terciário BioLumen (ARR 0 na Aurora). O segundo subcliente (NorteAlimentos) só existe a partir do PO **01/08/2026**.

| Nível | Entidade | ARR fim FY2024 | ARR fim FY2025 | ARR jun/2026 ou alvo |
|---|---|---|---|---|
| 1 Principal | Aurora Tech (operação + tenant raiz) | n/a | n/a | n/a (é quem reconhece o ARR) |
| 2 Sub A | Rede Clínica Lumen | R$ 3,18 mi | R$ 3,72 mi | R$ 4,10 mi (top 1) |
| 2 Sub B | NorteAlimentos | não existia | não existia | R$ 0 até go-live; alvo R$ 736.320 |
| 3 Terciário | BioLumen (sob a Lumen) | não existia | **R$ 0** (org_unit desde 03/2025) | **R$ 0** — não faturar |

Concentração top 5 do ARR: 38% (FY2024) → 34% (FY2025) → 31% (R12 jun/2026). Lumen sozinha: 8,1% do ARR FY2024 (3,18 / 39,5); 6,8% do FY2025 (3,72 / 55,0); 6,6% do R12 (4,10 / 61,8).

Maior subcliente em 2024, 2025 e jun/2026: **Lumen**. NorteAlimentos **não** entra no ranking enquanto não houver go-live. Lives do BioLumen já estão dentro das lives da Lumen — não somar de novo.

## 3. Operação comercial

| Indicador | Q1 2026 | Q2 2026 |
|---|---|---|
| Pipeline ponderado | R$ 18,4 mi | R$ 21,9 mi |
| Win rate (nº deals) | 22% | 25% |
| Ciclo mediano enterprise | 94 dias | 88 dias |
| Ticket mediano new logo | R$ 186 mil ARR | R$ 201 mil ARR |
| NPS clientes (relacional) | 41 | 44 |
| CSAT suporte N1 | 4,2 / 5 | 4,3 / 5 |

Quota Q2 2026 atingida: 97% (faltaram R$ 410 mil de um deal de manufatura perdido para concorrente).

| Indicador | Q1 2025 | Q2 2025 |
|---|---|---|
| Pipeline ponderado | R$ 14,1 mi | R$ 16,7 mi |
| Win rate (nº deals) | 19% | 21% |
| Ciclo mediano enterprise | 106 dias | 98 dias |
| Ticket mediano new logo | R$ 154 mil ARR | R$ 168 mil ARR |
| NPS clientes (relacional) | 36 | 39 |
| CSAT suporte N1 | 4,0 / 5 | 4,1 / 5 |

Quota Q2 2025 atingida: 94% (faltaram R$ 680 mil; ciclo ainda acima de 100 dias e win rate 21%).

| Indicador | Q1 2024 | Q2 2024 |
|---|---|---|
| Pipeline ponderado | R$ 10,8 mi | R$ 12,9 mi |
| Win rate (nº deals) | 16% | 18% |
| Ciclo mediano enterprise | 118 dias | 110 dias |
| Ticket mediano new logo | R$ 128 mil ARR | R$ 141 mil ARR |
| NPS clientes (relacional) | 32 | 35 |
| CSAT suporte N1 | 3,8 / 5 | 3,9 / 5 |

Quota Q2 2024 atingida: 89% (faltaram R$ 910 mil; comercial com 22–24 pessoas e win rate 18%).

Não há Q3/Q4 de 2026 neste documento (próxima emissão FIN-KPI-010 em 10/10/2026). 2024 e 2025 acima são o H1, no mesmo recorte de 2026.

## 4. Pessoas

| Data | Headcount total | Engenharia | CS + Support | Comercial | G&A |
|---|---|---|---|---|---|
| 30/06/2024 | 108 | 33 | 27 | 22 | 26 |
| 31/12/2024 | 118 | 36 | 29 | 24 | 29 |
| 30/06/2025 | 130 | 38 | 32 | 28 | 32 |
| 31/12/2025 | 141 | 41 | 34 | 31 | 35 |
| 30/06/2026 | 156 | 47 | 38 | 34 | 37 |

| Indicador People | FY2024 / Q2 2024 | FY2025 / Q2 2025 | Q2 2026 (R12) |
|---|---|---|---|
| Turnover voluntário 12 meses | 18,5% | 16,2% | 14,8% |
| People eNPS companhia | +4 | +11 | +18 |
| Modelo de escritório | 4 dias (terça a sexta) | 3 dias (terça a quinta) | 3 dias (terça a quinta) |
| Vale-refeição / dia útil | R$ 35 (Flash) | R$ 38 (Flash) | R$ 42 (Flash) |
| Unimed coparticipação | 30% | 20% | 20% |
| Custo fully loaded Engenharia | R$ 22,6 mil/mês | R$ 25,1 mil/mês | **R$ 28,4 mil/mês** |
| Hora interna postmortem SRE | R$ 220 | R$ 245 | R$ 280 |

Hora de 2026 alinhada ao relatório de Engenharia Q2. Plantão: adicional R$ 500 / semana na política mar/2024; **R$ 650** a partir de ago/2025 (POL-SRE-014-REV2).

## 5. Produto e uso

| Métrica | dez/2024 | jun/2025 | dez/2025 | jun/2026 |
|---|---|---|---|---|
| Tenants Helios ativos | 154 | 182 | 214 | 241 |
| Colaboradores geridos no Helios (soma clientes) | 135 mil | 160 mil | 186 mil | 211 mil |
| Requests Nimbus / mês | 238 mi | 318 mi | 410 mi | 538 mi |
| p95 Nimbus global | 210 ms | 195 ms | 180 ms | 164 ms |
| RAG interno (manuais em Markdown) | meta 2024: 0% (piloto) | meta 2025: ~30% (índice inicial) | meta 2025: ~70% | meta 2026: 100% (índice local) |

Uptime composto no status page (alvo comercial 99,90%) ≠ SLO interno de Engenharia (99,95% Helios) — vigente em 2024, 2025 e 2026. Lives globais de jun/2026 (211 mil) **não** somam as 180 do BioLumen de novo (já dentro da Lumen).

## 6. Capital e runway

| Indicador | Q2 2024 | Q2 2025 | Q2 2026 |
|---|---|---|---|
| Queima média / mês | R$ 0,70 mi | R$ 0,55 mi | R$ 0,90 mi |
| Caixa + aplicações (fim do recorte) | R$ 8,4 mi (FY2024) | R$ 11,9 mi (FY2025) | R$ 10,2 mi (jun/2026) |
| Runway sem novo equity | ~12 meses | ~22 meses | ~11 meses |
| Dívida (capital de giro) | R$ 1,2 mi | R$ 1,5 mi | R$ 2,0 mi |
| Custo da dívida | 2,1% a.m. | 1,9% a.m. | 1,8% a.m. |
| Vencimento | jan/2025 (rolado) | ago/2025 (rolado) | nov/2026 |

Queima de Q2 2026 sobe vs 2025 por IR e antecipação de cloud anual (GPU/RAG). Runway de 2026 é **antes** de converter o pipeline. Dívida de 2024/2025 foi rolada; o papel vigente vence em nov/2026.

## 7. Alertas da controladoria

1. **2026:** GPU/RAG cresceu 55% no trimestre (ver relatório Engenharia Q2 2026); risco de compressão de margem se não houver chargeback interno. Em **2025** o RAG ainda era ~30–70% dos manuais e a linha de GPU era imaterial no P&L. Em **2024** não havia `aurora-rag-index` no plantão (só entra na POL de ago/2025).  
2. **2026:** NorteAlimentos é subcliente nível 2 com PO em 01/08/2026; ARR alvo R$ 736 mil **não** está no ARR até o go-live. Em **2024–2025** o único subcliente com ARR era a Lumen. BioLumen (terciário desde 03/2025) não gera ARR.  
3. Dois documentos de plantão coexistem no corpus: Folha em 2024 paga **R$ 500** (POL-SRE-014); a partir de ago/2025 paga **R$ 650** (REV2). Não usar a tabela de 2024 para competência 2026.

## 8. Próxima emissão

FIN-KPI-010 prevista para 10/10/2026 (Q3).
