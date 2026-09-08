import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

st.set_page_config(page_title='Inside Sales Smart Hub V4', page_icon='⚡', layout='wide')

st.markdown('''
<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1500px}
.hero{background:linear-gradient(120deg,#071b33 0%,#0b4f8a 58%,#0d74c7 100%);padding:28px 30px;border-radius:20px;color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:38px;font-weight:700}.hero p{margin:8px 0 0;opacity:.92;font-size:17px}
.pill{display:inline-block;background:rgba(255,255,255,.14);padding:6px 10px;border-radius:999px;margin:12px 6px 0 0;font-size:12px}
.card{border:1px solid rgba(120,140,160,.22);border-radius:16px;padding:16px 18px;background:rgba(255,255,255,.03);min-height:130px}
.card h3{margin:0 0 8px;font-size:18px}.muted{opacity:.72;font-size:13px}.big{font-size:26px;font-weight:700}
[data-testid="stMetric"]{border:1px solid rgba(120,140,160,.18);padding:12px 14px;border-radius:14px}
</style>
''', unsafe_allow_html=True)

# ---------- DEMO DATA: 100% fictitious / anonymized ----------
CUSTOMERS = pd.DataFrame([
    ['Hospital Horizonte','Ana',1180000,1320000,890000,18,620000,175000,22,'Sudeste'],
    ['Rede Vida Nova','Bruno',940000,1010000,715000,27,520000,98000,39,'Sudeste'],
    ['Instituto Aurora','Carla',560000,625000,430000,9,260000,62000,71,'Sul'],
    ['Hospital Monte Azul','Ana',780000,735000,515000,14,350000,48000,93,'Nordeste'],
    ['Clínica Integra','Bruno',430000,510000,365000,7,190000,78000,31,'Centro-Oeste'],
    ['Grupo Santa Luz','Carla',1260000,1430000,960000,31,780000,210000,16,'Sudeste'],
    ['Hospital Nova Esperança','Ana',690000,755000,505000,12,310000,92000,58,'Sul'],
    ['Centro Médico Solaris','Bruno',350000,390000,250000,6,150000,18000,127,'Nordeste'],
    ['Rede Plena Saúde','Carla',870000,930000,640000,20,440000,135000,44,'Sudeste'],
    ['Hospital Parque Central','Ana',610000,675000,455000,11,285000,76000,36,'Centro-Oeste'],
], columns=['Cliente','Vendedor','Fat_2024','Fat_2025','Fat_2026_YTD','Base_Instalada','Limite_Credito','Credito_Livre','Dias_Ultima_Compra','Regiao'])

STOCK = pd.DataFrame([
    ['DMO-1001','Kit Preventivo Alpha','Peças',46,12,0,8900],
    ['DMO-1002','Sensor de Fluxo Pro','Sensores',18,24,4,12700],
    ['DMO-1003','Bateria Backup Plus','Acessórios',7,16,0,7600],
    ['DMO-1004','Módulo Eletrônico X','Módulos',3,9,2,21400],
    ['DMO-1005','Filtro Performance','Consumíveis',124,40,0,1850],
    ['DMO-1006','Válvula Inspiratória','Peças',0,18,6,9400],
    ['DMO-1007','Contrato Preventivo 12M','Serviços',999,0,0,32500],
    ['DMO-1008','Upgrade Performance','Upgrades',999,0,0,44800],
], columns=['SKU','Descricao','Familia','Estoque_Livre','Transito','Qualidade','Preco_Demo'])

