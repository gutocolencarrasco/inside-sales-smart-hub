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

st.markdown('''<div class="hero"><h1>Inside Sales Smart Hub V7</h1><p>From Reactive Requests to Intelligent Revenue Growth</p><span class="pill">SMART WORKFLOW</span><span class="pill">SMART PRIORITY</span><span class="pill">SMART GROWTH</span></div>''',unsafe_allow_html=True)
st.caption('MVP demonstrativo • Todos os clientes, CNPJs, SKUs, oportunidades, volumes e valores exibidos são fictícios e anonimizados.')

page=st.sidebar.radio('Navegação',['Central de Decisão','Smart Workflow','Fila Inteligente','Account 360','Growth Engine','Cockpit do Coordenador','Arquitetura & Automação','Modo Apresentação'])
st.sidebar.markdown('---'); st.sidebar.metric('Operação','600 orçamentos/mês','≈ 30/dia útil'); st.sidebar.metric('Time','3 colaboradores'); st.sidebar.caption('Business Case • dados demonstrativos')

if page=='Central de Decisão':
    st.subheader('Central de Decisão — o que merece atenção agora?')
    p1=Q[Q.Score>=80]; late=Q[Q.SLA_h>4]; stockrisk=Q[Q.Estoque_Livre<=3]; hi=G[G.Growth_Score>=70]
    c1,c2,c3,c4=st.columns(4)
    c1.metric('P1 • atender agora',len(p1),brl(p1.Valor.sum()))
    c2.metric('Fora do SLA',len(late),brl(late.Valor.sum()))
    c3.metric('Receita em risco',brl(stockrisk.Valor.sum()),'estoque / abastecimento')
    c4.metric('Growth identificado',brl(hi.Potencial_Demo.sum()),f"{len(hi)} sinais")

    st.markdown('### Leitura executiva do dia')
    a,b,c=st.columns(3)
    a.markdown('<div class="card"><b>SMART WORKFLOW</b><div class="big">Preparar antes de distribuir</div><p class="muted">Identificação, histórico, estoque, crédito e cadência prontos antes do vendedor atuar.</p></div>',unsafe_allow_html=True)
    b.markdown('<div class="card"><b>SMART PRIORITY</b><div class="big">Fila por impacto</div><p class="muted">Valor + conversão + estoque + SLA + crédito substituem a ordem puramente cronológica.</p></div>',unsafe_allow_html=True)
    c.markdown('<div class="card"><b>SMART GROWTH</b><div class="big">Criar demanda</div><p class="muted">Base instalada, recorrência e comportamento geram sinais de reativação, cross-sell e upsell.</p></div>',unsafe_allow_html=True)

    st.markdown('### Próximas melhores ações')
    view=Q[['OPP','Cliente','Vendedor','Produto','Valor','Score','Prioridade','SLA_h','Etapa']].head(6).copy()
    view['Valor']=view['Valor'].map(brl)
    view=view.rename(columns={'Valor':'Valor demonstrativo','SLA_h':'SLA (h)'})
    st.dataframe(view,use_container_width=True,hide_index=True)

    st.markdown('### Gestão por exceção')
    x1,x2,x3=st.columns(3)
    x1.info(f"**SLA:** {len(late)} oportunidades precisam de ação para voltar à cadência.")
    x2.warning(f"**Revenue at Risk:** {len(stockrisk)} oportunidades têm restrição de estoque.")
    x3.success(f"**Growth:** {len(hi)} sinais proativos já podem virar abordagem comercial.")
    st.caption('Objetivo do hub: reduzir decisões operacionais repetitivas e aumentar o tempo efetivo de venda.')

