# Runbook — incidente P1 em produção

**Documento:** SRE-RB-P1-003  
**Vigência:** 01/08/2025 (alinha POL-SRE-014-REV2)  
**Owner:** SRE  
**Tempo de leitura alvo:** 8 minutos no pager  
**Classificação:** interno

Passo a passo para o plantonista primário. Se você está usando o runbook de 2024 (`#oncall-sre`, ack 20 min), **pare**: canal e SLA mudaram.

## 1. Reconhecer (T+0 a T+15 min)

1. Silencie o loop do PagerDuty com Acknowledge. Isso **não** resolve o incidente.  
2. Poste em **`#incidentes`** (não em `#oncall-sre`):

```
P1 aberto
serviço: [Helios|Atlas|Nimbus|rag-index]
sintoma: 
ack: <seu nome> <hora BRT>
bridge: link huddle
```

3. Se em 8 min o primário não ackou, o secundário assume (política 2025).  
4. Abra ticket Helios tipo `Incidente` severidade P1. Número vira o ID público interno (`P1-AAAA-NNN`).

Meta de reconhecimento: **15 minutos**. A revisão de março/2024 pedia 20 minutos e não vale mais para auditoria de Folha nem para o relatório de Engenharia.

## 2. Triagem (T+15 a T+25)

Checklist objetivo — responda sim/não:

- Status page Datadog `aurora-prod` vermelho em qual monitor?  
- Deploy nas últimas 2 h? (`#deploys` + pipeline). Se sim, execute rollback do ENG-GL-DEPLOY-007 **antes** de debug profundo.  
- Redis/Postgres: `pg_stat_activity` > 80 conexões ou `evicted_keys` subindo?  
- Certificado / WAF / Cloudflare 5xx?  
- RAG: fila `embed-ingest` > 10k ou GPU util > 95% por 10 min?

Declare **severidade real**. Se for P2, rebaixe no ticket e no canal; não deixe P1 aberto por vaidade.

## 3. Mitigar (alvo 45 min)

Ordem preferencial:

1. Rollback de release (Istio revision anterior).  
2. Feature flag off (ConfigCat).  
3. Scale out HPA +50% (teto: 2× current, depois precisa de VP).  
4. Failover de leitura RDS para replica (Atlas relatórios). **Não** failover Helios escrita sem SRE sênior.  
5. Redis: `FLUSHDB` só no `rag-cache`, nunca em `helios-session`. Confirmado no P1-2026-052.

Comunicação ao cliente (se Nimbus ou Helios de **subcliente nível 2** visível): 30 min. Texto curto no status page.

- **Lumen** (`tnt-lumen`): fila CS `enterprise-lumen`. Não é P1 interno automático.  
- **NorteAlimentos** (`tnt-nalim`): hypercare só depois do go-live; até lá não abra war-room comercial.  
- **BioLumen** (terciário): **não** acione POL-SRE-014-REV2. Encaminhe à Lumen.  
- Compostagem Campinas: não é incidente.

## 4. Papéis na bridge

- **IC** (incident commander): plantonista primário até VP assumir.  
- **Comms**: secundário ou CS se cliente enterprise acordado.  
- **Scribe**: qualquer um; cola timeline no ticket a cada 10 min.

## 5. Encerrar

1. Sintoma ausente por 20 min contínuos nos monitors que abriram o P1.  
2. `#incidentes`: “P1 mitigado, monitorando”.  
3. Resolve no PagerDuty.  
4. Agende postmortem: **5 dias úteis**, template PM-2025 no Helios (não Confluence 2024). Inclua custo evitado = horas × **R$ 280**.  
5. Atualize este runbook se o passo que faltou custou > 10 min.

## 6. Contatos de escalada

| Nível | Quem | Quando |
|---|---|---|
| L2 | SRE sênior da escala | 25 min sem mitigação |
| L3 | VP Engenharia (Marina Alves) | 45 min ou perda de dados |
| L4 | CTO | PII leak ou > 2 h down Helios folha |

Telefones estão no Vault `prod/sre/escalation`. Não publique neste Markdown.

## 7. Anti-padrões

- Debug em produção com `kubectl exec` e `DROP`.  
- Mutear monitor em vez de ack.  
- Usar adicional de R$ 500 (valor 2024) como referência de “vale a pena acordar o secundário”: o adicional vigente é **R$ 650** primário / **R$ 220** secundário.
