import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak

st.set_page_config(page_title='Inside Sales Smart Hub V7', page_icon='⚡', layout='wide')

st.markdown('''
<style>
.block-container{padding-top:1.2rem;padding-bottom:2rem;max-width:1500px}
.hero{background:linear-gradient(120deg,#071b33 0%,#0b4f8a 58%,#0d74c7 100%);padding:28px 30px;border-radius:20px;color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:38px;font-weight:700}.hero p{margin:8px 0 0;opacity:.92;font-size:17px}
.pill{display:inline-block;background:rgba(255,255,255,.14);padding:6px 10px;border-radius:999px;margin:12px 6px 0 0;font-size:12px}
.card{border:1px solid rgba(120,140,160,.22);border-radius:16px;padding:16px 18px;background:rgba(255,255,255,.03);min-height:130px}
.card h3{margin:0 0 8px;font-size:18px}.muted{opacity:.72;font-size:13px}.big{font-size:26px;font-weight:700}
[data-testid="stMetric"]{border:1px solid rgba(120,140,160,.18);padding:12px 14px;border-radius:14px}
[data-testid="stSidebar"] [data-testid="stMetricValue"]{font-size:24px!important;white-space:normal!important;line-height:1.15!important}
[data-testid="stSidebar"] [data-testid="stMetricLabel"]{font-size:13px!important}
.step-ok{border:1px solid #b7e4c7;background:#f1fbf4;border-radius:12px;padding:12px 14px;margin:7px 0}
.reco{border-left:5px solid #0d74c7;background:rgba(13,116,199,.07);padding:16px 18px;border-radius:10px;margin-top:14px}
.scorebox{font-size:30px;font-weight:800;color:#0b4f8a}
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
    ['DMO-1001','Kit Preventivo Alpha','Peças',46,12,0,16400,.18,7350],
    ['DMO-1002','Sensor de Fluxo Pro','Sensores',18,24,4,23800,.15,10150],
    ['DMO-1003','Bateria Backup Plus','Acessórios',7,16,0,14200,.12,6100],
    ['DMO-1004','Módulo Eletrônico X','Módulos',3,9,2,39600,.10,18800],
    ['DMO-1005','Filtro Performance','Consumíveis',124,40,0,3450,.20,1350],
    ['DMO-1006','Válvula Inspiratória','Peças',0,18,6,17600,.16,7700],
    ['DMO-1007','Contrato Preventivo 12M','Serviços',999,0,0,48500,.08,21400],
    ['DMO-1008','Upgrade Performance','Upgrades',999,0,0,72800,.10,32600],
], columns=['SKU','Descricao','Familia','Estoque_Livre','Transito','Qualidade','Preco_Lista','Desconto_Max','COGS_Demo'])
STOCK['Preco_Demo']=(STOCK['Preco_Lista']*(1-STOCK['Desconto_Max'])).round(2)

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

def brl2(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X','.')

def growth_for_customer(cliente, requested_sku):
    base_cli=BASE[BASE.Cliente==cliente]
    candidates=[]
    for _, row in base_cli.iterrows():
        if row.SKU_Recorrente != requested_sku and row.Meses_Desde_Compra >= 12:
            prod=STOCK[STOCK.SKU==row.SKU_Recorrente]
            if len(prod) and int(prod.iloc[0].Estoque_Livre)>0:
                p=prod.iloc[0]
                candidates.append({
                    'tipo':'CROSS-SELL','sku':p.SKU,'produto':p.Descricao,
                    'motivo':f"Base instalada com {int(row.Qtd)} equipamentos e recorrência há {int(row.Meses_Desde_Compra)} meses.",
                    'score':92,'qtd':max(1,min(5,int(round(row.Qtd*.25))))
                })
    upsell_map={'DMO-1001':'DMO-1007','DMO-1002':'DMO-1008','DMO-1003':'DMO-1008','DMO-1005':'DMO-1001'}
    upsku=upsell_map.get(requested_sku)
    if upsku:
        p=STOCK[STOCK.SKU==upsku].iloc[0]
        candidates.append({'tipo':'UPSELL','sku':p.SKU,'produto':p.Descricao,
                           'motivo':'Alternativa de maior valor associada ao perfil demonstrativo da conta e à base instalada.',
                           'score':78,'qtd':1})
    if not candidates:
        available=STOCK[(STOCK.SKU!=requested_sku)&(STOCK.Estoque_Livre>0)].copy()
        p=available.sort_values(['Preco_Lista','Estoque_Livre'],ascending=[False,False]).iloc[0]
        candidates.append({'tipo':'CROSS-SELL','sku':p.SKU,'produto':p.Descricao,
                           'motivo':'Produto complementar identificado pelo perfil demonstrativo da conta.',
                           'score':65,'qtd':1})
    return sorted(candidates,key=lambda x:x['score'],reverse=True)[0]

def generate_proposal_pdf(cliente, vendedor, items, proposta_no):
    buf=BytesIO()
    doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=18*mm,leftMargin=18*mm,topMargin=15*mm,bottomMargin=15*mm)
    styles=getSampleStyleSheet()
    title=ParagraphStyle('title2',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=18,textColor=colors.HexColor('#0877BE'),alignment=TA_CENTER,spaceAfter=8)
    h=ParagraphStyle('h',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=10,textColor=colors.HexColor('#0877BE'),spaceBefore=8,spaceAfter=5)
    body=ParagraphStyle('body2',parent=styles['BodyText'],fontSize=9,leading=12)
    small=ParagraphStyle('small',parent=styles['BodyText'],fontSize=7.5,leading=10,textColor=colors.HexColor('#555555'))
    story=[]
    story.append(Paragraph('SMART HUB - PROPOSTA COMERCIAL DEMONSTRATIVA',title))
    story.append(Paragraph('<b>DADOS 100% FICTÍCIOS / NÃO UTILIZAR COM CLIENTES</b>',ParagraphStyle('warn',parent=body,textColor=colors.HexColor('#B42318'),alignment=TA_CENTER)))
    story.append(Spacer(1,6*mm))
    date=datetime.now().strftime('%d/%m/%Y')
    story.append(Paragraph(f'<b>Proposta Nº:</b> {proposta_no}<br/><b>Data:</b> {date}<br/><b>CLIENTE:</b> {cliente}<br/><b>CNPJ:</b> 00.000.000/0000-00<br/><b>ENDEREÇO:</b> Endereço demonstrativo - São Paulo/SP',body))
    story.append(Spacer(1,5*mm))
    total=sum(i['qtd']*i['unit'] for i in items)
    desc=' + '.join([f"{i['produto']} - {i['qtd']} unidade(s)" for i in items])
    box=Table([[Paragraph(f'<b>{desc}</b>',body)],[Paragraph(f'<b>VALOR TOTAL DA VENDA: {brl2(total)}</b>',body)]],colWidths=[170*mm])
    box.setStyle(TableStyle([('BOX',(0,0),(-1,-1),1.5,colors.HexColor('#245A7D')),('ALIGN',(0,0),(-1,-1),'CENTER'),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('TOPPADDING',(0,0),(-1,-1),9),('BOTTOMPADDING',(0,0),(-1,-1),9)]))
    story.append(box)
    story.append(Spacer(1,5*mm))
    story.append(Paragraph('Temos o prazer de encaminhar esta proposta demonstrativa. As condições comerciais foram calculadas automaticamente pelo Smart Workflow com política fictícia de lista de preços e desconto.',body))
    story.append(Spacer(1,4*mm))
    story.append(Paragraph(f'Atenciosamente,<br/><b>{vendedor}</b><br/>Inside Sales - Demonstração',body))
    story.append(PageBreak())
    story.append(Paragraph('DESCRIÇÃO COMPLETA DOS ITENS - DEMONSTRAÇÃO',title))
    data=[['Código','Descrição','Qtde','Preço Lista','Desconto','Valor Unit.','Valor Total']]
    for i in items:
        data.append([i['sku'],i['produto'],str(i['qtd']),brl2(i['list_price']),f"{i['discount']*100:.0f}%",brl2(i['unit']),brl2(i['unit']*i['qtd'])])
    data.append(['','','','','','TOTAL',brl2(total)])
    tbl=Table(data,colWidths=[20*mm,48*mm,13*mm,24*mm,18*mm,24*mm,25*mm],repeatRows=1)
    tbl.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#EAF5FB')),('TEXTCOLOR',(0,0),(-1,0),colors.HexColor('#123A56')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTNAME',(-2,-1),(-1,-1),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),.5,colors.HexColor('#9DB6C6')),('FONTSIZE',(0,0),(-1,-1),7.5),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('ALIGN',(2,1),(-1,-1),'RIGHT'),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
    story.append(tbl)
    story.append(Paragraph('CONDIÇÃO DE PAGAMENTO',h))
    story.append(Paragraph(f'Pagamento demonstrativo em 01 parcela em até 30 dias do faturamento. Valor total: <b>{brl2(total)}</b>. Condição sujeita a validação de crédito na operação real.',body))
    story.append(Paragraph('PRAZO DE ENTREGA',h))
    story.append(Paragraph('Disponibilidade demonstrativa validada no Smart Workflow. Na operação real, o prazo deve ser confirmado no ato do pedido.',body))
    story.append(Paragraph('VALIDADE DO PREÇO E DA PROPOSTA',h))
    story.append(Paragraph('30 dias corridos a partir da data de emissão, exclusivamente para fins de demonstração do Business Case.',body))
    story.append(Paragraph('OBSERVAÇÕES',h))
    story.append(Paragraph('Valores, clientes, produtos, descontos, CNPJ e demais informações são fictícios e anonimizados. A automação de pricing deve respeitar alçadas e governança comercial reais antes de qualquer uso produtivo.',small))
    doc.build(story)
    return buf.getvalue()

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
SF_STAGES=['Identify','Develop','Propose','Order Promised','Lost Closed']

def build_v8_queue():
    w=Q.copy().reset_index(drop=True)
    w['Status SF']=['Identify','Propose','Propose','Develop','Identify','Develop','Propose','Propose','Identify','Propose']
    w['Próxima Ação']=['Qualificar demanda','Follow-up D+2','Follow-up vencido','Validar crédito','Qualificar demanda','Preparar proposta','Follow-up D+10','Validar disponibilidade','Qualificar demanda','Aguardar retorno']
    w['Incluir']=False
    w['Gerar proposta']=False
    desc=[]; vals=[]; types=[]; skus=[]; qtds=[]
    for _,r in w.iterrows():
        g=growth_for_customer(r.Cliente,r.SKU)
        p=STOCK[STOCK.SKU==g['sku']].iloc[0]
        v=float(p.Preco_Demo*g['qtd'])
        desc.append(f"{g['tipo']}: {g['produto']} • {g['qtd']} un. • +{brl(v)}")
        vals.append(v); types.append(g['tipo']); skus.append(g['sku']); qtds.append(g['qtd'])
    w['Cross Sell / Upsell']=desc; w['Growth_Value']=vals; w['Growth_Type']=types; w['Growth_SKU']=skus; w['Growth_Qtd']=qtds
    return w

if 'v8_queue' not in st.session_state: st.session_state.v8_queue=build_v8_queue()
if 'fup_comments' not in st.session_state:
    st.session_state.fup_comments={81002:'Compras avaliando internamente.',81003:'Sem retorno após último contato.',81007:'Retornar com área técnica.',81008:'Aguardando disponibilidade.',81010:'Proposta em avaliação.'}
W=st.session_state.v8_queue

def gauge(name,score,pipeline,growth):
    return f"<div class='card' style='text-align:center;min-height:230px'><h3>{name}</h3><div style='font-size:46px;font-weight:800;color:#0b4f8a'>{score}</div><div class='muted'>Índice de Performance / 100</div><progress value='{score}' max='100' style='width:90%;height:22px'></progress><p><b>Pipeline:</b> {brl(pipeline)}<br><b>Receita incremental:</b> {brl(growth)}</p></div>"

st.markdown("""<div class="hero"><h1>Inside Sales Smart Hub V8</h1><p>From Reactive Requests to Intelligent Revenue Growth</p><span class="pill">SMART WORKFLOW</span><span class="pill">SMART PRIORITY</span><span class="pill">SMART GROWTH</span><span class="pill">FOLLOW-UP</span></div>""",unsafe_allow_html=True)
st.caption('MVP demonstrativo • Todos os dados exibidos são fictícios e anonimizados.')

page=st.sidebar.radio('Navegação',['Central de Decisão','Smart Workflow','Follow-up Comercial','Fila Inteligente','Account 360','Growth Engine','Performance Comercial do Time','Arquitetura & Automação','Modo Apresentação'])
st.sidebar.markdown('---'); st.sidebar.metric('Operação','600 orçamentos/mês','≈ 30/dia útil'); st.sidebar.metric('Time','3 colaboradores'); st.sidebar.caption('Business Case • dados demonstrativos')

if page=='Central de Decisão':
    st.subheader('Central de Decisão')
    active=W[~W['Status SF'].isin(['Order Promised','Lost Closed'])]
    p1=W[W.Score>=80]; stockrisk=W[W.Estoque_Livre<=3]
    c1,c2,c3,c4=st.columns(4)
    c1.metric('Pipeline',brl(active.Valor.sum()),f'{len(active)} oportunidades')
    c2.metric('Cross Sell / Upsell',brl(active.Growth_Value.sum()),'potencial incremental')
    c3.metric('Eficiência Comercial',f'{len(p1)} P1',brl(p1.Valor.sum()))
    c4.metric('Receita em Risco',brl(stockrisk.Valor.sum()),'estoque / abastecimento')
    st.markdown('### Prioridades Comerciais')
    t=W[['OPP','Cliente','Vendedor','Valor','Score','Prioridade','Status SF','Próxima Ação']].head(6).copy(); t['Valor']=t.Valor.map(brl)
    st.dataframe(t,use_container_width=True,hide_index=True)
    st.markdown('### Alertas Executivos')
    a,b,c=st.columns(3)
    a.info(f"**Eficiência Comercial:** {len(W[W.SLA_h>4])} oportunidades requerem ação de cadência.")
    b.warning(f"**Receita em Risco:** {len(stockrisk)} oportunidades apresentam restrição de estoque.")
    c.success(f"**Potencial de Crescimento:** {len(W)} oportunidades avaliadas para Cross Sell / Upsell.")

elif page=='Smart Workflow':
    st.subheader('Smart Workflow — Fila Comercial Priorizada')
    st.caption('O sistema prepara e prioriza. O vendedor decide e vende.')
    show=W.copy(); show['Oportunidade']=show.Valor.map(brl)
    cols=['Prioridade','Cliente','Score','Status SF','Oportunidade','Cross Sell / Upsell','Incluir','Próxima Ação','Gerar proposta']
    edited=st.data_editor(show[cols],use_container_width=True,hide_index=True,key='v8_workflow',
        column_config={
            'Status SF':st.column_config.SelectboxColumn('Status SF',options=SF_STAGES,required=True),
            'Incluir':st.column_config.CheckboxColumn('Incluir?'),
            'Próxima Ação':st.column_config.TextColumn('Próxima Ação'),
            'Gerar proposta':st.column_config.CheckboxColumn('Gerar proposta')},
        disabled=['Prioridade','Cliente','Score','Oportunidade','Cross Sell / Upsell'])
    for i in range(len(edited)):
        W.at[i,'Status SF']=edited.at[i,'Status SF']; W.at[i,'Próxima Ação']=edited.at[i,'Próxima Ação']
        W.at[i,'Incluir']=bool(edited.at[i,'Incluir']); W.at[i,'Gerar proposta']=bool(edited.at[i,'Gerar proposta'])
    sel=W[W['Gerar proposta']]
    if len(sel):
        r=sel.iloc[0]; s=STOCK[STOCK.SKU==r.SKU].iloc[0]; qtd=max(1,int(round(r.Valor/s.Preco_Demo)))
        items=[{'sku':s.SKU,'produto':s.Descricao,'qtd':qtd,'list_price':float(s.Preco_Lista),'discount':float(s.Desconto_Max),'unit':float(s.Preco_Demo)}]
        if r.Incluir:
            gp=STOCK[STOCK.SKU==r.Growth_SKU].iloc[0]
            # V7 PDF receives the optional item; V8 screen makes its optional nature explicit.
            items.append({'sku':gp.SKU,'produto':'OPCIONAL - '+gp.Descricao,'qtd':int(r.Growth_Qtd),'list_price':float(gp.Preco_Lista),'discount':float(gp.Desconto_Max),'unit':float(gp.Preco_Demo)})
        no=f"DEMO-{datetime.now().strftime('%Y%m%d')}-{int(r.OPP)}"
        st.markdown('### Proposta pronta para validação')
        a,b,c=st.columns(3); a.metric('Demanda principal',brl(r.Valor)); b.metric('Adicional opcional',brl(r.Growth_Value) if r.Incluir else 'R$ 0'); c.metric('Status Salesforce',r['Status SF'])
        st.download_button('📄 BAIXAR PROPOSTA AUTOMÁTICA',generate_proposal_pdf(r.Cliente,r.Vendedor,items,no),f'Proposta_{no}.pdf','application/pdf',type='primary')
        st.info('Cross Sell / Upsell selecionado pelo vendedor é identificado como **OPCIONAL** na proposta.' if r.Incluir else 'Proposta somente com a demanda principal; recomendação de Growth permanece registrada.')
    with st.expander('+ Nova solicitação'):
        a,b,c=st.columns(3); cli=a.selectbox('Cliente',CUSTOMERS.Cliente.tolist()); sku=b.selectbox('SKU',STOCK.SKU.tolist()); qtd=c.number_input('Quantidade',1,100,2)
        if st.button('Criar oportunidade'): st.success('Oportunidade demonstrativa criada em **Identify**.')

elif page=='Follow-up Comercial':
    st.subheader('Follow-up Comercial')
    st.caption('Cadência: D+2 → D+5 → D+10 → depois a cada 5 dias até Order Promised ou Lost Closed.')
    f=W[W['Status SF']=='Propose'].copy()
    days={81002:2,81003:7,81007:12,81008:5,81010:10}
    f['Dias aguardando resposta']=f.OPP.map(days).fillna(3).astype(int)
    def nxt(d):
        if d<=2:return 'D+2'
        if d<=5:return 'D+5'
        if d<=10:return 'D+10'
        return f"D+{10+5*int(np.ceil((d-10)/5))}"
    f['Próximo FUP']=f['Dias aguardando resposta'].map(nxt)
    f['Comentários']=f.OPP.map(st.session_state.fup_comments).fillna('')
    a,b,c,d=st.columns(4); a.metric('Follow-ups ativos',len(f)); b.metric('FUP ≥ D+5',len(f[f['Dias aguardando resposta']>=5])); c.metric('Valor aguardando resposta',brl(f.Valor.sum())); d.metric('Cadência','D+2 / D+5 / D+10','depois +5 dias')
    f['Valor']=f.Valor.map(brl)
    ed=st.data_editor(f[['OPP','Cliente','Valor','Dias aguardando resposta','Vendedor','Status SF','Próximo FUP','Comentários']],use_container_width=True,hide_index=True,
        column_config={'Status SF':st.column_config.SelectboxColumn('Status SF',options=SF_STAGES),'Comentários':st.column_config.TextColumn('Comentários',width='large')},
        disabled=['OPP','Cliente','Valor','Dias aguardando resposta','Vendedor','Próximo FUP'])
    for _,r in ed.iterrows():
        st.session_state.fup_comments[int(r.OPP)]=r['Comentários']
        ix=W.index[W.OPP==r.OPP]
        if len(ix): W.at[ix[0],'Status SF']=r['Status SF']

elif page=='Fila Inteligente':
    st.subheader('Smart Priority — priorização comercial')
    a,b,c=st.columns(3); seller=a.selectbox('Vendedor',['Todos']+sorted(W.Vendedor.unique())); pri=b.selectbox('Prioridade',['Todas','P1','P2','P3']); sf=c.selectbox('Status Salesforce',['Todos']+SF_STAGES)
    q=W.copy()
    if seller!='Todos': q=q[q.Vendedor==seller]
    if pri!='Todas': q=q[q.Prioridade.str.startswith(pri)]
    if sf!='Todos': q=q[q['Status SF']==sf]
    t=q[['OPP','Cliente','Produto','Vendedor','Valor','Score','Prioridade','Status SF','Próxima Ação']].copy(); t['Valor']=t.Valor.map(brl)
    st.dataframe(t,use_container_width=True,hide_index=True)

elif page=='Account 360':
    st.subheader('Account 360')
    cli=st.selectbox('Cliente',CUSTOMERS.Cliente.tolist()); a=CUSTOMERS[CUSTOMERS.Cliente==cli].iloc[0]
    c1,c2,c3,c4=st.columns(4); c1.metric('Fat. 2025',brl(a.Fat_2025)); c2.metric('2026 YTD',brl(a.Fat_2026_YTD)); c3.metric('Base instalada',int(a.Base_Instalada)); c4.metric('Crédito livre',brl(a.Credito_Livre))
    st.dataframe(BASE[BASE.Cliente==cli],use_container_width=True,hide_index=True)
    q=W[W.Cliente==cli][['OPP','Produto','Valor','Score','Status SF','Próxima Ação']].copy(); q['Valor']=q.Valor.map(brl); st.dataframe(q,use_container_width=True,hide_index=True)

elif page=='Growth Engine':
    st.subheader('Smart Growth — receita incremental')
    hi=G[G.Growth_Score>=70]; a,b,c=st.columns(3); a.metric('Sinais de alta aderência',len(hi)); b.metric('Potencial demonstrativo',brl(hi.Potencial_Demo.sum())); c.metric('Contas mapeadas',hi.Cliente.nunique())
    gv=G[['Cliente','Vendedor','Equipamento','Meses_Desde_Compra','Descricao','Growth_Score','Potencial_Demo','Acao_Sugerida']].copy(); gv['Potencial_Demo']=gv.Potencial_Demo.map(brl); st.dataframe(gv,use_container_width=True,hide_index=True)

elif page=='Performance Comercial do Time':
    st.subheader('Performance Comercial do Time')
    rows=[]
    for seller in sorted(W.Vendedor.unique()):
        s=W[W.Vendedor==seller]; adoption=int(round(s.Incluir.mean()*100)); conv=int(round(s.Prob.mean()*100)); score=int(round(conv*.35+s.Score.mean()*.35+max(50,adoption)*.30))
        rows.append([seller,score,s.Valor.sum(),len(s),conv,s.SLA_h.mean(),adoption,s[s.Incluir].Growth_Value.sum()])
    perf=pd.DataFrame(rows,columns=['Vendedor','Performance','Pipeline','OPPs Ativas','Conversão','SLA','Adoção Growth','Receita Incremental'])
    cs=st.columns(3)
    for c,(_,r) in zip(cs,perf.iterrows()): c.markdown(gauge(r.Vendedor,int(r.Performance),r.Pipeline,r['Receita Incremental']),unsafe_allow_html=True)
    st.markdown('### Visão Executiva por Vendedor')
    p=perf.copy(); p['Pipeline']=p.Pipeline.map(brl); p['Conversão']=p['Conversão'].astype(str)+'%'; p['SLA']=p.SLA.round(1).astype(str)+' h'; p['Adoção Growth']=p['Adoção Growth'].astype(str)+'%'; p['Receita Incremental']=p['Receita Incremental'].map(brl); st.dataframe(p,use_container_width=True,hide_index=True)
    st.markdown('### Negociações por Vendedor')
    seller=st.selectbox('Selecionar vendedor',sorted(W.Vendedor.unique()))
    v=W[W.Vendedor==seller][['OPP','Cliente','Valor','Score','Status SF','Próxima Ação','Cross Sell / Upsell','Incluir']].copy(); v['Valor']=v.Valor.map(brl); v=v.rename(columns={'Incluir':'Growth trabalhado?'}); st.dataframe(v,use_container_width=True,hide_index=True)
    st.markdown('### Insights de Performance & Coaching')
    for _,r in perf.iterrows():
        if r['Adoção Growth']<35: st.warning(f"{r.Vendedor}: coaching em Cross Sell / Upsell — adoção {int(r['Adoção Growth'])}%.")
        elif r.SLA>4: st.info(f"{r.Vendedor}: revisar carga e cadência — SLA médio {r.SLA:.1f}h.")
        else: st.success(f"{r.Vendedor}: execução equilibrada; manter cadência e ampliar receita incremental.")

elif page=='Arquitetura & Automação':
    st.subheader('Arquitetura proposta — Smart Hub + Salesforce')
    st.markdown("**Salesforce:** Identify → Develop → Propose → Order Promised / Lost Closed.  \n**Smart Hub:** prepara, prioriza, recomenda, gera proposta e controla cadência.  \n**Governança:** Status SF e Próxima Ação são editáveis pelo vendedor.")
    flow=pd.DataFrame([['Identify','Demanda recebida ou oportunidade criada'],['Develop','Oportunidade em andamento'],['Propose','Proposta enviada ao cliente'],['Order Promised','OC recebida'],['Lost Closed','Oportunidade perdida']],columns=['Status Salesforce','Gatilho'])
    st.dataframe(flow,use_container_width=True,hide_index=True)
    st.info('Gerar o PDF não muda sozinho o status para Propose; a etapa representa o envio efetivo ao cliente.')

elif page=='Modo Apresentação':
    st.subheader('Modo Apresentação — Business Case')
    st.markdown("### Três soluções\n**1. Smart Workflow / Productivity** — preparação, Salesforce stages, proposta e Follow-up.  \n**2. Smart Priority / Conversion** — fila por impacto e próxima ação.  \n**3. Smart Growth / Incremental Revenue** — Cross Sell / Upsell antes da proposta e adoção por vendedor.")
    agenda=pd.DataFrame([['0–3 min','Cenário'],['3–7 min','Smart Priority'],['7–11 min','Smart Workflow'],['11–14 min','Follow-up Comercial'],['14–17 min','Performance do Time'],['17–20 min','Plano 30 dias']],columns=['Tempo','Bloco'])
    st.dataframe(agenda,use_container_width=True,hide_index=True)

st.markdown('---'); st.caption('Inside Sales Smart Hub V8 • MVP demonstrativo • dados 100% fictícios e anonimizados')
