# Inside Sales Smart Hub V10

Executive MVP demonstrativo para o business case de Inside Sales. **Todos os clientes, valores, produtos, scores e indicadores são 100% fictícios/anônimos.**

## V10 — principais evoluções
- Executive Sales Cockpit inspirado no benchmark visual aprovado: navegação lateral, cards, gráficos, insights e painéis densos porém organizados.
- Linguagem executiva: AOP, Open Pipeline, AOP Attainment, Revenue at Risk, Growth Potential, Conversion Rate, Sales Efficiency, Next Best Action, Commercial Load Index.
- Seller Performance Dashboard individual por vendedor, além da visão consolidada do time.
- Filipe — Commercial Assistant disponível em todas as páginas e respondendo a perguntas com base nos dados fictícios do Smart Hub.
- Smart Workflow mais limpo: filtros Seller / Salesforce Stage, cards por estágio e painel 360° da oportunidade.
- Ações contextuais: Generate Opportunity, Add Cross / Up Sell e Generate Proposal.
- Proposal PDF funcional: sem List Price/desconto para cliente; Cross/Up Sell separado como opcional; gerar PDF não muda Salesforce Stage.
- Smart Priority: Priority Score numérico 0–100; Revenue, Conversion, Inventory, SLA e Credit classificados visualmente por cor.
- Conversion explicável: histórico do cliente 40%, produto/família 25%, recorrência 20%, maturidade 15%.
- Growth Engine com seller, filtro, Growth Funnel, Growth Potential e Generate Text sob demanda; sem preço na primeira abordagem.
- Follow UP Comercial corrigido e enriquecido com aging, FUP Today, Overdue FUP, Pipeline Awaiting Response e FUP Compliance.
- Salesforce stages: Identify → Develop → Propose → Order Promised / Lost Closed.
- Governança do Agente Autônomo e handoff por Commercial Load Index.

## Render
Build command:
`pip install -r requirements.txt`

Start command:
`streamlit run app.py --server.port $PORT --server.address 0.0.0.0`
