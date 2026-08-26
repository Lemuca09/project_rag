# Relatório trimestral — Engenharia de Plataforma

**Unidade:** Engenharia / SRE / Dados  
**Período:** Q2 2026 (01/04/2026 a 30/06/2026)  
**Emitido em:** 08/07/2026  
**Autor:** Marina Alves, VP de Engenharia  
**Distribuição:** comitê executivo, Financeiro, People  
**Classificação:** interno — não encaminhar a cliente

Relatório de departamento. Consolida operação, qualidade, custo de nuvem e entregas. Números de receita consolidada da companhia estão no documento de métricas FY2025/rolling 2026; aqui o recorte é **só Engenharia**.

## 1. Resumo executivo

O trimestre fechou com disponibilidade composta (Helios + Atlas + Nimbus) de **99,91%**, abaixo da meta interna de 99,95%. Houve **3 P1** (dois de autoria de deploy sem feature flag, um de saturação de Redis no RAG index). DORA: lead time mediano 18 h (meta 12 h), CFR 14,2% (meta < 10%). Headcount Engenharia: **47** pessoas no último dia do trimestre (41 em 31/03/2026).

Custo AWS + GCP: **R$ 1,84 milhão** no trimestre (+11% vs Q1), puxado por GPU `g5.xlarge` do índice RAG e por retraining mensal que ainda não foi movido para spot.

## 2. Disponibilidade e incidentes

| Serviço | SLO interno | Observado Q2 | Error budget restante | P1 | P2 |
|---|---|---|---|---|---|
| Helios (RH) | 99,95% | 99,93% | 18% do budget trimestral | 1 | 4 |
| Atlas (dados) | 99,90% | 99,88% | 0% (estourado) | 1 | 6 |
| Nimbus (API clientes) | 99,95% | 99,96% | 62% | 0 | 2 |
| aurora-rag-index | 99,50% | 99,12% | estourado | 1 | 3 |

P1-2026-041 (12/05): deploy Helios 4.18 sem flag `payroll.batch_v2` derrubou cálculo de férias por 71 minutos. Ack em 11 min (dentro da POL-SRE-014-REV2). Custo evitado estimado no postmortem: R$ 19,6 mil (horas × R$ 280).  
P1-2026-052 (03/06): Redis `rag-cache` sem `maxmemory-policy` adequado; p95 de retrieve 4,8 s. Mitigação 39 min.  
P1-2026-061 (28/06): job Atlas `dim_employee` duplicou chaves após backfill; impacto em relatórios People, não em folha.

Postmortems: 3/3 no Helios dentro de 5 dias úteis (conforme política vigente de agosto/2025). A política de 2024 (10 dias, Confluence) **não** foi usada.

## 3. Entregas e backlog

Concluído: Helios 4.18 (módulo Runbooks), Nimbus webhooks v2, pipeline de dedup Jaccard no RAG, conversão docx→md.  
Deslizado para Q3: SSO SAML para clientes enterprise (bloqueio jurídico no DPA), multi-região Atlas.

Throughput: 61 PRs mergeados/semana (mediana), 11 serviços com dono no catálogo. Dívida: 214 tickets `tech-debt`, 37 com idade > 90 dias.

## 4. Pessoas e escala de plantão

Escala SRE: 9 aptos (igual à POL vigente). Houve 2 isenções por sono interrompido (P1-041 e P1-052). Adicional de plantão pago no trimestre: **R$ 23.400** (primário) + **R$ 5.940** (secundário), alinhado a R$ 650 / R$ 220 por semana.

People reportou eNPS Engenharia **+31** (Q1 era +24). Turnover voluntário: 1 pessoa (data engineer). Vagas abertas em 30/06: 4 (2 SRE, 1 platform, 1 NLP).

## 5. Segurança e compliance

- Patch CVE-2026-1184 (OpenSSL) em 100% dos AMIs em 9 dias.  
- Acesso break-glass Vault: 7 usos, todos com ticket Helios.  
- DLP: 0 incidentes de PII em log público.  
- Pen-test Q2 (vendor Astrum): 1 high (CORS Nimbus staging), corrigido 19/06.

## 6. Custos de nuvem (R$ mil)

| Rubrica | Q1 2026 | Q2 2026 | Δ |
|---|---|---|---|
| Compute (ECS/EKS) | 612 | 658 | +7,5% |
| Banco (RDS/Aurora PostgreSQL) | 401 | 418 | +4,2% |
| GPU / RAG | 188 | 291 | +54,8% |
| Tráfego + NAT | 97 | 112 | +15,5% |
| Observabilidade (Datadog) | 210 | 221 | +5,2% |
| Outros | 150 | 140 | −6,7% |
| **Total** | **1.658** | **1.840** | **+11,0%** |

Ação Q3: migrar retraining RAG para spot + schedule noturno; meta de reduzir GPU em 25%.

## 7. Pedidos ao comitê

1. Aprovar +2 SRE antes de outubro (risco de escala < 8 aptos se houver férias simultâneas).  
2. Capex de R$ 180 mil para ambiente de DR em `sa-east-1b` (hoje só `sa-east-1a`).  
3. Congelar features de Nimbus na semana 32 para o pen-test enterprise do **subcliente** NorteAlimentos (`tnt-nalim`). Não usar o tenant da Lumen nem o `org_unit` BioLumen nesse teste.

## 8. Assinaturas

Marina Alves (Engenharia) — 08/07/2026  
Ciente: CFO (custo nuvem) e People (headcount).