elif page=='Smart Workflow':
    st.subheader('Smart Workflow V7 — solicitação → Growth → proposta pronta')
    st.markdown('**Entrada → Identificação → Estoque → Pricing → Smart Growth → Decisão do vendedor → Proposta automática → Cadência**')

    c1,c2,c3=st.columns(3)
    c1.markdown('<div class="card"><h3>1. Preparar</h3><div class="big">Cliente + Estoque + Pricing</div><p class="muted">Valida conta, disponibilidade, preço lista e desconto permitido.</p></div>',unsafe_allow_html=True)
    c2.markdown('<div class="card"><h3>2. Crescer</h3><div class="big">Smart Growth antes da proposta</div><p class="muted">Cross-sell / upsell aparece antes da cotação sair.</p></div>',unsafe_allow_html=True)
    c3.markdown('<div class="card"><h3>3. Executar</h3><div class="big">Proposta automática</div><p class="muted">Gera PDF demonstrativo já precificado e prepara D+2 / D+5.</p></div>',unsafe_allow_html=True)

    st.markdown('### Simulação de nova solicitação')
    a,b,c=st.columns(3)
    cli=a.selectbox('Cliente',CUSTOMERS.Cliente.tolist(),key='wf_cli')
    sku=b.selectbox('SKU solicitado',STOCK.SKU.tolist(),key='wf_sku')
    qtd=c.number_input('Quantidade',1,100,2,1,key='wf_qtd')
    s0=STOCK[STOCK.SKU==sku].iloc[0]
    st.caption(f"Preço lista demonstrativo: {brl2(s0.Preco_Lista)} • desconto automático permitido: {s0.Desconto_Max*100:.0f}% • preço líquido: {brl2(s0.Preco_Demo)}")

    if st.button('Processar solicitação', type='primary'):
        s=STOCK[STOCK.SKU==sku].iloc[0]
        ac=CUSTOMERS[CUSTOMERS.Cliente==cli].iloc[0]
        val=float(s.Preco_Demo*qtd)
        base_cli=BASE[BASE.Cliente==cli]
        hist_meses=int(base_cli.Meses_Desde_Compra.max()) if len(base_cli) else 0
        estoque_score=100 if s.Estoque_Livre>=qtd else (65 if s.Estoque_Livre>0 else 5)
        credito_score=100 if ac.Credito_Livre>=val else (55 if ac.Credito_Livre>0 else 5)
        recencia_score=90 if ac.Dias_Ultima_Compra<=45 else (70 if ac.Dias_Ultima_Compra<=90 else 45)
        valor_score=min(100,max(20,val/180000*100))
        score=int(round(valor_score*.30+82*.25+estoque_score*.20+recencia_score*.15+credito_score*.10))
        prioridade='P1 • Atender agora' if score>=80 else ('P2 • Alta prioridade' if score>=65 else 'P3 • Normal')
        growth=growth_for_customer(cli,sku)
        st.session_state['wf_result']={'cli':cli,'sku':sku,'qtd':int(qtd),'score':score,'prioridade':prioridade,'growth':growth,'val':val,'hist_meses':hist_meses}
        st.session_state['wf_growth_include']=False

    r=st.session_state.get('wf_result')
    if r and r['cli']==cli and r['sku']==sku and r['qtd']==int(qtd):
        s=STOCK[STOCK.SKU==r['sku']].iloc[0]
        ac=CUSTOMERS[CUSTOMERS.Cliente==r['cli']].iloc[0]
        growth=r['growth']
        st.markdown('### Resultado do processamento')
        x1,x2,x3,x4=st.columns(4)
        x1.metric('Priority Score',f"{r['score']}/100",r['prioridade'])
        x2.metric('Estoque livre',f"{int(s.Estoque_Livre)} un.",f"+{int(s.Transito)} em trânsito")
        x3.metric('Preço líquido',brl2(s.Preco_Demo),f"{s.Desconto_Max*100:.0f}% desc. automático")
        x4.metric('Crédito livre',brl(ac.Credito_Livre),'demonstrativo')

        steps=[
            f"✓ Cliente identificado — {r['cli']} • responsável {ac.Vendedor}",
            f"✓ Histórico e base instalada consultados — {int(ac.Base_Instalada)} equipamentos",
            f"✓ Estoque validado — {s.Descricao}: {int(s.Estoque_Livre)} unidades livres",
            f"✓ Price List aplicada — lista {brl2(s.Preco_Lista)} • desconto {s.Desconto_Max*100:.0f}% • líquido {brl2(s.Preco_Demo)}",
            f"✓ Crédito verificado — {brl(ac.Credito_Livre)} livres para cotação de {brl2(r['val'])}",
            f"✓ Commercial Priority Score — {r['score']}/100 • {r['prioridade']}",
            f"✓ Smart Growth consultado antes da proposta — {growth['tipo']} encontrado",
            "✓ Proposta comercial preparada; falta apenas a decisão sobre a oportunidade incremental"
        ]
        for item in steps:
            st.markdown(f'<div class="step-ok">{item}</div>',unsafe_allow_html=True)

        st.markdown('### 💡 Smart Growth — oportunidade antes de gerar a proposta')
        gp=STOCK[STOCK.SKU==growth['sku']].iloc[0]
        gpot=gp.Preco_Demo*growth['qtd']
        st.markdown(
            f'<div class="reco"><b>{growth["tipo"]} IDENTIFICADO • Growth Score {growth["score"]}/100</b><br>'
            f'<b>{growth["produto"]}</b> • SKU {growth["sku"]}<br>{growth["motivo"]}<br>'
            f'Potencial incremental demonstrativo: <b>{brl2(gpot)}</b> • Preço líquido dentro da política fictícia: {brl2(gp.Preco_Demo)}</div>',
            unsafe_allow_html=True
        )
        include=st.checkbox('Incluir esta oportunidade na proposta',value=st.session_state.get('wf_growth_include',False),key='wf_growth_include')
        if include:
            st.success(f"O item {growth['produto']} será incluído na proposta como oportunidade de {growth['tipo'].lower()}.")
        else:
            st.info('O vendedor pode seguir somente com o item solicitado. A recomendação fica registrada para aprendizado e follow-up.')

        st.markdown('### Proposta automática')
        items=[{'sku':s.SKU,'produto':s.Descricao,'qtd':int(r['qtd']),'list_price':float(s.Preco_Lista),'discount':float(s.Desconto_Max),'unit':float(s.Preco_Demo)}]
        if include:
            items.append({'sku':gp.SKU,'produto':gp.Descricao,'qtd':int(growth['qtd']),'list_price':float(gp.Preco_Lista),'discount':float(gp.Desconto_Max),'unit':float(gp.Preco_Demo)})
        total=sum(i['qtd']*i['unit'] for i in items)
        resumo=pd.DataFrame(items)
        resumo['Preço Lista']=resumo['list_price'].map(brl2)
        resumo['Desconto']=resumo['discount'].map(lambda x:f'{x*100:.0f}%')
        resumo['Preço Líquido']=resumo['unit'].map(brl2)
        resumo['Total']=pd.Series([i['qtd']*i['unit'] for i in items]).map(brl2)
        resumo=resumo.rename(columns={'sku':'SKU','produto':'Produto','qtd':'Qtd'})[['SKU','Produto','Qtd','Preço Lista','Desconto','Preço Líquido','Total']]
        st.dataframe(resumo,use_container_width=True,hide_index=True)
        p1,p2,p3=st.columns(3)
        p1.metric('Valor da proposta',brl2(total))
        p2.metric('Economia vs. lista',brl2(sum(i['qtd']*i['list_price'] for i in items)-total))
        margem=(total-sum(i['qtd']*float(STOCK[STOCK.SKU==i['sku']].iloc[0].COGS_Demo) for i in items))/total if total else 0
        p3.metric('Margem demonstrativa',f'{margem*100:.1f}%','indicador fictício')

        proposal_no=f"DEMO-{datetime.now().strftime('%Y%m%d')}-{abs(hash((r['cli'],r['sku'],r['qtd'])))%10000:04d}"
        pdf_bytes=generate_proposal_pdf(r['cli'],ac.Vendedor,items,proposal_no)
        st.download_button('📄 GERAR / BAIXAR PROPOSTA AUTOMÁTICA',data=pdf_bytes,file_name=f'Proposta_{proposal_no}.pdf',mime='application/pdf',type='primary')
        st.caption('Modelo demonstrativo inspirado na estrutura da proposta enviada anteriormente: capa/resumo, tabela de itens, condição de pagamento, prazo e validade. Nenhum dado comercial real é usado.')
        st.markdown(f'<div class="reco"><b>Próxima melhor ação</b><br>{r["prioridade"]}. Proposta já precificada dentro da política demonstrativa. Após envio, criar follow-up D+2 e alerta D+5 automaticamente.</div>',unsafe_allow_html=True)

