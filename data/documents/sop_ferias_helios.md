# SOP — solicitar férias no Helios

**Documento:** PEO-SOP-FER-012  
**Vigência:** 03/02/2026  
**Owner:** People Operations  
**Sistemas:** Helios módulo Time Off, folha TOTVS  
**Classificação:** interno — todos os CLT Aurora Tech

Procedimento para o colaborador e para o gestor. A política de direito (30 dias corridos, terço, parcelamento) está no Manual interno; **este SOP só ensina a operar o sistema**. Conflitos de regra: prevalece o Manual + CLT, não um print antigo do Helios.

## 1. Quem pode abrir o pedido

CLT com **12 meses de período aquisitivo completo** ou saldo em aberto no extrato Helios. PJ / estágio: não usam este SOP (contrato próprio). Período de experiência: People recusa o workflow automaticamente.

Antecedência mínima: **30 dias corridos** antes do primeiro dia de descanso. Exceção médica (atestado + INSS) abre chamado People, não este fluxo.

## 2. Passo a passo do colaborador

1. Acesse Helios → **Time Off** → **Novo pedido** → tipo `Férias`.  
2. Confira o saldo. O terço constitucional é calculado na prévia; o valor só fecha na folha.  
3. Escolha datas. Regras de UI:  
   - 1 período: 30 dias; ou  
   - 2 períodos: um deles ≥ 14 dias; soma = 30.  
   - Não cruce dois períodos aquisitivos no mesmo pedido.  
4. Indique substituto operacional (campo obrigatório para Engenharia, CS e Comercial). SRE em semana de plantão: o Helios bloqueia se você for primário na POL vigente; troque a escala **antes** (People não altera PagerDuty).  
5. Anexe apenas se Folha pedir (ex.: abono pecuário — a Aurora **não** pratica abono de 1/3 vender férias como padrão; o campo existe mas People recusa).  
6. Envie. SLA de resposta People: **5 dias úteis**. Gestor tem 3 dias úteis no primeiro degrau.

Não envie e-mail paralelo. Não use o módulo antigo “Férias 2023” (desligado).

## 3. Passo a passo do gestor

1. Fila Helios → **Aprovações**.  
2. Verifique cobertura: para Engenharia, cruzar com escala SRE (plantão começa segunda 9h desde ago/2025).  
3. Recusar com motivo visível ao colaborador (texto ≥ 20 caracteres).  
4. Aprovar dispara Folha: pagamento do terço **até 2 dias úteis antes** do início. Se Folha estiver em cutoff (dia 20–23), o Helios alerta; remarque o início.

## 4. Folha e valores (referência operacional)

- Adicional de 1/3 sobre a remuneração de férias, inclusive média de horas extras dos 12 meses e adicional de plantão **se habitual** (≥ 8 semanas no aquisitivo). O valor de plantão a considerar é o da política **da época do trabalho**: semanas em 2024 a R$ 500, a partir de ago/2025 a **R$ 650**.  
- Vale-refeição Flash: não é pago nos 30 dias de férias (crédito zerado no período).  
- Plano Unimed permanece. Coparticipação 20% inalterada.

## 5. Home office e ponto

Férias não exigem check-in híbrido (terça–quinta no escritório). Banco de horas: saldo deve ser zerado no trimestre; férias **não** zeram banco automaticamente — o gestor trata horas extras antes do pedido.

## 6. Cancelamento e alteração

Até 15 dias do início: colaborador solicita `Alterar férias`. Depois disso: só People + Folha, com risco de terço já pago (devolução em folha seguinte). P1 de sistema no go-live de cliente **não** cancela férias já pagas.

## 7. Falhas conhecidas do Helios 4.18

O batch `payroll.batch_v2` (incidente P1-2026-041) corrompeu prévias de férias em maio/2026 por 71 min. Se o extrato mostrar saldo negativo absurdo, **não** recarregue o pedido: abra ticket People com print e timestamp. O recálculo é job Atlas `dim_employee`, não botão do usuário.

## 8. Indicadores People (Q2 2026)

Pedidos abertos: 41. Tempo mediano de aprovação gestor: 1,8 dia útil. Recusas por antecedência < 30 dias: 6. Pedidos de SRE conflitantes com plantão: 2 (ambos recusados pela regra de bloqueio).
