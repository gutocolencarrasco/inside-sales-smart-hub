# Inside Sales Smart Hub V14.4

Cenário ampliado, com dados 100% fictícios e sem repetição de clientes entre Workflow e FUP.

## Volume por responsável
Para cada responsável — **Ana, Bruno, Carla e Filipe**:
- **30 clientes em Workflow**
- **70 clientes em FUP**
- **100 clientes ativos únicos por responsável**

Total do cenário:
- **120 clientes em Workflow**
- **280 clientes em FUP**
- **400 oportunidades/clientes ativos únicos**

## Governança de estágio
### Workflow
- Somente **Identify**
- OPP recém-criada pelo agente a partir de WhatsApp, E-mail ou Service Call
- FUP Status = Not Started
- Cliente ainda não entrou em negociação comercial

### FUP
- Somente **Develop** ou **Propose**
- Cliente já teve interação comercial
- Develop = desenvolvimento/negociação em andamento
- Propose = proposta enviada / negociação e follow-up
- Action editável
- Next FUP editável
- Proposal Review / Revised Proposal dentro do próprio FUP

## Integridade do cenário
Os nomes são gerados como clientes fictícios únicos. Nenhum cliente do Workflow é reutilizado no FUP.

Salesforce stages:
**Identify → Develop → Propose → Order Promised → Win Closed → Lost Closed**

## Hotfix
Corrigido erro de runtime no Render causado por uma regra legada que tentava acessar a coluna `Seller`.
O cenário V14.4 usa `Owner` e preserva exatamente 30 Workflow + 70 FUP por responsável.

## FIX2 — Inventory runtime error
Corrigido o erro:
`AttributeError: 'DataFrame' object has no attribute 'Inventory'`

Causa:
o cenário ampliado V14.4 não estava criando as colunas de drivers comerciais usadas pelo dashboard.

Correções:
- Revenue
- Conversion
- Inventory
- SLA
- Credit

Também foi adicionada compatibilidade com sessões antigas do Streamlit que ainda estejam em memória.
