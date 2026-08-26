# Guideline — deploy em produção (Helios, Atlas, Nimbus)

**Documento:** ENG-GL-DEPLOY-007  
**Vigência:** 12/05/2026  
**Owner:** Platform Engineering  
**Audiência:** qualquer engenheiro com permissão `prod-deploy`  
**Classificação:** interno

Procedimento obrigatório. Deploy que pule este guideline é causa raiz aceitável em postmortem (ver P1-2026-041 no relatório Q2).

## 1. O que pode ir para produção

Somente artefatos versionados do GitHub Actions workflow `prod-deploy.yml`, a partir da branch `main`, tag `vX.Y.Z` assinada. Hotfix: branch `hotfix/*` com aprovação de 2 maintainers (um deles SRE). **Proibido** `kubectl apply` local contra o cluster `prod-sae1`.

Serviços cobertos: `helios-web`, `helios-worker`, `atlas-jobs`, `nimbus-api`, `aurora-rag-index`. Bancos: migrações Prisma/Flyway **nunca** no mesmo pipeline do binário se forem expand/contract incompletos.

## 2. Pré-checagem (T-0)

Execute na ordem. Se qualquer item falhar, **pare**.

1. `gh run list --branch main` verde nos últimos 24 h no repositório do serviço.  
2. Changelog no Helios ticket tipo `Release` com: risco (baixo/médio/alto), SLO afetado, flag name, plano de rollback (commit SHA anterior).  
3. Datadog monitor `deploy.canary.error_rate` em OK.  
4. Error budget do serviço > 10% no trimestre (consulta Grafana `slo-board`). Se Atlas estiver com budget estourado (como no Q2 2026), deploy alto risco exige VP Engenharia.  
5. Janela: dias úteis **10h–16h BRT**. Sexta depois das 14h: só P1. Plantão vigente (POL-SRE-014-REV2) deve estar coberto; avise `#incidentes` 15 min antes.

## 3. Feature flags

Todo comportamento novo em Helios/Nimbus exige flag no serviço `configcat` projeto `aurora-prod`. Nome: `squad.superficie.descricao` (ex.: `payroll.batch_v2`). Rollout: 0% → 5% internos → 25% → 100%. Tempo mínimo entre degraus: 30 min com p95 e 5xx estáveis.

P1-2026-041 ocorreu porque `payroll.batch_v2` foi mergeado **ligado**. Checklist: PR template pergunta “flag default false?”. Reviewer bloqueia se a resposta for vazia.

## 4. Canary

1. Publicar tag. Pipeline sobe **1** replica canary com label `track=canary`.  
2. Traffic split Istio 5% por 20 minutos.  
3. Abortar se: 5xx > 0,5% absoluto **ou** p95 > 1,3× baseline 1 h.  
4. Promover: 25% (15 min) → 50% (15 min) → 100%.  
5. Somente então o pipeline escala o ReplicaSet estável e remove o canary.

`aurora-rag-index`: canary é um pod de retrieve-only; **não** rode reindexação completa em canary (custo GPU; ver métricas de nuvem Q2).

## 5. Migração de schema

Padrão expand/contract:

- Expansão: add column nullable / new table. Deploy app. Backfill job `atlas-jobs` com `max_in_flight=50`.  
- Contrato: app deixa de ler coluna velha.  
- Contração: drop em release **seguinte**, mínimo 7 dias depois.

Proibido `LOCK TABLE` em Helios no horário 8h–19h. Folha e férias usam as mesmas tabelas `leave_request`.

## 6. Rollback

Tempo alvo: **10 minutos** até tráfego 100% no SHA anterior.

```
# operador: nunca cole senha; use Vault
istioctl rollback <service> --revision <prev>
# se migração expand já rodou: NÃO dropar coluna no pânico; só reverter app
```

Abra P1 no `#incidentes` se o rollback for por erro de usuário. Ack continua 15 min (política 2025, não 20 min de 2024).

## 7. Comunicação

- Início: thread no `#deploys` com link do Release ticket.  
- Cliente externo (Nimbus): status page só se P2+ visível em tenant **nível 2**. Lumen = `prod-lumen`. NorteAlimentos = `nalim` somente após go-live. Terciário BioLumen não tem canary próprio (tráfego da Lumen).  
- Fim: marcar ticket Helios `Release` como concluído e colar SHA.

## 8. Exceções

Emergência de segurança (CVE crítico): CTO ou VP Engenharia libera janela fora de 10h–16h. Mesmo assim canary 5% por no mínimo 10 min, salvo cluster down.

## 9. Registro de revisão

| Data | Nota |
|---|---|
| 12/05/2026 | Inclusão obrigatória de flag após P1-2026-041. |
| 20/06/2026 | Canary RAG retrieve-only. |
