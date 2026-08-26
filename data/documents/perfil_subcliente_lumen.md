# Perfil operacional — subcliente Rede Clínica Lumen (nível 2)

**Documento:** CS-SUB-LUMEN-002  
**Cliente principal:** Aurora Tech (`tnt-aurora`)  
**Este documento:** subcliente **dependente** da Aurora  
**Vigência:** atualizado 15/07/2026  
**Classificação:** interno CS / Engenharia

A Rede Clínica Lumen S.A. não é a Aurora. É o **subcliente A** no mapa CS-HIER-001. Tudo o que a Lumen opera no Helios/Nimbus depende do contrato mestre com a Aurora. Abaixo da Lumen existe o cliente **terciário** BioLumen.

## 1. Cadastro

| Campo | Valor |
|---|---|
| Razão social | Rede Clínica Lumen S.A. |
| CNPJ | 11.208.771/0001-03 |
| Nível | 2 — subcliente dependente |
| Tenant | `tnt-lumen` |
| Namespace | `prod-lumen` |
| Contrato mestre | CTR-AUR-LUMEN-2019-07, aditivo 2025 |
| ARR na Aurora (jun/2026) | R$ 4.100.000 |
| Lives Helios | 12.400 (inclui 180 do terciário BioLumen) |
| Go-live original | 11/2019 |
| Executiva CS | Renata Moura |
| NPS relacional Q2 2026 | 48 |

## 2. Produtos contratados

Helios RH (férias, plantão clínico interno da Lumen — **não** confundir com plantão SRE da Aurora), Nimbus API `/v2` média 42 mi req/mês, SSO SAML (Okta da Lumen). **Não** contrata Atlas analítico. **Não** tem GPU/RAG.

SLA comercial: disponibilidade Helios 99,90% (crédito 5%/15% como tabela enterprise padrão). Ack P1 no canal do cliente: 30 min 8h–20h. Isso **não** altera o ack interno de 15 min da POL-SRE-014-REV2.

## 3. Dependência da Aurora

- Identidade Nimbus: issuer da Aurora; se `tnt-aurora` perder certificado raiz, Lumen e BioLumen caem juntos.  
- Billing: fatura única Aurora → Lumen. A Lumen **repassa** custo do terciário.  
- Churn da Lumen: cancela `tnt-lumen` e, em cascata, BioLumen. NorteAlimentos não é afetado.  
- Customizações: 3 campos extras em `leave_request` (`plantao_uti`, `crm_medico`, `unidade_lumen`). Não copiar esses campos para `tnt-nalim`.

## 4. Relação com o terciário BioLumen

BioLumen é laboratório de análises da rede, CNPJ próprio, **sem** contrato com a Aurora. A Lumen provisiona `org_unit=biolumen` e emite a chave Nimbus `oa-lumen.biolumen` com scope `labs.read labs.orders`. Quota da chave filha: 2 mi req/mês, descontada da quota da Lumen (não é faixa extra na Aurora).

Suporte BioLumen: N1 da própria Lumen. Ticket na Aurora só se CS Lumen escalar com ID `tnt-lumen` e texto explícito “impacto rede completa”.

## 5. Incidentes recentes (não são P1 da Aurora)

2026-05-19: CORS em staging Nimbus (pen-test Astrum) — corrigido 19/06, citado no relatório de Engenharia Q2. Impacto Lumen em staging apenas.  
Nenhum P1 de produção Lumen no Q2 2026.

## 6. O que não fazer

- Não aplicar preços ORC-2026-118 (NorteAlimentos) neste tenant.  
- Não abrir namespace `nalim` para a Lumen.  
- Não indexar o guia de compostagem de Campinas como “política da Lumen”.  
- Não pagar adicional de plantão SRE (R$ 650) contra o CNPJ da Lumen.
