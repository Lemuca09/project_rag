# Orçamento comercial — implantação Nimbus + Helios RH

**Proposta:** ORC-2026-118  
**CNPJ NorteAlimentos:** 08.441.902/0001-40  
**Cliente (nível):** NorteAlimentos S.A. — **subcliente dependente nível 2** da Aurora Tech (CS-HIER-001)  
**Cliente principal da cadeia:** Aurora Tech (`tnt-aurora`)  
**Não é:** cliente terciário (terciário = BioLumen, sob a Lumen)  
**Contato cliente:** Paulo Henrique Vasconcelos, TI corporativa  
**Executivo Aurora Tech:** Camila Prado (Enterprise)  
**Data da proposta:** 14/07/2026  
**Validade:** 45 dias (até 28/08/2026)  
**Moeda:** BRL  
**Classificação:** confidencial — uso do cliente e da Aurora Tech

Este documento é um **orçamento de projeto** para o **segundo subcliente dependente** da Aurora (o primeiro é a Rede Clínica Lumen, já em produção). Preços de lista internos (custo engenharia R$ 280/h) não devem ser revelados ao cliente; a tabela abaixo já está em preço de venda.

NorteAlimentos **não** herda o tenant `tnt-lumen` nem o `org_unit` BioLumen. Tenant alvo: `tnt-nalim`. PO de dependência assinado em **01/08/2026**; até o go-live o ARR deste subcliente ainda não entra no FIN-KPI.

## 1. Escopo resumido

Implantação de Helios (RH, férias, plantão de times do cliente) e Nimbus (API de integração com o ERP TOTVS RM da NorteAlimentos), ambiente dedicado `prod-nalim`, SSO SAML, janela de hypercare 60 dias e treino de 12 administradores.

Fora de escopo: customização de folha de pagamento brasileira além dos eventos já homologados, GPU/RAG corporativo da Aurora, e qualquer módulo Atlas analítico.

## 2. Premissas técnicas

- Até **2.400 colaboradores** ativos no Helios no go-live.  
- Integração TOTVS: 14 endpoints REST, latência p95 acordada 400 ms na VPC peering.  
- RPO 1 h / RTO 4 h no plano de DR compartilhado (não dedicado).  
- Dados residem em `sa-east-1`. Não há replicação para Europa neste contrato.

## 3. Cronograma comercial

| Fase | Duração | Marco faturável |
|---|---|---|
| Kickoff e desenho | 3 semanas | 20% |
| Integração TOTVS + SSO | 7 semanas | 30% |
| Homologação UAT | 3 semanas | 20% |
| Go-live + hypercare | 9 semanas (4 + 5) | 30% |
| **Total** | **22 semanas** | 100% |

Início previsto se PO até 28/08/2026: **15/09/2026**. Go-live alvo: **16/02/2027**.

## 4. Preços — implantação (one-time)

| Item | Qtd | Preço unitário | Total |
|---|---|---|---|
| Licença setup Helios (tenant dedicado) | 1 | R$ 86.000 | R$ 86.000 |
| Licença setup Nimbus (API + webhooks v2) | 1 | R$ 54.000 | R$ 54.000 |
| Integração TOTVS RM (pacote 14 endpoints) | 1 | R$ 128.000 | R$ 128.000 |
| SSO SAML (Okta / ADFS) | 1 | R$ 22.500 | R$ 22.500 |
| Migração histórica de férias (até 5 anos) | 1 | R$ 19.800 | R$ 19.800 |
| Treinamento 12 admins (16 h presenciais em Recife) | 1 | R$ 14.400 | R$ 14.400 |
| Hypercare 60 dias (fila P2 dedicada, horário 8h–20h) | 1 | R$ 36.000 | R$ 36.000 |
| **Subtotal implantação** | | | **R$ 360.700** |

Impostos (ISS 5% + PIS/COFINS no regime da proposta): **R$ 41.480,50**.  
**Total implantação com impostos:** **R$ 402.180,50**.

## 5. Recorrência anual (SaaS)

| Item | Métrica | Preço |
|---|---|---|
| Helios RH | R$ 18,90 / colaborador / mês | R$ 45.360 / mês na base de 2.400 |
| Nimbus API | faixa até 8 milhões req/mês | R$ 9.200 / mês |
| Ambiente dedicado (compute mínimo) | fixo | R$ 6.800 / mês |
| **ARR estimado no go-live** | | **R$ 736.320 / ano** |

Excedente de API: R$ 1,15 por milhão de requests acima de 8 mi. Excedente de headcount Helios: pró-rata do unitário no mês.

Desconto enterprise nesta proposta: **8%** na implantação se PO integral até 15/08/2026 (não cumulativo com o prazo de validade estendido). Com desconto: implantação R$ 331.844 + impostos.

## 6. SLA contratual oferecido ao cliente

| Classe | Disponibilidade mensal | Crédito |
|---|---|---|
| Helios | 99,90% | 5% da mensalidade Helios se 99,5–99,90; 15% se < 99,5 |
| Nimbus | 99,90% | idem sobre a mensalidade Nimbus |
| Ack P1 (canal do cliente) | 30 min em horário 8h–20h BRT | sem crédito automático; registra ticket |

Estes SLAs de **contrato comercial** não substituem os SLOs internos da POL-SRE-014-REV2 (ack P1 interno 15 min). O subcliente NorteAlimentos **não** entra na escala `#incidentes` interna. O terciário BioLumen **não** é parte desta proposta.

## 7. Equipe alocada (lado Aurora)

- 1 gerente de projeto (0,5 FTE, 22 semanas)  
- 2 engenheiros de integração (1,0 FTE)  
- 1 consultor Helios RH (0,6 FTE)  
- 1 SRE (0,3 FTE na homologação e go-live)

Capacidade reservada; não implica que o VP de Engenharia (relatório Q2) esteja alocado neste cliente.

## 8. Condições de pagamento

Boleto 28 dias. Implantação em 4 faturas alinhadas aos marcos da seção 3. SaaS: mensal antecipado a partir do go-live. Reajuste anual IPCA, teto 6,5% a.a. neste contrato.

## 9. Aceite

Espaço para assinatura NorteAlimentos / Aurora Tech. Proposta elaborada em São Paulo, 14/07/2026.
