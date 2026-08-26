# Política de plantão de engenharia — Aurora Tech

**Documento:** POL-SRE-014  
**Vigência:** 01/03/2024 a 31/07/2025  
**Substitui:** POL-SRE-011 (2022)  
**Elaboração:** SRE / Engenharia de Plataforma  
**Aprovação:** CTO, 18/02/2024  
**Classificação:** interno

Este documento define o modelo de plantão (on-call) da Aurora Tech para serviços em produção. A versão vigente a partir de agosto de 2025 é a POL-SRE-014-REV2; **não use esta revisão para calcular adicional, SLA de P1 ou janela de cobertura após 31/07/2025**.

## 1. Objetivo e escopo

Cobrir disponibilidade dos produtos Helios (RH), Atlas (data plane) e Nimbus (API pública de clientes). Não cobre plantão comercial nem suporte N1 de Helpdesk.

## 2. Janela de cobertura (vigência 2024)

O plantão semanal começa na **segunda-feira às 8h** (horário de Brasília) e termina na segunda seguinte às 8h. Há um plantonista primário e um secundário (shadow). O secundário só é acionado se o primário não reconhecer o alerta em 10 minutos.

Sexta-feira o expediente interno pode encerrar às 17h, mas o plantão **não** encerra. Feriados nacionais entram na escala normalmente; não há overstaffing automático.

## 3. Severidade e tempos de resposta (2024)

| Severidade | Definição | Reconhecimento | Mitigação inicial | Comunicação ao cliente |
|---|---|---|---|---|
| P1 | Indisponibilidade total de Helios, Atlas ou Nimbus, ou perda de dados | 20 minutos | 60 minutos | 45 minutos |
| P2 | Degradação > 30% de latência p95 ou erro 5xx > 2% por 15 min | 40 minutos | 4 horas | 2 horas |
| P3 | Falha localizada, workaround conhecido | 4 horas úteis | próximo dia útil | sob demanda |
| P4 | Ruído / melhoria | backlog | backlog | não |

O canal oficial de P1/P2 em 2024 é `#oncall-sre`. O bot PagerDuty envia SMS e ligação. **Não** use `#incidentes` nesta vigência — o canal só foi padronizado na revisão de 2025.

## 4. Compensação

- Adicional de plantão: **R$ 500,00** por semana completa, pago na folha do mês seguinte.
- Chamado P1 atendido fora do expediente: hora extra 100% sobre a hora base, além do adicional semanal.
- Plantonista secundário: **R$ 180,00** por semana, sem hora extra salvo acionamento real.
- Não há adicional proporcional para cobertura parcial inferior a 48h; nesse caso a semana é reatribuída.

## 5. Ferramentas obrigatórias na escala 2024

1. PagerDuty (integração Datadog → PD).  
2. VPN WireGuard perfil `sre-prod`.  
3. Runbooks no Confluence espaço `SRE/2024` (não no Helios).  
4. Acesso break-glass via cofre HashiCorp Vault path `prod/sre`.

Grafana e o canal Slack `#incidentes` **não** são requisitos desta revisão.

## 6. Rotação e saúde da escala

Máximo de **2 semanas consecutivas** de primário. Após 3 semanas de plantão no trimestre, o gestor deve realocar. Médicos atestados de burnout ou sono interrompido (>3 noites com P1) geram isenção da escala por 30 dias.

Headcount SRE em março/2024: 6 engenheiros aptos à escala. Cobertura teórica: 6 semanas de ciclo. Folga média entre plantões: 5 semanas.

## 7. Pós-incidente (2024)

P1 exige postmortem em até **10 dias úteis**, template `PM-2024`. Blameless, mas sem a seção de “custo evitado” (incluída só em 2025). O postmortem é arquivado no Confluence; não há obrigatoriedade de ticket no Helios.

## 8. Histórico de alterações

| Data | Mudança |
|---|---|
| 18/02/2024 | Publicação. Ack P1 = 20 min. Adicional R$ 500. Canal `#oncall-sre`. |
| 01/03/2024 | Início de vigência. |

**Fim da vigência desta revisão: 31/07/2025.**
