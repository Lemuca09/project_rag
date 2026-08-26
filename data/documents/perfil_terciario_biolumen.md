# Perfil — cliente terciário Laboratório Diagnóstico BioLumen

**Documento:** CS-TER-BIOLUMEN-001  
**Nível:** 3 — terciário  
**Depende de:** Rede Clínica Lumen (subcliente nível 2)  
**Cliente principal da cadeia:** Aurora Tech  
**Atualizado:** 20/06/2026  
**Classificação:** interno CS

BioLumen **não** é cliente da Aurora Tech. Não assina DPA com a Aurora, não recebe fatura da Aurora, não tem tenant k8s, não entra em `#incidentes`. Qualquer resposta de RAG que trate BioLumen como “cliente Aurora” está errada.

## 1. Cadastro

| Campo | Valor |
|---|---|
| Razão social | Laboratório Diagnóstico BioLumen Ltda. |
| CNPJ | 44.019.332/0001-91 |
| Nível | 3 — terciário |
| Pai (nível 2) | Rede Clínica Lumen (`tnt-lumen`) |
| Avô (nível 1) | Aurora Tech (`tnt-aurora`) |
| Identidade técnica | `org_unit=biolumen` dentro de `tnt-lumen` |
| Contrato com a Aurora | **inexistente** |
| Contrato com a Lumen | CL-2025-44 (mar/2025) |
| Lives no Helios | 180 (já contidas nas 12.400 da Lumen) |
| Receita na Aurora | R$ 0 |
| Sede | unidade Lumen Moema, São Paulo |

## 2. O que a BioLumen usa (por herança)

- Login Helios via IdP da Lumen (Okta); grupo `biolumen-staff`.  
- Nimbus: chave `oa-lumen.biolumen`, scopes `labs.read` e `labs.orders` apenas. Sem webhooks v2.  
- Sem módulo de férias corporativo Aurora (People da Aurora). Férias dos 180 lives: política **da Lumen**, não o SOP PEO-SOP-FER-012 (esse SOP é só CLT da Aurora).  
- Sem plantão SRE. Plantão de analistas clínicos é escala interna Lumen (`plantao_uti` no Helios da Lumen).

## 3. Queda em cascata

Se a Aurora suspender a Lumen: BioLumen perde Helios e Nimbus no mesmo instante.  
Se a Lumen desligar só o `org_unit` BioLumen: Aurora continua; NorteAlimentos continua; Lumen continua.  
Se NorteAlimentos falhar no go-live: **zero** efeito na BioLumen.

## 4. Dados e privacidade

Laudos laboratoriais **não** saem no Nimbus da Aurora além dos scopes acima. Atlas da Aurora **não** materializa `fct_lab_result`. Proibido jogar CSV de exames no corpus RAG interno da Aurora.

## 5. Contato (somente via Lumen)

CS Aurora não atende ramal da BioLumen. Encaminhar o solicitante para Renata Moura (CS Lumen) ou para o N1 Lumen. Abrir ticket Helios da Aurora com tenant `tnt-lumen:biolumen` é recusado pelo workflow (`nível 3 — escalar pai`).