BASE = pd.DataFrame([
    ['Hospital Horizonte','Equipamento A',10,2019,14,'DMO-1001'],['Hospital Horizonte','Equipamento B',8,2021,9,'DMO-1002'],
    ['Rede Vida Nova','Equipamento A',16,2018,17,'DMO-1001'],['Rede Vida Nova','Equipamento C',11,2020,13,'DMO-1003'],
    ['Instituto Aurora','Equipamento B',9,2021,15,'DMO-1002'],['Hospital Monte Azul','Equipamento A',14,2018,19,'DMO-1001'],
    ['Clínica Integra','Equipamento C',7,2022,8,'DMO-1003'],['Grupo Santa Luz','Equipamento A',19,2017,18,'DMO-1001'],
    ['Grupo Santa Luz','Equipamento C',12,2020,14,'DMO-1003'],['Hospital Nova Esperança','Equipamento B',12,2019,16,'DMO-1002'],
    ['Centro Médico Solaris','Equipamento A',6,2017,21,'DMO-1001'],['Rede Plena Saúde','Equipamento A',13,2019,12,'DMO-1001'],
    ['Rede Plena Saúde','Equipamento B',7,2021,11,'DMO-1002'],['Hospital Parque Central','Equipamento C',11,2020,15,'DMO-1003'],
], columns=['Cliente','Equipamento','Qtd','Ano_Instalacao','Meses_Desde_Compra','SKU_Recorrente'])

QUOTES = pd.DataFrame([
    [81001,'Hospital Horizonte','DMO-1001','Kit Preventivo Alpha','Ana',186000,.92,1.1,'Aprovado','Novo'],
    [81002,'Rede Vida Nova','DMO-1002','Sensor de Fluxo Pro','Bruno',74000,.78,3.2,'Aprovado','Follow-up D+2'],
    [81003,'Instituto Aurora','DMO-1005','Filtro Performance','Carla',29500,.84,5.8,'Aprovado','Follow-up vencido'],
    [81004,'Hospital Monte Azul','DMO-1004','Módulo Eletrônico X','Ana',128000,.64,4.7,'Revisar','Crédito'],
    [81005,'Clínica Integra','DMO-1003','Bateria Backup Plus','Bruno',68000,.88,1.6,'Aprovado','Novo'],
    [81006,'Grupo Santa Luz','DMO-1007','Contrato Preventivo 12M','Carla',215000,.72,2.4,'Aprovado','Negociação'],
    [81007,'Hospital Nova Esperança','DMO-1001','Kit Preventivo Alpha','Ana',99000,.86,6.2,'Aprovado','Follow-up vencido'],
    [81008,'Centro Médico Solaris','DMO-1006','Válvula Inspiratória','Bruno',47000,.55,7.1,'Bloqueado','Estoque'],
    [81009,'Rede Plena Saúde','DMO-1002','Sensor de Fluxo Pro','Carla',83000,.81,2.0,'Aprovado','Novo'],
    [81010,'Hospital Parque Central','DMO-1008','Upgrade Performance','Ana',152000,.69,3.8,'Aprovado','Proposta'],
], columns=['OPP','Cliente','SKU','Produto','Vendedor','Valor','Prob','SLA_h','Credito','Etapa'])

def brl(v): return f"R$ {v:,.0f}".replace(',', 'X').replace('.', ',').replace('X','.')

def enrich(q):
    q=q.merge(STOCK[['SKU','Estoque_Livre','Transito']],on='SKU',how='left')
    q['S_Receita']=np.clip(q['Valor']/180000*100,10,100)
    q['S_Conversao']=q['Prob']*100
    q['S_Estoque']=np.where(q['Estoque_Livre']>0,np.clip(q['Estoque_Livre']*8,25,100),5)
    q['S_SLA']=np.clip(4/np.maximum(q['SLA_h'],.2)*100,10,100)
    q['S_Credito']=q['Credito'].map({'Aprovado':100,'Revisar':45,'Bloqueado':5}).fillna(40)
    q['Score']=(q.S_Receita*.30+q.S_Conversao*.25+q.S_Estoque*.20+q.S_SLA*.15+q.S_Credito*.10).round().astype(int)
    q['Prioridade']=np.select([q.Score>=80,q.Score>=65],['P1 • Atacar agora','P2 • Alta'],default='P3 • Normal')
    return q.sort_values(['Score','Valor'],ascending=False)

Q=enrich(QUOTES.copy())

