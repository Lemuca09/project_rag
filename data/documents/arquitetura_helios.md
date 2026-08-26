# Arquitetura técnica — plataforma Helios e satélites Atlas/Nimbus

**Documento:** ENG-ARCH-HELIOS-005  
**Revisão:** 4.18 (maio/2026)  
**Owner:** Architecture Guild  
**Audiência:** engenharia, segurança, novos contratados  
**Classificação:** interno

Descrição do sistema. Não é política de plantão, não é orçamento de cliente e não substitui o guideline de deploy.

## 1. Visão de contexto (C4 — container)

A Aurora Tech opera três superfícies:

- **Helios:** aplicação de RH (férias, ponto, aprovações, runbooks, incidentes, pós-mortem). Multi-tenant. UI React + BFF `helios-web`. Workers `helios-worker` para folha e notificações.  
- **Atlas:** plano de dados interno (dbt + jobs Python). Modelos `dim_employee`, `fct_leave`, `fct_incident`. Não é vendido. Alimenta métricas FIN-KPI e o relatório de Engenharia.  
- **Nimbus:** API pública versionada (`/v2`) para clientes. Webhooks, SSO SAML, quotas por tenant. É o produto cotado em ORC-2026-118.

O índice **aurora-rag-index** é serviço interno: TF-IDF + BM25, ingestão Markdown, usado pelo agente de chat corporativo. Não é exposto no Nimbus.

## 2. Runtime

| Componente | Runtime | Região | Notas |
|---|---|---|---|
| EKS `prod-sae1` | k8s 1.31 | sa-east-1a | DR 1b ainda sem capex (pedido Q2) |
| RDS PostgreSQL 16 | Multi-AZ | Helios OLTP | `leave_request`, `incident`, `tenant` |
| Redis 7 | ElastiCache | sessões Helios + `rag-cache` | P1-2026-052: evicted_keys |
| Kafka (MSK) | 3 brokers | eventos de domínio | `leave.requested`, `incident.opened` |
| Object storage | S3 `aurora-artifacts` | binários, dumps | versionado |
| GPU | g5.xlarge spot (meta Q3) | RAG reindex | custo Q2 R$ 291 mil |

Service mesh: Istio 1.22. Ingress: NLB + WAF. Observabilidade: Datadog (APM + logs) + Grafana on-call.

## 3. Modelo de tenancy

Helios: **schema compartilhado**, `tenant_id` em todas as tabelas de negócio, Row-Level Security no Postgres para jobs Atlas. Nimbus: a mesma base, exposição via gateway que injeta `tenant_id` do OAuth client.

Hierarquia CS-HIER-001:

- `tnt-aurora` — cliente principal.  
- `tnt-lumen` — subcliente dependente A (produção). Terciário BioLumen = `org_unit=biolumen` **sem** `tenant_id` próprio.  
- `tnt-nalim` — subcliente dependente B (NorteAlimentos). Namespace k8s `nalim` + fila SQS no hypercare: **reservado** após PO 01/08/2026; go-live alvo 16/02/2027.

Não criar namespace para BioLumen. Rate limit Nimbus default 800 rps/tenant nível 2; chave filha do terciário: 2 mi req/mês descontadas da Lumen.

Limite de desenho atual: 300 tenants / 250 mil lives no Helios. Jun/2026: 241 tenants / 211 mil lives (métricas corporativas).

## 4. Domínio de férias (recorte)

```
Colaborador → POST /helios/time-off
  → valida antecedência 30 dias, saldo, plantão SRE
  → evento Kafka leave.requested
  → worker calcula 1/3 + média HE + adicional plantão (500 até jul/2025; 650 desde ago/2025)
  → gestor aprova → Folha TOTVS (arquivo CNAB interno)
```

O SOP PEO-SOP-FER-012 descreve a UI. Este documento descreve o caminho de dados. Falha no worker `payroll.batch_v2` sem flag foi o P1-2026-041.

## 5. Caminho de um P1

Alerta Datadog → PagerDuty → plantonista (ack 15 min, canal `#incidentes`) → ticket Helios `Incidente` → runbook SRE-RB-P1-003 → postmortem PM-2025 no Helios. Atlas materializa `fct_incident` D+1 para o relatório trimestral.

## 6. Segurança

- mTLS no mesh.  
- Segredos: Vault; rotação 90 dias (política plantão 2025).  
- PII (CPF, salário) só em RDS; logs com redaction Datadog `sensitive_data_scanner`.  
- Nimbus: OAuth2 client credentials + optional SAML. Rate limit 800 rps/tenant default.  
- RAG interno: documentos em Markdown local; **não** indexar o guia de compostagem de Campinas em contextos de resposta sobre a empresa — o arquivo existe no corpus por ruído de pasta; o quality gate deve recusar se a pergunta for sobre Aurora e o trecho for SSP-CAM-AMB-033.

## 7. SLI de referência (não confundir com contrato)

| SLI | SLO interno | Alvo comercial status page |
|---|---|---|
| Helios availability | 99,95% | 99,90% |
| Nimbus p95 | 250 ms | 400 ms (enterprise pode cotar 400 ms, vide NorteAlimentos) |
| rag-index availability | 99,50% | não publicado |

Q2 2026: Helios 99,93%, Atlas 99,88%, Nimbus 99,96%, rag-index 99,12%.

## 8. Evolução prevista

Q3 2026: SSO SAML enterprise (deslizou), DR `sa-east-1b`, spot GPU, chargeback RAG. Q4: multi-região somente se capex for aprovado.

## 9. Referências cruzadas

POL-SRE-014-REV2, ENG-GL-DEPLOY-007, SRE-RB-P1-003, PEO-SOP-FER-012, FIN-KPI-009, REL-ENG-Q2-2026.
