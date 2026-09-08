import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Inside Sales Smart Hub V12", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ---------------------------- Executive UI ----------------------------
st.markdown("""<style>
:root{--navy:#063b6f;--blue:#0878c9;--green:#16a36a;--yellow:#f2b705;--red:#df3b3b;--ink:#16324a;--muted:#60758a;--line:#dbe6ef;--bg:#f5f8fb}
.stApp{background:var(--bg)} .block-container{padding-top:.7rem;max-width:1580px;padding-bottom:4rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#073f75,#052e58);}
[data-testid="stSidebar"] *{color:#fff}.hero{background:white;border:1px solid var(--line);padding:16px 22px;border-radius:14px;margin-bottom:12px;box-shadow:0 2px 10px #0b35500d}
.hero h1{font-size:28px;margin:0;color:#0b2d4d}.hero .smart{color:#0878c9}.hero p{margin:3px 0 0;color:#61788d;font-size:13px}
.section-title{font-size:17px;font-weight:800;color:#0b3e6e;border-bottom:2px solid #e6eef5;padding-bottom:7px;margin:12px 0 9px}
.kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:13px 14px;min-height:104px;box-shadow:0 2px 8px #173e5e0a}.kpi .label{font-size:11px;text-transform:uppercase;letter-spacing:.4px;color:#60758a;font-weight:800}.kpi .value{font-size:25px;color:#102f49;font-weight:850;margin-top:6px}.kpi .sub{font-size:11px;color:#6f8293;margin-top:3px}
.insight{background:white;border:1px solid var(--line);border-radius:12px;padding:12px 14px;min-height:96px}.insight b{color:#0b4c83}.risk{border-left:5px solid var(--red)}.growth{border-left:5px solid var(--green)}.warn{border-left:5px solid var(--yellow)}.info{border-left:5px solid var(--blue)}
.badge{display:inline-block;border-radius:14px;padding:3px 8px;font-size:11px;font-weight:800}.g{background:#daf5e8;color:#087a4b}.y{background:#fff1bd;color:#8a6200}.r{background:#ffe0e0;color:#a52020}.b{background:#dcefff;color:#075d9a}
.box{background:white;border:1px solid var(--line);border-radius:12px;padding:14px}.agent{background:#f3efff;border-left:5px solid #7652c7;border-radius:10px;padding:13px}
.small{font-size:11px;color:#6b7f91}.stage{background:white;border:1px solid var(--line);border-radius:10px;padding:10px;text-align:center}.stage b{font-size:18px;color:#0b3e6e}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:11px;border-radius:12px;box-shadow:none}
.stButton>button{border-radius:8px;font-weight:700}.chat-answer{background:#eef6ff;border:1px solid #cfe5f8;border-radius:12px;padding:13px;color:#173b58}.chat-user{background:#fff;border:1px solid #dce7ef;border-radius:12px;padding:10px}
</style>""", unsafe_allow_html=True)

AOP=4_000_000
STAGES=["Identify","Develop","Propose","Order Promised","Lost Closed"]
ACTIVE=["Identify","Develop","Propose"]
def brl(v): return f"R$ {float(v):,.0f}".replace(",","X").replace(".",",").replace("X",".")
def pct(v): return f"{float(v):.1f}%".replace(".",",")
def priority(score): return "Altíssima" if score>=80 else "Alta" if score>=60 else "Normal"
def risk_color(level): return {"Normal":"🟢","Alta":"🟡","Altíssima":"🔴"}.get(level,"⚪")
def component_level(points,maxp):
    ratio=points/maxp
    return "Altíssima" if ratio>=.80 else "Alta" if ratio>=.60 else "Normal"