elif page=='Fila Inteligente':
    st.subheader('Smart Priority — trabalhar a oportunidade certa no momento certo')
    f1,f2=st.columns(2)
    vendedor=f1.selectbox('Filtrar vendedor',['Todos']+sorted(Q.Vendedor.unique().tolist()))
    prioridade_f=f2.selectbox('Filtrar prioridade',['Todas','P1','P2','P3'])
    fq=Q.copy()
    if vendedor!='Todos': fq=fq[fq.Vendedor==vendedor]
    if prioridade_f!='Todas': fq=fq[fq.Prioridade.str.startswith(prioridade_f)]
    fila=fq[['OPP','Cliente','Produto','Vendedor','Valor','Prob','Estoque_Livre','SLA_h','Credito','Score','Prioridade']].copy()
    fila['Valor']=fila['Valor'].map(brl)
    fila['Prob']=(fila['Prob']*100).round().astype(int).astype(str)+'%'
    fila=fila.rename(columns={'Valor':'Valor demonstrativo','Prob':'Prob. conversão','SLA_h':'SLA (h)'})
    st.dataframe(fila,use_container_width=True,hide_index=True)
    st.caption('Score demonstrativo: Receita 30% • Conversão 25% • Estoque 20% • SLA 15% • Crédito 10%. Pesos calibráveis com histórico real.')
    st.info('A fila é recalculada quando mudam estoque, SLA, crédito ou contexto comercial — o ranking acompanha o negócio, não apenas a hora de chegada.')