def growth_engine():
    g=BASE.merge(CUSTOMERS[['Cliente','Vendedor','Credito_Livre','Dias_Ultima_Compra','Fat_2025','Fat_2026_YTD']],on='Cliente',how='left')
    g=g.merge(STOCK[['SKU','Descricao','Estoque_Livre','Preco_Demo']],left_on='SKU_Recorrente',right_on='SKU',how='left')
    g['Idade_Parque']=2026-g['Ano_Instalacao']
    g['Growth_Score']=((g.Meses_Desde_Compra>=12)*35+(g.Idade_Parque>=5)*25+(g.Credito_Livre>30000)*15+(g.Estoque_Livre>0)*15+(g.Dias_Ultima_Compra>45)*10).astype(int)
    g['Potencial_Demo']=(g.Qtd*np.minimum(g.Preco_Demo,11000)*.72).round(-2)
    g['Acao_Sugerida']=np.where(g.Meses_Desde_Compra>=12,'Reativar + oferecer item recorrente','Avaliar cross-sell')
    return g.sort_values(['Growth_Score','Potencial_Demo'],ascending=False)
G=growth_engine()

st.markdown('''<div class="hero"><h1>Inside Sales Smart Hub V4</h1><p>From Reactive Requests to Intelligent Revenue Growth</p><span class="pill">SMART WORKFLOW</span><span class="pill">SMART PRIORITY</span><span class="pill">SMART GROWTH</span></div>''',unsafe_allow_html=True)
st.caption('MVP demonstrativo • Todos os clientes, CNPJs, SKUs, oportunidades, volumes e valores exibidos são fictícios e anonimizados.')

page=st.sidebar.radio('Navegação',['Central de Decisão','Smart Workflow','Fila Inteligente','Account 360','Growth Engine','Cockpit do Coordenador','Arquitetura & Automação','Modo Apresentação'])
st.sidebar.markdown('---'); st.sidebar.metric('Operação','600 orçamentos/mês','≈ 30/dia útil'); st.sidebar.metric('Time','3 colaboradores'); st.sidebar.caption('Business Case • dados demonstrativos')

if page=='Central de Decisão':
    st.subheader('O que precisa da minha atenção agora?')
    p1=Q[Q.Score>=80]; late=Q[Q.SLA_h>4]; stockrisk=Q[Q.Estoque_Livre<=3]
    c1,c2,c3,c4=st.columns(4)
    c1.metric('P1 • atacar agora',len(p1),brl(p1.Valor.sum()))
    c2.metric('Fora do SLA',len(late),brl(late.Valor.sum()))
    c3.metric('Receita em risco',brl(stockrisk.Valor.sum()),'estoque/abastecimento')
    c4.metric('Growth identificado',brl(G[G.Growth_Score>=70].Potencial_Demo.sum()),f"{len(G[G.Growth_Score>=70])} sinais")
    st.markdown('### Próximas melhores ações')
    view=Q[['OPP','Cliente','Vendedor','Produto','Valor','Score','Prioridade','SLA_h','Etapa']].head(6).copy()
    st.dataframe(view,use_container_width=True,hide_index=True)
    st.info('A fila deixa de ser cronológica: o vendedor recebe primeiro as oportunidades com maior combinação de potencial, conversão, disponibilidade, SLA e crédito.')

elif page=='Smart Workflow':
    st.subheader('Smart Workflow — preparar a oportunidade antes de chegar ao vendedor')
    st.markdown('**Entrada → Identificação → Validação → Enriquecimento → Priorização → Cadência → Gestão**')
    c1,c2,c3=st.columns(3)
    c1.markdown('<div class="card"><h3>1. Capturar</h3><div class="big">E-mail / WhatsApp / CRM</div><p class="muted">Extrair cliente, CNPJ, OPP, SKU, quantidade, valor e prazo.</p></div>',unsafe_allow_html=True)
    c2.markdown('<div class="card"><h3>2. Enriquecer</h3><div class="big">Cliente + Estoque</div><p class="muted">Cruzar histórico, base instalada, crédito e disponibilidade.</p></div>',unsafe_allow_html=True)
    c3.markdown('<div class="card"><h3>3. Executar</h3><div class="big">Score + Follow-up</div><p class="muted">Priorizar, sugerir resposta e criar próxima ação com SLA.</p></div>',unsafe_allow_html=True)
    st.markdown('### Simulação de nova solicitação')
    a,b,c=st.columns(3); cli=a.selectbox('Cliente',CUSTOMERS.Cliente); sku=b.selectbox('SKU',STOCK.SKU); val=c.number_input('Valor demonstrativo',1000,500000,58000,1000)
    if st.button('Processar solicitação'):
        s=STOCK[STOCK.SKU==sku].iloc[0]; ac=CUSTOMERS[CUSTOMERS.Cliente==cli].iloc[0]
        st.success(f"Cliente identificado • {int(ac.Base_Instalada)} equipamentos na base • estoque livre do SKU: {int(s.Estoque_Livre)} • crédito livre demonstrativo: {brl(ac.Credito_Livre)}")
        st.write('**Próxima ação sugerida:** criar/atualizar oportunidade, calcular prioridade e programar follow-up D+2.')