def kpi(label,value,sub=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>',unsafe_allow_html=True)

# ---------------------------- 100% fictitious demo data ----------------------------
BASE=[
[91001,"Hospital Horizonte","Ana",186000,"Develop",92,28,24,20,12,8,"Kit Preventivo Alpha — 10 un.","Sensor de Fluxo Pro — 2 un.","FUP today","WhatsApp",2],
[91002,"Rede Vida Nova","Bruno",74000,"Propose",78,22,20,18,10,8,"Sensor de Fluxo Pro — 3 un.","Contrato Preventivo 12M — 1 un.","FUP D+2","Email",5],
[91003,"Instituto Aurora","Carla",29500,"Propose",84,25,22,18,11,8,"Filtro Performance — 10 un.","Kit Preventivo Alpha — 1 un.","FUP overdue","WhatsApp",11],
[91004,"Hospital Monte Azul","Ana",128000,"Identify",66,24,14,10,10,8,"Módulo Eletrônico X — 3 un.","Contrato Preventivo 12M — 1 un.","Validate credit","Email",1],
[91005,"Clínica Integra","Bruno",68000,"Develop",76,21,21,16,10,8,"Bateria Backup Plus — 5 un.","Upgrade Performance — 1 un.","Customer contacted","WhatsApp",7],
[91006,"Grupo Santa Luz","Carla",215000,"Propose",82,30,19,17,9,7,"Contrato Preventivo 12M — 1 un.","Upgrade Performance — 1 un.","Negotiation","Email",3],
[91007,"Hospital Nova Esperança","Ana",99000,"Propose",88,26,23,20,12,7,"Kit Preventivo Alpha — 6 un.","Sensor de Fluxo Pro — 2 un.","FUP overdue","WhatsApp",16],
[91008,"Centro Médico Solaris","Bruno",47000,"Identify",54,17,12,5,11,9,"Válvula Inspiratória — 3 un.","Kit Preventivo Alpha — 1 un.","Await inventory","Email",1],
[91009,"Rede Plena Saúde","Carla",83000,"Develop",79,23,22,18,9,7,"Sensor de Fluxo Pro — 4 un.","Contrato Preventivo 12M — 1 un.","Customer contacted","WhatsApp",4],
[91010,"Hospital Parque Central","Ana",152000,"Propose",73,27,17,13,9,7,"Upgrade Performance — 2 un.","Contrato Preventivo 12M — 1 un.","FUP D+5","Email",9],
[91011,"Clínica Vale Verde","Bruno",7800,"Identify",48,8,13,15,7,5,"Filtro Performance — 3 un.","Kit Preventivo Alpha — 1 un.","Automatic first contact","WhatsApp",0],
[91012,"Centro Diagnóstico Orion","Carla",9400,"Develop",57,10,16,15,9,7,"Bateria Backup Plus — 1 un.","Filtro Performance — 2 un.","WhatsApp replied","WhatsApp",2],
[91013,"Hospital Bela Vista","Ana",4600,"Propose",52,7,15,17,8,5,"Filtro Performance — 2 un.","Kit Preventivo Alpha — 1 un.","FUP D+2","Email",5],
[91014,"Rede Saúde Prime","Bruno",56000,"Order Promised",86,25,22,20,11,8,"Kit Preventivo Alpha — 3 un.","—","PO validated","Email",0],
[91015,"Instituto Lumina","Carla",33000,"Lost Closed",61,16,18,12,8,7,"Sensor de Fluxo Pro — 2 un.","—","Lost — price","Email",0]]
COL=["OPP","Customer","Seller","Value","SF Stage","Score","Revenue","Conversion","Inventory","SLA","Credit","Items in Quote","Cross Sell / Up Sell","Next Best Action","Source","Days Waiting"]
if "opps" not in st.session_state: st.session_state.opps=pd.DataFrame(BASE,columns=COL)
opps=st.session_state.opps
opps["Priority"]=opps.Score.map(priority)
opps["Owner"]=opps.apply(lambda r:"Filipe" if r.Priority=="Normal" and r.Value<=10000 else r.Seller,axis=1)

GROWTH_BASE=[
["Hospital Horizonte","Ana","Part","Kit Preventivo Alpha",3,49200,"Protect uptime with local preventive stock","Identified"],
["Rede Vida Nova","Bruno","Service","Contrato Preventivo 12M",1,44600,"Increase equipment availability and maintenance predictability","Approached"],
["Instituto Aurora","Carla","Part","Sensor de Fluxo Pro",2,40460,"Reduce response time with preventive stock","Interacted"],
["Clínica Integra","Bruno","Part","Bateria Backup Plus",2,24992,"Anticipate replacement and reduce operational impact","Identified"],
["Grupo Santa Luz","Carla","Service","Contrato Preventivo 12M",1,44600,"Move from reactive to planned maintenance","OPP Created"],
["Hospital Nova Esperança","Ana","Part","Kit Preventivo Alpha",2,32800,"Protect equipment availability with local stock","Approached"]]
growth=pd.DataFrame(GROWTH_BASE,columns=["Customer","Seller","Type","Suggested Item","Qty","Growth Potential","Value Proposition","Growth Stage"])
growth["Responsible"]=growth.apply(lambda r:"Filipe" if r["Growth Potential"]<=50000 and r["Growth Stage"]!="OPP Created" else r["Seller"],axis=1)

team=pd.DataFrame([
["Ana",87,569600,5,31.5,94,82,126000,78,93,68],
["Bruno",79,196800,4,27.8,88,76,82000,61,86,54],
["Carla",84,336900,4,29.4,91,85,104000,69,90,62]],
columns=["Seller","Performance Index","Open Pipeline","Active OPPs","Conversion Rate","First Response SLA","Growth Adoption","Incremental Revenue","Commercial Load Index","FUP Compliance","Pipeline Coverage"])

trend=pd.DataFrame({"Month":["Apr","May","Jun","Jul","Aug","Sep"],"Open Pipeline":[680000,760000,820000,910000,990000,1103300],"Conversion Rate":[22.1,23.5,24.2,26.1,28.3,29.6],"Incremental Revenue":[42000,58000,69000,82000,97000,112000]})

# ---------------------------- Helpers ----------------------------
def summary(df=None):
    d=opps if df is None else df
    return pd.DataFrame([[s,int((d["SF Stage"]==s).sum()),float(d.loc[d["SF Stage"]==s,"Value"].sum())] for s in STAGES],columns=["SF Stage","OPPs","Value"])
def stage_cards(df):
    cols=st.columns(5)
    for c,s in zip(cols,STAGES):
        q=df[df["SF Stage"]==s]
        with c: st.markdown(f'<div class="stage"><span class="small">{s}</span><br><b>{len(q)}</b><br><span class="small">{brl(q.Value.sum())}</span></div>',unsafe_allow_html=True)
def proposal_pdf(r, include_optional=True, revision=False):
    b=BytesIO(); styles=getSampleStyleSheet(); doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=16*mm,bottomMargin=16*mm)
    title="REVISED COMMERCIAL PROPOSAL" if revision else "COMMERCIAL PROPOSAL"
    story=[Paragraph(f"INSIDE SALES SMART HUB — {title}",styles['Title']),Spacer(1,5),Paragraph("DADOS 100% FICTÍCIOS / NÃO UTILIZAR COM CLIENTES",styles['Heading3']),Spacer(1,8),Paragraph(f"Customer: {r['Customer']} &nbsp;&nbsp; | &nbsp;&nbsp; Proposal date: {datetime.now().strftime('%d/%m/%Y')} &nbsp;&nbsp; | &nbsp;&nbsp; OPP: DEMO-{int(r['OPP'])}",styles['BodyText']),Spacer(1,12)]
    main=float(r.Value); optional=round(main*0.12,2) if r['Cross Sell / Up Sell']!='—' else 0
    data=[["Código","Descrição","Quantidade","Valor Unitário","Valor Total"],["DEMO-001",r['Items in Quote'],"1",brl(main),brl(main)]]
    if include_optional and optional>0:
        data.append(["OPTIONAL",f"OPCIONAL — {r['Cross Sell / Up Sell']}","1",brl(optional),brl(optional)])
    t=Table(data,colWidths=[26*mm,78*mm,20*mm,29*mm,29*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#063b6f')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.45,colors.HexColor('#d9e3ec')),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),8),('VALIGN',(0,0),(-1,-1),'TOP'),('PADDING',(0,0),(-1,-1),6)]))
    if include_optional and optional>0:
        t.setStyle(TableStyle([('BACKGROUND',(0,2),(-1,2),colors.HexColor('#fff6d8')),('TEXTCOLOR',(0,2),(-1,2),colors.HexColor('#7b5a00')),('FONTNAME',(0,2),(1,2),'Helvetica-Bold')]))
    story += [Paragraph("Commercial Items",styles['Heading2']),t,Spacer(1,10),Paragraph(f"Main Proposal Value: <b>{brl(main)}</b>",styles['BodyText'])]
    if include_optional and optional>0:
        story += [Paragraph(f"Optional Items: <b>{brl(optional)}</b>",styles['BodyText']),Paragraph(f"Total if Optional Items are Accepted: <b>{brl(main+optional)}</b>",styles['BodyText'])]
    story += [Spacer(1,14),Paragraph("Payment: demonstrative commercial condition. Delivery: subject to inventory validation.",styles['BodyText']),Paragraph("Proposal validity: 30 days. Warranty and specific conditions subject to applicable commercial governance.",styles['BodyText']),Spacer(1,14),Paragraph("Customer-facing proposal does not display List Price, Discount, Margin or COGS.",styles['BodyText'])]
    doc.build(story); b.seek(0); return b

def growth_message(r):
    if r.Type=="Part": return f"Olá, [Nome]. Temos o {r['Suggested Item']} disponível e identificamos que pode fazer sentido manter {int(r.Qty)} un. em estoque, reduzindo o risco de parada e possíveis perdas enquanto uma nova peça é adquirida e entregue. Posso avaliar essa necessidade com você?"
    return "Olá, [Nome]. Pela sua base instalada, identificamos uma oportunidade de contrato de serviço para aumentar a disponibilidade dos equipamentos, reduzir paradas não planejadas e trazer maior previsibilidade à manutenção. Posso te apresentar rapidamente essa possibilidade?"

def filipe_answer(text, seller_context="All"):
    q=text.lower().strip(); active=opps[opps["SF Stage"].isin(ACTIVE)]
    seller=None
    for s in team.Seller:
        if s.lower() in q: seller=s
    if seller is None and seller_context!="All": seller=seller_context
    d=active[active.Seller==seller] if seller else active
    who=seller if seller else "o time"
    if any(x in q for x in ["minhas demandas","minhas oportunidades","demandas","oportunidades"]):
        p=d.Priority.value_counts(); return f"{who} possui {len(d)} active opportunities, totalizando {brl(d.Value.sum())}. Priority mix: {p.get('Altíssima',0)} Altíssima, {p.get('Alta',0)} Alta e {p.get('Normal',0)} Normal. A maior oportunidade é {d.sort_values('Value',ascending=False).iloc[0].Customer if len(d) else '—'} ({brl(d.Value.max()) if len(d) else 'R$ 0'})."
    if "aop" in q or "meta" in q:
        pipe=active.Value.sum(); return f"O AOP demonstrativo é {brl(AOP)}. O Open Pipeline atual é {brl(pipe)}, equivalente a {pct(pipe/AOP*100)} do AOP. O AOP Gap nominal é {brl(max(AOP-pipe,0))}."
    if "risco" in q or "risk" in q:
        r=active[(active.Priority=="Altíssima") & (active.Inventory<16)]; return f"Revenue at Risk: {brl(r.Value.sum())} em {len(r)} oportunidades Altíssimas com sinal de inventory pressure. Recomendo priorizar validação de disponibilidade e plano de contingência."
    if "carga" in q or "load" in q:
        x=team.sort_values("Commercial Load Index"); return f"{x.iloc[0].Seller} tem o menor Commercial Load Index ({x.iloc[0]['Commercial Load Index']}) e é o melhor candidato para handoff. O maior índice é {x.iloc[-1].Seller} ({x.iloc[-1]['Commercial Load Index']})."
    if "follow" in q or "fup" in q:
        f=d[d["SF Stage"].isin(["Develop","Propose"])]; overdue=f[f["Days Waiting"]>10]; return f"{who}: {len(f)} oportunidades em Follow UP Comercial, {len(overdue)} overdue, com {brl(f.Value.sum())} aguardando avanço."
    if "growth" in q or "cross" in q or "up sell" in q:
        g=growth[growth.Seller==seller] if seller else growth; return f"{who} possui {len(g)} Growth signals com potencial interno de {brl(g['Growth Potential'].sum())}. O maior sinal é {g.sort_values('Growth Potential',ascending=False).iloc[0].Customer if len(g) else '—'}."
    if "convers" in q:
        if seller: v=float(team.loc[team.Seller==seller,"Conversion Rate"].iloc[0]); return f"Conversion Rate de {seller}: {pct(v)}. No Priority Score, o driver Conversion combina histórico do cliente (40%), conversão da família/produto (25%), recorrência (20%) e maturidade da demanda (15%)."
        return "No Priority Score, Conversion combina histórico de conversão do cliente (40%), conversão da família/produto (25%), recorrência de compra (20%) e maturidade da demanda (15%)."
    if "pipeline" in q:
        return f"Open Pipeline de {who}: {brl(d.Value.sum())}, distribuído em {len(d)} active opportunities."
    if any(x in q for x in ["hoje","fazer hoje","prioridades do dia","agenda"]):
        sf=d[d['SF Stage'].isin(['Develop','Propose'])]; od=sf[sf['Days Waiting']>10]; ng=growth[(growth.Seller==seller) & (growth['Growth Stage'].isin(['Identified','Approached']))] if seller else growth[growth['Growth Stage'].isin(['Identified','Approached'])]
        return f"Prioridades de hoje para {who}: {int((d['SF Stage']=='Identify').sum())} New Opportunities, {len(sf)} Follow UPs ({len(od)} overdue / {brl(od.Value.sum())}), {len(ng)} Active Prospecting actions ({brl(ng['Growth Potential'].sum())}) e revisão de propostas em Propose quando houver negociação."
    if "filipe" in q and any(x in q for x in ["trabalhando","carteira","responsavel","responsável"]):
        fo=active[active.Owner=='Filipe']; fg=growth[growth.Responsible=='Filipe']; return f"Filipe é responsável por {len(fo)} oportunidades reativas Normal de até R$ 10K ({brl(fo.Value.sum())}), incluindo seus Follow UPs, e por {len(fg)} sinais de Active Prospecting de até R$ 50K ({brl(fg['Growth Potential'].sum())} de potencial interno)."
    return "Posso consultar o Smart Hub sobre demandas, Open Pipeline, AOP, Revenue at Risk, Growth, Follow UP Comercial, Conversion, Commercial Load e performance por vendedor. Ex.: ‘Quais são as demandas da Ana?’ ou ‘Quem tem menor Commercial Load?’"

# ---------------------------- Navigation ----------------------------
nav=["Executive Cockpit","Sales Workspace","Growth Engine","Account 360","Management"]
st.sidebar.markdown("## PHILIPS\n**Health Systems**")
st.sidebar.markdown('<span style="font-size:12px;opacity:.75">INSIDE SALES SMART HUB</span><br><span style="display:inline-block;margin-top:6px;background:#ffffff22;border:1px solid #ffffff55;border-radius:12px;padding:2px 9px;font-size:11px;font-weight:800">VERSION 12</span>',unsafe_allow_html=True)
main_page=st.sidebar.radio("Navigation",nav,label_visibility="collapsed")
if main_page=="Executive Cockpit":
    sub=st.sidebar.radio("View",["Business Overview","Seller Performance"],key="exec_view")
    page="Central de Decisão" if sub=="Business Overview" else "Performance Comercial do Time"
elif main_page=="Sales Workspace":
    sub=st.sidebar.radio("Workspace",["Opportunities","Smart Priority","Follow UP"],key="sales_view")
    page={"Opportunities":"Smart Workflow","Smart Priority":"Fila Inteligente","Follow UP":"Follow UP Comercial"}[sub]
elif main_page=="Management":
    sub=st.sidebar.radio("Management",["Architecture","Presentation Mode"],key="mgmt_view")
    page="Arquitetura" if sub=="Architecture" else "Modo Apresentação"
else:
    page=main_page

ss=summary(); open_df=opps[opps["SF Stage"].isin(ACTIVE)]; open_value=float(open_df.Value.sum()); open_count=len(open_df)
rev_risk_side=float(open_df[(open_df.Priority=="Altíssima") & (open_df.Inventory<16)].Value.sum())
overdue_side=int(((opps["SF Stage"].isin(["Develop","Propose"])) & (opps["Days Waiting"]>10)).sum())
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div style="font-size:14px;font-weight:800;margin-bottom:5px">SALESFORCE PIPELINE</div><div style="font-size:22px;font-weight:900">{brl(open_value)}</div><div style="font-size:11px;opacity:.78;margin-bottom:10px">{open_count} Active OPPs · AOP Coverage {pct(open_value/AOP*100)}</div>',unsafe_allow_html=True)
for stage in ["Identify","Develop","Propose","Order Promised"]:
    r=ss[ss["SF Stage"]==stage].iloc[0]
    st.sidebar.markdown(f'<div style="display:flex;justify-content:space-between;font-size:12px;padding:3px 0"><b>{stage}</b><span>{int(r.OPPs)} · {brl(r.Value)}</span></div>',unsafe_allow_html=True)
st.sidebar.progress(min(open_value/AOP,1.0))
st.sidebar.markdown(f'<div style="font-size:11px;line-height:1.75;margin-top:6px">🟢 <b>{brl(float(opps.loc[opps["SF Stage"]=="Propose","Value"].sum()))}</b> in Propose<br>🔴 <b>{brl(rev_risk_side)}</b> Revenue at Risk<br>🟡 <b>{overdue_side}</b> Overdue FUPs</div>',unsafe_allow_html=True)
lost=ss[ss["SF Stage"]=="Lost Closed"].iloc[0]
st.sidebar.caption(f"Lost Closed: {int(lost.OPPs)} OPP · {brl(lost.Value)}")

st.markdown('<div class="hero"><h1>INSIDE SALES <span class="smart">SMART HUB</span></h1><p>Serve better. Sell more. Prioritize what creates value. · V12 Executive Cockpit · 100% fictitious demo data</p></div>',unsafe_allow_html=True)

# ---------------------------- Pages ----------------------------
if page=="Central de Decisão":
    st.markdown('<div class="section-title">Executive Sales Cockpit</div>',unsafe_allow_html=True)
    active=opps[opps["SF Stage"].isin(ACTIVE)]; won=opps[opps["SF Stage"]=="Order Promised"]
    rev_risk=active[(active.Priority=="Altíssima") & (active.Inventory<16)].Value.sum(); gp=growth["Growth Potential"].sum()
    cols=st.columns(6)
    vals=[("Open Pipeline",brl(active.Value.sum()),f"{len(active)} active OPPs"),("AOP Attainment",pct((active.Value.sum()+won.Value.sum())/AOP*100),f"AOP {brl(AOP)}"),("Conversion Rate","29,6%","+1,3 p.p. vs Aug"),("Sales Efficiency","91%","SLA + FUP execution"),("Revenue at Risk",brl(rev_risk),"Inventory / SLA pressure"),("Growth Potential",brl(gp),f"{len(growth)} signals")]
    for c,v in zip(cols,vals):
        with c:kpi(*v)
    st.markdown('<div class="section-title">Sales Performance & Pipeline</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([1.25,1,1])
    with c1:
        st.caption("Salesforce Funnel — Value by Stage")
        s=summary(); st.bar_chart(s.set_index("SF Stage")["Value"],height=260)
    with c2:
        st.caption("Open Pipeline by Seller")
        ps=active.groupby("Seller")["Value"].sum().sort_values(ascending=False); st.bar_chart(ps,height=260)
    with c3:
        st.caption("Priority Mix — Active OPPs")
        mix=active.Priority.value_counts().reindex(["Altíssima","Alta","Normal"]).fillna(0); st.bar_chart(mix,height=260)
    c1,c2=st.columns([1.4,1])
    with c1:
        st.caption("Open Pipeline Trend")
        st.line_chart(trend.set_index("Month")[["Open Pipeline"]],height=230)
    with c2:
        st.caption("AOP Coverage")
        coverage=min(active.Value.sum()/AOP*100,100); st.progress(coverage/100); st.metric("Pipeline / AOP",pct(coverage),brl(active.Value.sum()))
        st.caption(f"AOP Gap: {brl(max(AOP-active.Value.sum()-won.Value.sum(),0))}")
    st.markdown('<div class="section-title">Executive Insights</div>',unsafe_allow_html=True)
    a,b,c,d=st.columns(4)
    with a: st.markdown(f'<div class="insight risk"><b>Revenue at Risk</b><br>{brl(rev_risk)} require inventory/SLA attention.<br><span class="small">Prioritize high-probability OPPs.</span></div>',unsafe_allow_html=True)
    with b: st.markdown(f'<div class="insight growth"><b>Growth Opportunity</b><br>{brl(gp)} identified across {len(growth)} signals.<br><span class="small">Approach before demand arrives.</span></div>',unsafe_allow_html=True)
    with c: st.markdown('<div class="insight warn"><b>Follow UP Alert</b><br>2 opportunities are above cadence.<br><span class="small">Protect conversion and cycle time.</span></div>',unsafe_allow_html=True)
    with d: st.markdown(f'<div class="insight info"><b>AOP Gap</b><br>{brl(max(AOP-active.Value.sum()-won.Value.sum(),0))} remaining.<br><span class="small">Focus on Propose + Altíssima.</span></div>',unsafe_allow_html=True)

elif page=="Performance Comercial do Time":
    st.markdown('<div class="section-title">Team Performance & Daily Execution</div>',unsafe_allow_html=True)
    fup_all=opps[opps['SF Stage'].isin(['Develop','Propose'])].copy(); fup_all['Overdue']=fup_all['Days Waiting']>10
    prospect_all=growth[growth['Growth Stage'].isin(['Identified','Approached'])].copy()
    c1,c2,c3,c4,c5,c6=st.columns(6)
    c1.metric("Team Performance Index","83/100","+3 pts"); c2.metric("Open Pipeline",brl(opps[opps['SF Stage'].isin(ACTIVE)].Value.sum())); c3.metric("Overdue FUP",int(fup_all.Overdue.sum()),brl(fup_all.loc[fup_all.Overdue,'Value'].sum())); c4.metric("Active Prospecting",len(prospect_all),brl(prospect_all['Growth Potential'].sum())); c5.metric("FUP Compliance","90%","+4 p.p."); c6.metric("Incremental Revenue",brl(team['Incremental Revenue'].sum()))
    c1,c2,c3=st.columns(3)
    with c1: st.caption("Seller Performance Index"); st.bar_chart(team.set_index("Seller")[["Performance Index","First Response SLA","FUP Compliance"]],height=235)
    with c2: st.caption("Commercial Load Index"); st.bar_chart(team.set_index("Seller")["Commercial Load Index"],height=235)
    with c3: st.caption("Overdue FUP Value by Seller"); st.bar_chart(fup_all[fup_all.Overdue].groupby('Seller')['Value'].sum(),height=235)
    st.markdown('<div class="section-title">Seller Performance Dashboard</div>',unsafe_allow_html=True)
    seller=st.selectbox("Seller Performance Dashboard",["All"]+team.Seller.tolist()+["Filipe"])
    if seller=="All":
        so=opps[opps['SF Stage'].isin(ACTIVE)]; sg=growth; sfup=fup_all; sprosp=prospect_all; overdue=sfup[sfup.Overdue]
        perf,conv,gadopt,load=83,29.6,float(team['Growth Adoption'].mean()),float(team['Commercial Load Index'].mean())
    elif seller=="Filipe":
        so=opps[(opps.Owner=='Filipe')&(opps['SF Stage'].isin(ACTIVE))]; sg=growth[growth.Responsible=='Filipe']; sfup=fup_all[fup_all.Owner=='Filipe']; sprosp=prospect_all[prospect_all.Responsible=='Filipe']; overdue=sfup[sfup.Overdue]
        perf,conv,gadopt,load=86,34.0,100.0,42.0
    else:
        tr=team[team.Seller==seller].iloc[0]; so=opps[(opps.Owner==seller)&(opps['SF Stage'].isin(ACTIVE))]; sg=growth[growth.Responsible==seller]; sfup=fup_all[fup_all.Owner==seller]; sprosp=prospect_all[prospect_all.Responsible==seller]; overdue=sfup[sfup.Overdue]
        perf,conv,gadopt,load=float(tr['Performance Index']),float(tr['Conversion Rate']),float(tr['Growth Adoption']),float(tr['Commercial Load Index'])
    cols=st.columns(7); metrics=[("Performance Index",f"{perf:.0f}/100","Management score"),("Open Pipeline",brl(so.Value.sum()),f"{len(so)} active OPPs"),("Conversion Rate",pct(conv),"Commercial effectiveness"),("Overdue FUP",str(len(overdue)),brl(overdue.Value.sum())),("Active Prospecting",str(len(sprosp)),brl(sprosp['Growth Potential'].sum())),("Growth Adoption",pct(gadopt),"Proactive selling"),("Commercial Load",f"{load:.0f}/100","Capacity indicator")]
    for c,v in zip(cols,metrics):
        with c:kpi(*v)
    c1,c2,c3=st.columns(3)
    with c1: st.caption("Salesforce Funnel"); st.bar_chart(summary(so).set_index('SF Stage')['Value'],height=220)
    with c2: st.caption("Priority Portfolio"); st.bar_chart(so.Priority.value_counts().reindex(['Altíssima','Alta','Normal']).fillna(0),height=220)
    with c3: st.caption("Growth Funnel"); st.bar_chart(sg['Growth Stage'].value_counts(),height=220)
    st.markdown("<div class=\"section-title\">Today&#39;s Priorities</div>",unsafe_allow_html=True)
    newopp=so[so['SF Stage']=='Identify'][['Customer','Owner','Value','Priority','SF Stage']].copy(); newopp.insert(0,'Activity Type','New Opportunity'); newopp['Due']='Today'; newopp['Status']='Open'; newopp['Action']='Open opportunity'
    fupday=sfup[(sfup['Days Waiting'].isin([2,5,10])) | (sfup['Days Waiting']>10)][['Customer','Owner','Value','Priority','SF Stage','Days Waiting']].copy(); fupday.insert(0,'Activity Type','Follow UP'); fupday['Due']=fupday['Days Waiting'].apply(lambda x:'Overdue' if x>10 else 'Today'); fupday['Status']='Open'; fupday['Action']='Execute FUP'; fupday=fupday.drop(columns=['Days Waiting'])
    prospect=sprosp[['Customer','Responsible','Growth Potential','Growth Stage']].copy(); prospect.columns=['Customer','Owner','Value','SF Stage']; prospect['Priority']='Growth'; prospect.insert(0,'Activity Type','Active Prospecting'); prospect['Due']='Today'; prospect['Status']=prospect['SF Stage']; prospect['Action']='Contact customer'
    if seller=="All": review_src=opps[(opps['SF Stage']=='Propose')&(opps['Next Best Action'].str.contains('Negotiation|overdue',case=False,regex=True))]
    else: review_src=opps[(opps.Owner==seller)&(opps['SF Stage']=='Propose')&(opps['Next Best Action'].str.contains('Negotiation|overdue',case=False,regex=True))]
    review=review_src[['Customer','Owner','Value','Priority','SF Stage']].copy(); review.insert(0,'Activity Type','Proposal Review'); review['Due']='Today'; review['Status']='Customer revision'; review['Action']='Review proposal'
    daily=pd.concat([newopp,fupday,prospect,review],ignore_index=True)
    if len(daily): daily['Opportunity Value']=daily['Value'].map(brl); daily=daily[['Owner','Activity Type','Customer','SF Stage','Opportunity Value','Priority','Due','Status','Action']]
    st.dataframe(daily,use_container_width=True,hide_index=True)
    c1,c2=st.columns(2)
    with c1: st.caption("Follow UP Exposure"); st.bar_chart(sfup.groupby('SF Stage')['Value'].sum(),height=210)
    with c2: st.caption("Active Prospecting Potential"); st.bar_chart(sg.groupby('Growth Stage')['Growth Potential'].sum(),height=210)
    st.info(f"Manager Insights & Coaching — {seller}: {len(overdue)} overdue FUP ({brl(overdue.Value.sum())}), {len(sprosp)} active prospecting actions ({brl(sprosp['Growth Potential'].sum())}) and {len(review)} proposal review(s). Filipe absorbs governed low-value execution and prospecting to release human capacity.")

elif page=="Smart Workflow":
    st.markdown('<div class="section-title">Smart Workflow — Demand to Action</div>',unsafe_allow_html=True)
    st.caption("Email / WhatsApp → Customer Match → Salesforce Identify → Enrichment → Priority → Owner")
    f1,f2=st.columns(2); seller=f1.selectbox("Seller",["All"]+team.Seller.tolist(),key="wf_seller"); stage=f2.selectbox("Salesforce Stage",["All"]+STAGES,key="wf_stage")
    wf=opps.copy(); wf=wf if seller=="All" else wf[wf.Seller==seller]; wf=wf if stage=="All" else wf[wf['SF Stage']==stage]
    stage_cards(wf)
    st.caption("Proposal actions are available only in Identify / Develop. Propose uses Review Proposal when negotiation or volume/price changes are requested.")
    wf=wf.copy(); wf['Optional Value']=wf.apply(lambda r: round(float(r.Value)*0.12,2) if r['Cross Sell / Up Sell']!='—' else 0,axis=1); wf['Total Opportunity Value']=wf['Value']+wf['Optional Value']
    early=wf[wf['SF Stage'].isin(['Identify','Develop'])].copy(); advanced=wf[~wf['SF Stage'].isin(['Identify','Develop'])].copy()
    if len(early):
        st.markdown("#### Commercial Creation — Identify / Develop")
        editable=early[["Priority","Customer","Owner","Items in Quote","Value","Cross Sell / Up Sell","Total Opportunity Value","SF Stage","OPP"]].copy(); editable['Add to Proposal']=False; editable['Generate Proposal']=False
        editable['Value']=editable['Value'].map(brl); editable['Total Opportunity Value']=editable['Total Opportunity Value'].map(brl)
        edited=st.data_editor(editable[["Priority","Customer","Owner","Items in Quote","Value","Cross Sell / Up Sell","Add to Proposal","Total Opportunity Value","SF Stage","Generate Proposal","OPP"]],use_container_width=True,hide_index=True,disabled=["Priority","Customer","Owner","Items in Quote","Value","Cross Sell / Up Sell","Total Opportunity Value","SF Stage","OPP"],column_config={"Add to Proposal":st.column_config.CheckboxColumn("Add to Proposal"),"Generate Proposal":st.column_config.CheckboxColumn("Generate Proposal"),"OPP":None},key="workflow_editor")
        requested=edited[edited['Generate Proposal']]
        for _,er in requested.iterrows():
            rr=opps[opps.OPP==er.OPP].iloc[0]; pdf=proposal_pdf(rr,bool(er['Add to Proposal']))
            st.download_button(f"Download Proposal — {rr.Customer}",pdf,file_name=f"proposal_demo_{int(rr.OPP)}.pdf",mime="application/pdf",key=f"dl_{int(rr.OPP)}")
    if len(advanced):
        st.markdown("#### Advanced Stages — Proposal actions closed")
        av=advanced[["Priority","Customer","Owner","Items in Quote","Value","Cross Sell / Up Sell","Total Opportunity Value","SF Stage"]].copy(); av['Value']=av['Value'].map(brl); av['Total Opportunity Value']=av['Total Opportunity Value'].map(brl)
        st.dataframe(av,use_container_width=True,hide_index=True)
    if len(wf):
        sel=st.selectbox("Selected Opportunity",wf.OPP.tolist(),format_func=lambda z:f"{wf.loc[wf.OPP==z,'Customer'].iloc[0]} · {brl(wf.loc[wf.OPP==z,'Value'].iloc[0])}"); r=opps[opps.OPP==sel].iloc[0]
        st.markdown('<div class="section-title">Selected Opportunity — 360° View</div>',unsafe_allow_html=True)
        a,b,c,d,e=st.columns(5); a.metric("Priority",f"{risk_color(r.Priority)} {r.Priority}"); b.metric("Priority Score",f"{r.Score}/100"); c.metric("Value",brl(r.Value)); d.metric("SF Stage",r['SF Stage']); e.metric("Owner",r.Owner)
        tabs=st.tabs(["Overview","History","Suggested Products","Inventory","Interactions"])
        with tabs[0]: st.write(f"**Current demand:** {r['Items in Quote']}"); st.write(f"**Source:** {r.Source}")
        with tabs[1]: st.write("Demand received → Customer matched → Salesforce OPP created → Score calculated → Owner assigned. Demo activity history.")
        with tabs[2]: st.success(f"Cross Sell / Up Sell: {r['Cross Sell / Up Sell']}")
        with tabs[3]: st.write(f"Inventory driver: {r.Inventory}/20 · {risk_color(component_level(r.Inventory,20))} {component_level(r.Inventory,20)}")
        with tabs[4]: st.write(f"Latest interaction source: {r.Source}. Days waiting: {r['Days Waiting']}.")
        if r['SF Stage'] in ['Identify','Develop']:
            st.success("Commercial creation window open — optional Cross / Up Sell and initial proposal can be prepared.")
        elif r['SF Stage']=='Propose':
            st.warning("Initial proposal already sent. If customer requests price, volume or scope changes, use Review Proposal in the responsible activity queue.")
            if st.button("Review Proposal",use_container_width=True,key=f"review_{int(r.OPP)}"):
                st.download_button("Download Revised Proposal",proposal_pdf(r,True,True),file_name=f"revised_proposal_demo_{int(r.OPP)}.pdf",mime="application/pdf",key=f"revdl_{int(r.OPP)}")
        else: st.info("Proposal creation is closed at this Salesforce stage.")

elif page=="Fila Inteligente":
    st.markdown('<div class="section-title">Smart Priority — Explainable Commercial Prioritization</div>',unsafe_allow_html=True)
    q=opps.copy().sort_values('Score',ascending=False)
    for c,m in [("Revenue",30),("Conversion",25),("Inventory",20),("SLA",15),("Credit",10)]: q[c]=q[c].apply(lambda x:f"{risk_color(component_level(x,m))} {component_level(x,m)}")
    view=q[["Customer","Priority","Score","Revenue","Conversion","Inventory","SLA","Credit","SF Stage","Owner"]].rename(columns={"Score":"Priority Score"}); st.dataframe(view,use_container_width=True,hide_index=True)
    st.caption("Priority Score remains numeric (0–100). Components are classified visually: 🟢 Normal · 🟡 Alta · 🔴 Altíssima.")
    sel=st.selectbox("Explain Priority",opps.OPP.tolist(),format_func=lambda z:opps.loc[opps.OPP==z,'Customer'].iloc[0]); r=opps[opps.OPP==sel].iloc[0]
    st.markdown(f"**Priority Score: {r.Score}/100** · Revenue {r.Revenue}/30 · Conversion {r.Conversion}/25 · Inventory {r.Inventory}/20 · SLA {r.SLA}/15 · Credit {r.Credit}/10")
    with st.expander("What is behind Conversion?"):
        st.write("**Customer historical conversion (40%)** · **Product/family conversion (25%)** · **Purchase recency & recurrence (20%)** · **Demand maturity (15%)**.")
        st.caption("The V12 demo uses fictitious component points. In production, these signals would be calculated from governed CRM/ERP history.")
    with st.expander("Explain all Priority drivers"):
        st.write("**Revenue:** financial relevance of the opportunity. **Inventory:** availability/constraint signal. **SLA:** urgency and elapsed response time. **Credit:** commercial credit readiness. Each driver is explainable and governed; AI does not replace commercial judgment.")

elif page=="Growth Engine":
    st.markdown('<div class="section-title">Growth Engine — Proactive Revenue Creation</div>',unsafe_allow_html=True)
    seller=st.selectbox("Seller",["All"]+team.Seller.tolist(),key="growth_seller"); g=growth if seller=="All" else growth[growth.Seller==seller]
    c1,c2,c3,c4=st.columns(4); c1.metric("Growth Potential",brl(g['Growth Potential'].sum())); c2.metric("Signals",len(g)); c3.metric("Approached",int((g['Growth Stage']=='Approached').sum())); c4.metric("OPP Created",int((g['Growth Stage']=='OPP Created').sum()))
    c1,c2=st.columns(2)
    with c1: st.caption("Growth Funnel"); st.bar_chart(g['Growth Stage'].value_counts(),height=230)
    with c2: st.caption("Growth Potential by Seller"); st.bar_chart(g.groupby('Seller')['Growth Potential'].sum(),height=230)
    v=g[["Customer","Seller","Responsible","Type","Suggested Item","Qty","Growth Potential","Value Proposition","Growth Stage"]].copy(); v['Growth Potential']=v['Growth Potential'].map(brl); st.dataframe(v,use_container_width=True,hide_index=True)
    if len(g):
        idx=st.selectbox("Generate Text",g.index.tolist(),format_func=lambda i:f"{g.loc[i,'Customer']} — {g.loc[i,'Suggested Item']}");
        if st.button("Generate Text for WhatsApp / Email"):
            st.text_area("Suggested outreach",growth_message(g.loc[idx]),height=125)
    st.info("Growth does not create a proposal first. Filipe may proactively approach governed signals up to R$ 50K internal potential. Salesforce OPP is created only after customer interaction/interest.")

elif page=="Follow UP Comercial":
    st.markdown('<div class="section-title">Follow UP Comercial — Cadence & Pipeline Protection</div>',unsafe_allow_html=True)
    f=opps[opps['SF Stage'].isin(['Develop','Propose'])].copy()
    fs=st.selectbox("Responsible",["All","Filipe"]+team.Seller.tolist(),key="fup_owner")
    if fs!="All": f=f[f.Owner==fs]
    def fup_status(d): return "Overdue" if d>10 else "Today" if d in [2,5,10] else "Scheduled"
    f['FUP Status']=f['Days Waiting'].apply(fup_status); f['Aging Bucket']=pd.cut(f['Days Waiting'],[-1,2,5,10,999],labels=['0–2 days','3–5 days','6–10 days','>10 days'])
    c1,c2,c3,c4=st.columns(4); c1.metric("FUP Today",int((f['FUP Status']=='Today').sum())); c2.metric("Overdue FUP",int((f['FUP Status']=='Overdue').sum())); c3.metric("Pipeline Awaiting Response",brl(f.Value.sum())); c4.metric("FUP Compliance","90%")
    c1,c2=st.columns(2)
    with c1: st.caption("Pipeline Aging"); st.bar_chart(f.groupby('Aging Bucket',observed=False)['Value'].sum(),height=240)
    with c2: st.caption("FUP Load by Seller"); st.bar_chart(f.groupby('Seller')['Value'].sum(),height=240)
    v=f[["Customer","Value","Days Waiting","Owner","Seller","SF Stage","FUP Status","Next Best Action"]].copy(); v.Value=v.Value.map(brl); st.dataframe(v,use_container_width=True,hide_index=True)
    st.caption("Cadence: D+2 → D+5 → D+10 → every +5 days until closure. Order Promised and Lost Closed exit the active queue.")

elif page=="Account 360":
    st.markdown('<div class="section-title">Account 360 — Customer Commercial View</div>',unsafe_allow_html=True)
    cli=st.selectbox("Customer",sorted(opps.Customer.unique())); x=opps[opps.Customer==cli]; gx=growth[growth.Customer==cli]
    c1,c2,c3,c4=st.columns(4); c1.metric("Pipeline",brl(x[x['SF Stage'].isin(ACTIVE)].Value.sum())); c2.metric("OPPs",len(x)); c3.metric("Highest Priority Score",int(x.Score.max())); c4.metric("Growth Potential",brl(gx['Growth Potential'].sum()))
    st.dataframe(x[["Priority","SF Stage","Value","Items in Quote","Cross Sell / Up Sell","Owner","Next Best Action"]].assign(Value=lambda d:d.Value.map(brl)),use_container_width=True,hide_index=True)
    if len(gx): st.markdown("#### Growth Signals"); st.dataframe(gx,use_container_width=True,hide_index=True)

elif page=="Arquitetura":
    st.markdown('<div class="section-title">Commercial Architecture & Governance</div>',unsafe_allow_html=True)
    st.markdown("""**Reactive flow**  
Email / WhatsApp → Customer Match → **Salesforce Identify** → Enrichment → Priority Score → Owner → Contact → **Develop** → Proposal sent → **Propose** → PO received → automated validations → **human final confirmation** → **Order Promised** → Backoffice.

**Growth flow**  
Installed base + history + portfolio + inventory → Growth Signal → governed proactive outreach → customer interaction → **Salesforce Identify** → same commercial flow.

**Governance**  
The system prepares, prioritizes and executes governed volume. Pricing exceptions, credit issues, inventory constraints and financial commitments remain under human approval. Filipe owns governed Normal reactive opportunities up to R$ 10K, including their Follow UP, and proactively searches/approaches Growth signals up to R$ 50K. Handoff goes to the seller with the lowest **Commercial Load Index** when human judgment is required.""")

else:
    st.markdown('<div class="section-title">Presentation Mode — 20 Minute Business Case</div>',unsafe_allow_html=True)
    st.markdown("""### Inside Sales Smart Hub — From Reactive Requests to Intelligent Revenue Growth
**1. Smart Workflow | Productivity** — capture, Salesforce, SLA/FUP and controlled automation.  
**2. Smart Priority | Conversion** — explainable Revenue + Conversion + Inventory + SLA + Credit.  
**3. Smart Growth | Incremental Revenue** — identify demand before the call and create qualified commercial interest.

**Executive principle:** *Filipe absorbs governed volume up to R$ 10K, owns its Follow UP and prospects portfolio opportunities up to R$ 50K. Preserve sellers for commercial judgment and higher-impact decisions.*

**First 30 days:** D1–5 baseline & SLA · D6–10 queue & scoring pilot · D11–20 Follow UP & dashboards · D21–30 Growth Engine & controlled agent pilot.

**Management KPIs:** Open Pipeline · AOP Attainment · Conversion Rate · First Response SLA · FUP Compliance · Sales Cycle · Growth Adoption · Incremental Revenue · Revenue at Risk · Commercial Load Index.""")

# ---------------------------- Filipe, available everywhere ----------------------------
st.markdown("---")
st.markdown('<div class="section-title">💬 Filipe — Commercial Assistant</div>',unsafe_allow_html=True)
st.caption("Ask Filipe about any information available in this Smart Hub. Demo assistant is grounded only in the fictitious app dataset and does not execute financial/commercial commitments.")
fc1,fc2=st.columns([1,3]); ctx=fc1.selectbox("Seller context",["All"]+team.Seller.tolist(),key="filipe_ctx"); question=fc2.text_input("Ask Filipe",placeholder="Ex.: Quais são as demandas da Ana? | Quem tem menor Commercial Load? | Explique o AOP Gap")
if st.button("Ask Filipe",key="ask_filipe") and question:
    ans=filipe_answer(question,ctx); st.markdown(f'<div class="chat-answer"><b>Filipe</b><br>{ans}</div>',unsafe_allow_html=True)
