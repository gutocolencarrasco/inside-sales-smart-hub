# Inside Sales Smart Hub V15

V15 transforma as filas em um fluxo comercial transacional, usando dados 100% fictícios.

## Filas / reports
- **Workflow:** Identify only
- **FUP:** Develop / Propose
- **Growth:** Filipe
- **Orders / Won:** Order Promised / Win Closed
- **Lost:** Lost Closed

## Regras de prioridade
Workflow e FUP são ordenados automaticamente por:
1. Priority Score (maior primeiro)
2. SLA mais crítico
3. Opportunity Value maior
4. Days Waiting maior

## Opportunity Editor
Ao clicar em uma linha de Workflow ou FUP, abre uma caixa de edição com:
- Main Item
- Quantity
- Unit Price
- Salesforce Stage
- Action
- Next FUP
- Description / Commercial Notes
- Cross Sell / Up Sell
- Optional Qty / Unit Price
- Generate Proposal / Revised Proposal

## Movimentação automática por Salesforce Stage
- Identify → Workflow
- Develop / Propose → FUP
- Order Promised / Win Closed → Orders / Won
- Lost Closed → Lost

Lost Closed é automaticamente retirado de Open Pipeline, Revenue at Risk e valores de oportunidades ativas.

## Salesforce synchronization concept
Toda alteração salva:
- atualiza a oportunidade no Smart Hub;
- cria um **Salesforce Call / Activity Ticket** rastreável;
- registra campos alterados (antes → depois);
- adiciona a atualização à fila **API-ready** para espelhamento no Salesforce.

A demonstração não afirma conexão real com ambientes Philips/Salesforce/SAP.

## OPP Open Date
Workflow e FUP exibem **OPP Open Date** como coluna não editável.

## Cenário
- 30 clientes Workflow por responsável
- 70 clientes FUP por responsável
- Clientes Workflow e FUP não se repetem no cenário inicial
- 400 oportunidades fictícias no cenário inicial