elif page=='Fila Inteligente':
    st.subheader('Smart Priority — trabalhar a oportunidade certa no momento certo')
    st.dataframe(Q[['OPP','Cliente','Produto','Vendedor','Valor','Prob','Estoque_Livre','SLA_h','Credito','Score','Prioridade']],use_container_width=True,hide_index=True)
    st.caption('Score demonstrativo: Receita 30% • Conversão 25% • Estoque 20% • SLA 15% • Crédito 10%. Pesos calibráveis com histórico real.')

elif page=='Account 360':
    st.subheader('Account 360 — contexto comercial em uma única tela')
    cli=st.selectbox('Selecione o cliente',CUSTOMERS.Cliente.tolist()); a=CUSTOMERS[CUSTOMERS.Cliente==cli].iloc[0]; b=BASE[BASE.Cliente==cli]; q=Q[Q.Cliente==cli]
    c1,c2,c3,c4,c5=st.columns(5); c1.metric('Fat. 2025',brl(a.Fat_2025)); c2.metric('2026 YTD',brl(a.Fat_2026_YTD)); c3.metric('Base instalada',int(a.Base_Instalada)); c4.metric('Crédito livre',brl(a.Credito_Livre)); c5.metric('Última compra',f"{int(a.Dias_Ultima_Compra)} dias")
    st.markdown('#### Base instalada / recorrência'); st.dataframe(b,use_container_width=True,hide_index=True)
    st.markdown('#### Oportunidades abertas'); st.dataframe(q[['OPP','Produto','Valor','Score','Prioridade','Etapa']],use_container_width=True,hide_index=True)
    insights=[]
    if a.Dias_Ultima_Compra>60: insights.append('Cliente com janela de reativação.')
    if len(b) and (b.Meses_Desde_Compra>=12).any(): insights.append('Há recorrência de compra vencida na base instalada.')
    if a.Fat_2026_YTD < a.Fat_2025*.65: insights.append('Ritmo de faturamento abaixo da referência demonstrativa.')
    st.info(' **Smart Insights:** ' + (' '.join(insights) if insights else 'Conta sem alerta crítico; avaliar cross-sell.'))
    if st.button('GERAR NOVA OPORTUNIDADE'): st.success('Oportunidade demonstrativa preparada para validação humana antes da criação definitiva no CRM.')

elif page=='Growth Engine':
    st.subheader('Smart Growth — não esperar o próximo chamado chegar')
    hi=G[G.Growth_Score>=70]
    c1,c2,c3=st.columns(3); c1.metric('Sinais de alta aderência',len(hi)); c2.metric('Potencial demonstrativo',brl(hi.Potencial_Demo.sum())); c3.metric('Contas mapeadas',hi.Cliente.nunique())
    st.dataframe(G[['Cliente','Vendedor','Equipamento','Qtd','Meses_Desde_Compra','Descricao','Estoque_Livre','Growth_Score','Potencial_Demo','Acao_Sugerida']],use_container_width=True,hide_index=True)
    st.success('Motor proativo cruza base instalada + recência + estoque + crédito + comportamento para sugerir reativação, cross-sell e upsell.')

