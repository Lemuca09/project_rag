# Hierarquia de clientes — Aurora Tech como cliente principal

**Documento:** CS-HIER-001  
**Vigência:** 01/08/2026  
**Owner:** Customer Success + Jurídico  
**Classificação:** interno  
**Substitui:** qualquer menção solta a “clientes Nimbus” sem nível

A Aurora Tech é o **cliente principal** (nível 1) da plataforma Helios/Nimbus neste corpus. Abaixo dela existem exatamente **dois subclientes dependentes** (nível 2) e **um cliente terciário** (nível 3). Nenhum outro tenant deve ser tratado como contrato direto sem passar por esta hierarquia.

Perguntas do tipo “quem é o cliente?” devem distinguir o nível. Faturamento, SLA, canal `#incidentes` e namespace k8s **não** são iguais nos três níveis.

## 1. Mapa

```
Nível 1 — Cliente principal
└── Aurora Tech Serviços de Software Ltda.  (CNPJ 23.901.448/0001-77)
    tenant raiz: tnt-aurora
    ├── Nível 2 — Subcliente dependente A
    │   └── Rede Clínica Lumen S.A.         (CNPJ 11.208.771/0001-03)
    │       tenant: tnt-lumen
    │       └── Nível 3 — Cliente terciário
    │           └── Laboratório Diagnóstico BioLumen Ltda.
    │               (CNPJ 44.019.332/0001-91)
    │               subtenant: tnt-lumen:biolumen
    └── Nível 2 — Subcliente dependente B
        └── NorteAlimentos S.A.             (CNPJ 08.441.902/0001-40)
            tenant: tnt-nalim  (em implantação; PO 01/08/2026)
```

O guia de compostagem de Campinas **não** é cliente de nenhum nível.

## 2. Regras de dependência

| Nível | Quem paga a Aurora | Contrato Helios/Nimbus | Tenant próprio | Entra na escala `#incidentes` | Status page Aurora |
|---|---|---|---|---|---|
| 1 Principal | — (é a operadora + tenant raiz interno) | n/a interno | `tnt-aurora` | sim (POL-SRE-014-REV2) | interno |
| 2 Subcliente | sim, faturamento direto | sim, master com a Aurora | sim | **não** (fila CS / SLA comercial) | se P2+ no produto contratado |
| 3 Terciário | **não** — paga o subcliente Lumen | **não** há contrato com a Aurora | não; herda `tnt-lumen` | não | não |

Subcliente **dependente** significa: o tenant só existe enquanto o contrato mestre com a Aurora estiver ativo; churn da Aurora (hipótese) derruba Lumen e NorteAlimentos; churn da Lumen derruba o terciário BioLumen, mas **não** derruba NorteAlimentos.

## 3. Identificadores técnicos

| Entidade | `tenant_id` | Namespace k8s | OAuth Nimbus | Lives Helios (jun/2026 ou alvo) |
|---|---|---|---|---|
| Aurora (principal) | `tnt-aurora` | `prod-aurora` | interno | 156 colaboradores próprios |
| Lumen (sub A) | `tnt-lumen` | `prod-lumen` | `oa-lumen` | 12.400 lives |
| BioLumen (terciário) | `tnt-lumen:biolumen` | nenhum (pods da Lumen) | chave filha `oa-lumen.biolumen` emitida pela Lumen | 180 lives |
| NorteAlimentos (sub B) | `tnt-nalim` | `nalim` (reservado) | `oa-nalim` (após go-live) | 2.400 lives no go-live |

RLS no Postgres: `tenant_id IN ('tnt-aurora','tnt-lumen','tnt-nalim')`. O terciário **não** tem linha própria em `tenant`; o filtro é `tenant_id = 'tnt-lumen' AND org_unit = 'biolumen'`.

## 4. Faturamento (quem aparece no ARR da Aurora)

- **Lumen:** ARR **R$ 4,10 mi** — já no FIN-KPI-009 (top 1).  
- **NorteAlimentos:** ARR alvo **R$ 736.320** (ORC-2026-118) entra no ARR só após go-live; PO assinado 01/08/2026, implantação em curso.  
- **BioLumen:** R$ 0 na Aurora. A Lumen cobra BioLumen à parte (contrato Lumen–BioLumen CL-2025-44, valor interno da Lumen ≈ R$ 18 mil/mês). Chargeback interno Atlas pode marcar `cost_center=lumen.biolumen` só para custo de nuvem, não para receita.

## 5. Suporte e incidente

P1 na API Nimbus da Lumen: CS abre fila `enterprise-lumen`. Plantonista Aurora só entra se o IC declarar impacto em malha compartilhada (Istio/RDS).  
P1 só em BioLumen (180 lives): a Lumen trata. Aurora **não** aciona POL-SRE-014-REV2.  
P1 NorteAlimentos: após go-live, hypercare 60 dias com fila dedicada 8h–20h (orçamento); fora do hypercare, mesmo regime da Lumen.

## 6. O que o RAG não deve misturar

- Preço de implantação NorteAlimentos **não** se aplica à Lumen.  
- Adicional de plantão R$ 650 é custo **interno Aurora** (nível 1), não é cobrado do terciário.  
- Lives 211 mil nas métricas = soma de todos os tenants vendidos; **não** some 180 do BioLumen de novo (já estão dentro das 12.400 da Lumen).

## 7. Histórico

| Data | Evento |
|---|---|
| 2019 | Lumen vira subcliente nível 2. |
| 03/2025 | BioLumen entra como org_unit terciária sob a Lumen. |
| 01/08/2026 | PO NorteAlimentos — segundo subcliente dependente. |
| 16/02/2027 | Go-live alvo NorteAlimentos. |
