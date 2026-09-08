# Inside Sales Smart Hub V12

Executive MVP demonstrativo para o business case de Inside Sales. **Todos os clientes, valores, produtos, scores e indicadores são 100% fictícios/anônimos.**

## V12 — principais evoluções
- Navegação principal reduzida para 5 módulos: **Executive Cockpit, Sales Workspace, Growth Engine, Account 360 e Management**.
- **VERSION 12** exibida permanentemente na barra lateral.
- Salesforce Pipeline redesenhado como mini cockpit compacto.
- Sales Workspace agrupa Opportunities, Smart Priority e Follow UP.
- Smart Workflow sem Next Best Action e com **Total Opportunity Value** incluindo Cross Sell / Up Sell.
- **Add to Proposal / Generate Proposal** somente em Identify / Develop; não aparecem em Propose ou superior.
- FUP exclusivamente em Follow UP; Active Prospecting exclusivamente em Growth Engine.
- Seller Performance Dashboard filtra **Today's Priorities** com **All, Ana, Bruno, Carla e Filipe**.
- Today's Priorities consolida New Opportunity, Follow UP, Active Prospecting e Proposal Review por responsável.
- Filipe: Commercial Assistant + OPPs Normal até R$10K + FUP dessas OPPs + Active Prospecting governado até R$50K.
- Proposta preserva item **OPCIONAL** e Review Proposal para negociação/revisão.

## Deploy
Build: `pip install -r requirements.txt`

Start: `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