elif page=='Account 360':
    st.subheader('Account 360 — contexto comercial em uma única tela')
    cli=st.selectbox('Selecione o cliente',CUSTOMERS.Cliente.tolist()); a=CUSTOMERS[CUSTOMERS.Cliente==cli].iloc[0]; b=BASE[BASE.Cliente==cli]; q=Q[Q.Cliente==cli]
    c1,c2,c3,c4,c5=st.columns(5); c1.metric('Fat. 2025',brl(a.Fat_2025)); c2.metric('2026 YTD',brl(a.Fat_2026_YTD)); c3.metric('Base instalada',int(a.Base_Instalada)); c4.metric('Crédito livre',brl(a.Credito_Livre)); c5.metric('Última compra',f"{int(a.Dias_Ultima_Compra)} dias")
    st.markdown('#### Base instalada / recorrência'); st.dataframe(b,use_container_width=True,hide_index=True)
    st.markdown('#### Oportunidades abertas')
    qv=q[['OPP','Produto','Valor','Score','Prioridade','Etapa']].copy(); qv['Valor']=qv['Valor'].map(brl)
    qv=qv.rename(columns={'Valor':'Valor demonstrativo'})
    st.dataframe(qv,use_container_width=True,hide_index=True)
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
    gv=G[['Cliente','Vendedor','Equipamento','Qtd','Meses_Desde_Compra','Descricao','Estoque_Livre','Growth_Score','Potencial_Demo','Acao_Sugerida']].copy()
    gv['Potencial_Demo']=gv['Potencial_Demo'].map(brl)
    gv=gv.rename(columns={'Potencial_Demo':'Potencial demonstrativo','Growth_Score':'Growth Score','Meses_Desde_Compra':'Meses desde compra'})
    st.dataframe(gv,use_container_width=True,hide_index=True)
    st.success('Motor proativo cruza base instalada + recência + estoque + crédito + comportamento para sugerir reativação, cross-sell e upsell.')

