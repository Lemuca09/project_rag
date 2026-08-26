# Política de plantão de engenharia — Aurora Tech

**Documento:** POL-SRE-014-REV2  
**Vigência:** a partir de 01/08/2025 (indeterminado)  
**Substitui:** POL-SRE-014 de 01/03/2024  
**Elaboração:** SRE / Engenharia de Plataforma  
**Aprovação:** CTO, 22/07/2025  
**Classificação:** interno

Este documento é a política **vigente** de plantão. Qualquer cálculo de adicional, SLA de P1 ou ferramenta que cite a revisão de março/2024 está desatualizado.

## 1. Objetivo e escopo

Cobrir disponibilidade de Helios, Atlas, Nimbus e, a partir desta revisão, o **pipeline de embeddings internos do RAG corporativo** (serviço `aurora-rag-index`). Helpdesk N1 permanece fora do escopo.

## 2. Janela de cobertura (vigência 2025)

O plantão semanal começa na **segunda-feira às 9h** (horário de Brasília) e termina na segunda seguinte às 9h. Há plantonista primário e secundário. O secundário é acionado se o primário não reconhecer o alerta em **8 minutos**.

Sexta-feira o expediente interno pode encerrar às 17h se não houver plantão de cliente; o plantão de engenharia **não** encerra. Feriados: a escala permanece; o adicional semanal não é majorado.

## 3. Severidade e tempos de resposta (2025)

| Severidade | Definição | Reconhecimento | Mitigação inicial | Comunicação ao cliente |
|---|---|---|---|---|
| P1 | Indisponibilidade total, perda de dados, ou vazamento PII | **15 minutos** | 45 minutos | 30 minutos |
| P2 | Latência p95 > 2× baseline ou 5xx > 1% por 10 min | 25 minutos | 2 horas | 90 minutos |
| P3 | Falha localizada com workaround | 2 horas úteis | 8 horas úteis | sob demanda |
| P4 | Ruído / melhoria | backlog | backlog | não |

Canal oficial de P1: **`#incidentes`**. PagerDuty continua como pager. O canal `#oncall-sre` virou arquivo histórico em 01/08/2025; alertas novos **não** devem ser postados lá.

## 4. Compensação (valores atualizados)

- Adicional de plantão primário: **R$ 650,00** por semana completa (era R$ 500 na revisão 2024).
- Chamado P1 fora do expediente: hora extra 100% + adicional semanal.
- Plantonista secundário: **R$ 220,00** por semana.
- Semana parcial ≥ 48h: proporcional em 1/7 do adicional por dia coberto.
- Bônus trimestral de “zero P1 por culpa de runbook desatualizado”: R$ 400 por pessoa da escala, condicionado a postmortem no prazo.

## 5. Ferramentas obrigatórias na escala 2025

1. PagerDuty + Datadog (monitors com tag `oncall:true`).  
2. VPN WireGuard perfil `sre-prod`.  
3. Runbooks versionados em `data/documents` e no Helios módulo **Runbooks** (Confluence 2024 é somente leitura).  
4. Vault `prod/sre` com rotação de 90 dias.  
5. Grafana pasta `Prod/Oncall` e playbook `P1-ack` no Slack.

## 6. Rotação e saúde da escala

Máximo de **1 semana consecutiva** de primário (reduzido em relação a 2024). Após 2 semanas no trimestre, realocação obrigatória. Atestado de sono interrompido (>2 noites com P1) gera isenção de 45 dias.

Headcount SRE em julho/2025: **9** engenheiros aptos. Ciclo teórico: 9 semanas. Folga média entre plantões: 8 semanas.

## 7. Pós-incidente (2025)

P1 exige postmortem em até **5 dias úteis**, template `PM-2025`, **obrigatoriamente** registrado como ticket Helios tipo `Postmortem`. Inclui seção de custo evitado (horas de engenharia × R$ 280) e ação de atualização de runbook com dono e data.

## 8. Diff em relação à POL-SRE-014 (2024)

| Item | Mar/2024 | Ago/2025 |
|---|---|---|
| Início da semana | segunda 8h | segunda 9h |
| Ack P1 | 20 min | 15 min |
| Mitigação P1 | 60 min | 45 min |
| Canal | `#oncall-sre` | `#incidentes` |
| Adicional primário | R$ 500 | R$ 650 |
| Adicional secundário | R$ 180 | R$ 220 |
| Postmortem | 10 dias úteis, Confluence | 5 dias úteis, Helios |
| Semanas consecutivas máx. | 2 | 1 |
| Serviço RAG no escopo | não | sim |

## 9. Histórico

| Data | Mudança |
|---|---|
| 22/07/2025 | Aprovação REV2. |
| 01/08/2025 | Início de vigência. POL-SRE-014 (2024) arquivada. |
