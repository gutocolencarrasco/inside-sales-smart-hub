# Inside Sales Smart Hub V14

Business Case demonstrativo para transformação da operação de Inside Sales.

## V14 — principais evoluções
- Plataforma multiagente com 5 agentes visíveis:
  - Filipe — AI Sales Assistant / Reactive Sales / FUP / Growth
  - CRM Agent — estrutura demanda e orquestra Salesforce
  - Priority Agent — score, SLA, conversion e routing
  - Operations Agent — integração SAP para estoque e crédito
  - Proposal Agent — pricing governado, Cross/Up Sell opcional e proposta
- Camada **API-ready** para Salesforce e SAP (demo sem alegar conexão real).
- Novo **Salesforce Demand Intake & Evolution**, incluindo descrição estruturada do chamado/demanda.
- Workflow preserva Cross Sell / Up Sell e Generate Proposal somente em Identify / Develop.
- FUP, Negotiation e Growth permanecem em filas próprias.
- Filipe: OPP Normal ≤ R$10K + FUP dessas OPPs + 30–50 Growth actions/dia com potencial ≤ R$50K.
- Growth Signal só vira Salesforce OPP após interação/interesse do cliente.
- Salesforce stages padronizados:
  **Identify → Develop → Propose → Order Promised → Win Closed → Lost Closed**
- Dashboard único com filtro **All | Ana | Bruno | Carla | Filipe**.
- Número **VERSION 14** visível na barra lateral.
- Dados 100% fictícios e anonimizados.

## Deploy Render
Build command:
`pip install -r requirements.txt`

Start command:
`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