elif page=='Cockpit do Coordenador':
    st.subheader('Cockpit do Coordenador — gestão de capacidade, conversão e coaching')
    perf=Q.groupby('Vendedor').agg(Oportunidades=('OPP','count'),Pipeline=('Valor','sum'),Score_Medio=('Score','mean'),SLA_Medio=('SLA_h','mean'),Conversao=('Prob','mean')).reset_index()
    perf['Conversao']=perf.Conversao*100
    perf_show=perf.copy()
    perf_show['Pipeline']=perf_show['Pipeline'].map(brl)
    perf_show['Score_Medio']=perf_show['Score_Medio'].round(0).astype(int)
    perf_show['SLA_Medio']=perf_show['SLA_Medio'].round(1)
    perf_show['Conversao']=perf_show['Conversao'].round(0).astype(int).astype(str)+'%'
    st.dataframe(perf_show,use_container_width=True,hide_index=True)

    st.markdown('### Gestão por exceção e coaching')
    for _,r in perf.iterrows():
        if r.SLA_Medio>4:
            st.warning(f"{r.Vendedor}: revisar carga, priorização e redistribuição; SLA médio {r.SLA_Medio:.1f}h.")
        elif r.Conversao<70:
            st.info(f"{r.Vendedor}: coaching em qualificação, objeções e follow-up.")
        else:
            st.success(f"{r.Vendedor}: desempenho equilibrado; manter cadência e ampliar uso do Growth Engine.")

    st.markdown('### KPIs de gestão')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Meta 1º contato','≤ 4 h')
    k2.metric('Conversão alvo','38%','meta demonstrativa')
    k3.metric('Follow-up','D+2 / D+5')
    k4.metric('Cobertura','600/mês','3 colaboradores')

elif page=='Arquitetura & Automação':
    st.subheader('Arquitetura proposta — automatizar preparação, não julgamento comercial')
    st.markdown('''
**1. Entradas** — e-mail, WhatsApp e CRM.  
**2. Dados** — Salesforce/CRM + ERP/SAP (estoque) + histórico de pedidos/faturamento + base instalada.  
**3. Orquestração** — identificação, deduplicação, SLA, score, roteamento, cadência e Growth Engine.  
**4. IA assistiva** — extração de dados, resumo da conta, sugestão de resposta e próxima melhor ação.  
**5. Governança** — vendedor valida decisão comercial; crédito, pricing excepcional e criação definitiva de cliente permanecem sob aprovação humana.
''')
    flow=pd.DataFrame([
        ['1','Solicitação recebida','E-mail / WhatsApp / CRM','Captura dos campos relevantes'],
        ['2','Identificação','CRM','Match por cliente/CNPJ e responsável'],
        ['3','Enriquecimento','CRM + ERP/SAP','Histórico + base instalada + crédito + estoque'],
        ['4','Pricing','Price List + regras','Preço líquido dentro da alçada'],
        ['5','Growth antes da proposta','Base instalada + histórico','Cross-sell / upsell contextual'],
        ['6','Priorização','Motor de regras','Commercial Priority Score'],
        ['7','Proposta automática','Template + pricing','PDF comercial pronto para validação'],
        ['8','Execução assistida','IA + CRM','Resumo + resposta sugerida + próxima ação'],
        ['9','Cadência','Flow / CRM','D+2 / D+5 + alertas de SLA'],
        ['10','Growth Engine','Dados comerciais','Reativação + cross-sell + upsell'],
        ['11','Gestão','Dashboard','SLA + conversão + pipeline + revenue at risk']
    ],columns=['Etapa','Evento','Origem / Motor','Saída'])
    st.dataframe(flow,use_container_width=True,hide_index=True)

    st.markdown('### O que eu automatizaria x o que manteria humano')
    h1,h2=st.columns(2)
    h1.success('**Automatizar:** captura, consulta, enriquecimento, pricing dentro da alçada, score, Smart Growth, geração de proposta, alertas, cadência, recomendações e dashboards.')
    h2.warning('**Manter humano:** aprovação de crédito, exceções de pricing, criação definitiva de cliente e decisão final de negociação.')