elif page=='Cockpit do Coordenador':
    st.subheader('Cockpit do Coordenador — produtividade, conversão e coaching')
    perf=Q.groupby('Vendedor').agg(Oportunidades=('OPP','count'),Pipeline=('Valor','sum'),Score_Medio=('Score','mean'),SLA_Medio=('SLA_h','mean'),Conversao=('Prob','mean')).reset_index(); perf['Conversao']=perf.Conversao*100
    st.dataframe(perf,use_container_width=True,hide_index=True)
    for _,r in perf.iterrows():
        if r.SLA_Medio>4: st.warning(f"{r.Vendedor}: revisar carga e redistribuir oportunidades; SLA médio {r.SLA_Medio:.1f}h.")
        elif r.Conversao<70: st.info(f"{r.Vendedor}: coaching em qualificação e follow-up.")
        else: st.success(f"{r.Vendedor}: desempenho equilibrado; manter cadência e explorar Growth Engine.")

elif page=='Arquitetura & Automação':
    st.subheader('Como deixar a operação automatizada')
    st.markdown('''
**Camada 1 — Entradas:** e-mail, WhatsApp e solicitações já registradas no CRM.  
**Camada 2 — Dados:** Salesforce/CRM + ERP/SAP (estoque) + histórico de pedidos/faturamento + base instalada.  
**Camada 3 — Orquestração:** regras de identificação, deduplicação, SLA, score, cadência e Growth Engine.  
**Camada 4 — IA assistiva:** extração de dados, resumo da conta, sugestão de resposta e próxima melhor ação.  
**Camada 5 — Governança:** vendedor valida decisão comercial; crédito, pricing excepcional e criação definitiva de cliente permanecem sob aprovação humana.
''')
    st.markdown('### Automação proposta')
    flow=pd.DataFrame([
        ['1','Nova solicitação','Captura automática','Cliente/CNPJ/OPP/SKU/valor identificados'],['2','Match da conta','CRM','Conta existente ou pré-cadastro'],['3','Enriquecimento','CRM + ERP','Histórico, base instalada, crédito e estoque'],['4','Priorização','Motor de regras','Commercial Priority Score'],['5','Execução','IA assistiva','Resposta sugerida + próxima melhor ação'],['6','Cadência','CRM/Flow','Follow-up D+2 / D+5 + alerta'],['7','Gestão','Dashboard','SLA, conversão, pipeline, revenue at risk e growth']
    ],columns=['Etapa','Evento','Motor','Saída'])
    st.dataframe(flow,use_container_width=True,hide_index=True)
    st.warning('Princípio de governança: automatizar preparação e priorização; não automatizar decisões financeiras ou exceções comerciais sem aprovação humana.')

elif page=='Modo Apresentação':
    st.subheader('Roteiro de 20 minutos')
    st.markdown('''
**0–3 min • Diagnóstico** — 600 orçamentos/mês, ~30/dia, 3 pessoas e operação predominantemente reativa.  
**3–5 min • Visão** — Smart Workflow + Smart Priority + Smart Growth.  
**5–9 min • Workflow** — reduzir trabalho operacional e tempo até o primeiro contato.  
**9–12 min • Priority** — substituir fila cronológica por fila de impacto.  
**12–15 min • Growth** — criar oportunidades antes do chamado.  
**15–18 min • Demo** — Central → Account 360 → Growth Engine.  
**18–20 min • 30 dias + KPIs** — provar impacto e calibrar a solução.
''')
    st.markdown('### Primeiros 30 dias')
    plan=pd.DataFrame([['Dias 1–5','Baseline + SLA','Mapear funil, tempos e perdas'],['Dias 6–10','Fila inteligente piloto','Score inicial + gestão diária'],['Dias 11–20','Cadência + cockpit','Follow-up e gestão por exceção'],['Dias 21–30','Growth Engine piloto','Reativação/cross-sell em contas selecionadas']],columns=['Período','Prioridade','Entrega'])
    st.dataframe(plan,use_container_width=True,hide_index=True)
    st.markdown('**KPIs:** tempo até primeiro contato • % dentro do SLA • conversão • ciclo de vendas • oportunidades/rep • follow-up compliance • oportunidades proativas • receita incremental • revenue at risk.')

st.markdown('---'); st.caption('Inside Sales Smart Hub V4 • MVP demonstrativo • dados 100% fictícios e anonimizados • lógica inspirada na estrutura operacional, sem exposição de informações comerciais reais')