elif page=='Modo Apresentação':
    st.subheader('Modo Apresentação — roteiro guiado do Business Case')

    st.markdown('### 1. Diagnóstico')
    st.info('A operação recebe aproximadamente 600 orçamentos/mês (~30 por dia útil) com 3 colaboradores. O desafio não é simplesmente trabalhar mais solicitações; é trabalhar as oportunidades certas, mais rápido e gerar demanda além do fluxo reativo.')

    st.markdown('### 2. Três soluções conectadas')
    s1,s2,s3=st.columns(3)
    s1.markdown('<div class="card"><b>SMART WORKFLOW</b><div class="big">Produtividade</div><p class="muted">Preparar a oportunidade antes de chegar ao vendedor.</p></div>',unsafe_allow_html=True)
    s2.markdown('<div class="card"><b>SMART PRIORITY</b><div class="big">Conversão</div><p class="muted">Priorizar por impacto, não apenas por ordem de chegada.</p></div>',unsafe_allow_html=True)
    s3.markdown('<div class="card"><b>SMART GROWTH</b><div class="big">Receita incremental</div><p class="muted">Criar oportunidades via base instalada, recorrência, reativação, cross-sell e upsell.</p></div>',unsafe_allow_html=True)

    st.markdown('### 3. Roteiro de 20 minutos')
    agenda=pd.DataFrame([
        ['0–3 min','Diagnóstico','Cenário, gargalos e risco da operação reativa'],
        ['3–5 min','Visão','Apresentar os três motores conectados'],
        ['5–9 min','Smart Workflow V7','Pricing + Smart Growth + proposta automática'],
        ['9–12 min','Smart Priority','Fila por impacto e gestão de SLA'],
        ['12–15 min','Smart Growth','Nova receita além dos chamados recebidos'],
        ['15–18 min','Demo','Processar → Growth → incluir/ignorar → gerar proposta PDF'],
        ['18–20 min','30 dias + KPIs','Plano de implantação e medição']
    ],columns=['Tempo','Bloco','Mensagem'])
    st.dataframe(agenda,use_container_width=True,hide_index=True)

    st.markdown('### 4. Primeiros 30 dias')
    plan=pd.DataFrame([
        ['Dias 1–5','Baseline + SLAs','Mapear funil, tempos, perdas e motivos'],
        ['Dias 6–10','Fila inteligente piloto','Score inicial + gestão diária por exceção'],
        ['Dias 11–20','Cadência + cockpit','Follow-up D+2/D+5 + dashboard do coordenador'],
        ['Dias 21–30','Growth Engine piloto','Reativação/cross-sell em contas selecionadas']
    ],columns=['Período','Prioridade','Entrega'])
    st.dataframe(plan,use_container_width=True,hide_index=True)

    st.markdown('### 5. Indicadores')
    k1,k2,k3,k4=st.columns(4)
    k1.metric('Velocidade','1º contato / SLA')
    k2.metric('Conversão','Win rate / ciclo')
    k3.metric('Produtividade','Oportunidades / rep')
    k4.metric('Growth','Receita incremental')
    st.caption('Também acompanhar: follow-up compliance, pipeline prioritário, oportunidades proativas e revenue at risk.')

    st.markdown('### Fechamento sugerido')
    st.markdown('<div class="reco"><b>“Meu objetivo não seria colocar mais uma ferramenta para o time usar. Seria reduzir as decisões operacionais repetitivas para que as três pessoas tenham mais tempo para vender — com prioridade, cadência e visão de crescimento.”</b></div>',unsafe_allow_html=True)

st.markdown('---'); st.caption('Inside Sales Smart Hub V7 • MVP demonstrativo • dados 100% fictícios e anonimizados • lógica inspirada na estrutura operacional, sem exposição de informações comerciais reais')
