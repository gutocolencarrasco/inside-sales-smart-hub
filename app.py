import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime, timedelta, date
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Inside Sales Smart Hub V14", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# ---------------------------- Theme ----------------------------
st.markdown("""<style>
:root{--navy:#063b6f;--blue:#0878c9;--green:#18a36f;--yellow:#f4bd2a;--red:#df4343;--orange:#f28e2b;--purple:#7456b8;--ink:#18364f;--muted:#667d90;--line:#dce7ef;--bg:#f5f8fb}
.stApp{background:var(--bg)}.block-container{padding-top:.7rem;max-width:1580px;padding-bottom:5rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#073f75,#052d55)}[data-testid="stSidebar"] *{color:#fff}
.hero{background:white;border:1px solid var(--line);padding:15px 22px;border-radius:14px;margin-bottom:10px;box-shadow:0 2px 10px #14354a0b}
.hero h1{font-size:27px;margin:0;color:#0b2f50}.hero .smart{color:#0878c9}.hero p{margin:3px 0 0;color:#657c8f;font-size:12px}
.section-title{font-size:17px;font-weight:850;color:#0a3e6e;border-bottom:2px solid #e5eef5;padding-bottom:7px;margin:12px 0 9px}
.kpi{background:white;border:1px solid var(--line);border-radius:12px;padding:12px 14px;min-height:99px;box-shadow:0 2px 8px #173e5e0a}.kpi .label{font-size:10px;text-transform:uppercase;letter-spacing:.45px;color:#6c8294;font-weight:850}.kpi .value{font-size:24px;color:#14334c;font-weight:900;margin-top:6px}.kpi .sub{font-size:11px;color:#728697;margin-top:2px}
.mini{background:white;border:1px solid var(--line);border-radius:11px;padding:11px 12px}.mini b{color:#0b4b82}
.note{background:#eef6ff;border-left:4px solid var(--blue);padding:10px 12px;border-radius:9px;color:#24455d;font-size:12px}
.chat-answer{background:#eef6ff;border:1px solid #cfe5f8;border-radius:12px;padding:13px;color:#173b58}
div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:10px;border-radius:12px}
.stButton>button{border-radius:8px;font-weight:750}
</style>""", unsafe_allow_html=True)

AOP=4_000_000
STAGES=["Identify","Develop","Propose","Order Promised","Win Closed","Lost Closed"]
OPEN_STAGES=["Identify","Develop","Propose","Order Promised"]
ACTIVE_WORKFLOW=["Identify","Develop"]
OWNERS=["Ana","Bruno","Carla","Filipe"]

AGENTS = [
    ["Filipe","AI Sales Agent","Assistant • Reactive Sales ≤ R$10K • FUP • Growth 30–50/day","Active"],
    ["CRM Agent","Salesforce Orchestration","Structure demand • account match • create/update OPP • stage history","Active"],
    ["Priority Agent","Decision Engine","Priority Score • SLA • conversion • routing","Active"],
    ["Operations Agent","SAP Intelligence","Inventory • credit • availability • operational exceptions","API Ready"],
    ["Proposal Agent","Commercial Preparation","Pricing rules • optional Cross/Up Sell • proposal package","Active"],
]
AGENTS_DF = pd.DataFrame(AGENTS, columns=["Agent","Role","Scope","Status"])


def brl(v): return f"R$ {float(v):,.0f}".replace(",","X").replace(".",",").replace("X",".")
def pct(v): return f"{float(v):.1f}%".replace(".",",")
def priority(score): return "Altíssima" if score>=80 else "Alta" if score>=60 else "Normal"
def kpi(label,value,sub=""):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div><div class="sub">{sub}</div></div>',unsafe_allow_html=True)

def component_level(points,maxp):
    r=points/maxp
    return "Altíssima" if r>=.80 else "Alta" if r>=.60 else "Normal"
def component_icon(level): return {"Normal":"🟢","Alta":"🟡","Altíssima":"🔴"}.get(level,"⚪")

# ---------------------------- Demo data: 100% fictitious ----------------------------
BASE=[
[92001,"Hospital Horizonte","Ana",186000,"Develop",92,28,24,20,12,8,"Kit Preventivo Alpha — 10 un.","Sensor de Fluxo Pro — 2 un.",2,"Email",False],
[92002,"Rede Vida Nova","Bruno",74000,"Propose",78,22,20,18,10,8,"Sensor de Fluxo Pro — 3 un.","Contrato Preventivo 12M — 1 un.",5,"WhatsApp",True],
[92003,"Instituto Aurora","Carla",29500,"Propose",84,25,22,18,11,8,"Filtro Performance — 10 un.","Kit Preventivo Alpha — 1 un.",11,"Email",True],
[92004,"Hospital Monte Azul","Ana",128000,"Identify",66,24,14,10,10,8,"Módulo Eletrônico X — 3 un.","Contrato Preventivo 12M — 1 un.",1,"Email",False],
[92005,"Clínica Integra","Bruno",68000,"Develop",76,21,21,16,10,8,"Bateria Backup Plus — 5 un.","Upgrade Performance — 1 un.",7,"WhatsApp",False],
[92006,"Grupo Santa Luz","Carla",215000,"Propose",82,30,19,17,9,7,"Contrato Preventivo 12M — 1 un.","Upgrade Performance — 1 un.",3,"Email",True],
[92007,"Hospital Nova Esperança","Ana",99000,"Propose",88,26,23,20,12,7,"Kit Preventivo Alpha — 6 un.","Sensor de Fluxo Pro — 2 un.",16,"WhatsApp",False],
[92008,"Centro Médico Solaris","Bruno",47000,"Identify",54,17,12,5,11,9,"Válvula Inspiratória — 3 un.","Kit Preventivo Alpha — 1 un.",1,"Email",False],
[92009,"Rede Plena Saúde","Carla",83000,"Develop",79,23,22,18,9,7,"Sensor de Fluxo Pro — 4 un.","Contrato Preventivo 12M — 1 un.",4,"WhatsApp",False],
[92010,"Hospital Parque Central","Ana",152000,"Order Promised",73,27,17,13,9,7,"Upgrade Performance — 2 un.","Contrato Preventivo 12M — 1 un.",0,"Email",False],
[92011,"Clínica Vale Verde","Bruno",7800,"Identify",48,8,13,15,7,5,"Filtro Performance — 3 un.","Kit Preventivo Alpha — 1 un.",0,"WhatsApp",False],
[92012,"Centro Diagnóstico Orion","Carla",9400,"Develop",57,10,16,15,9,7,"Bateria Backup Plus — 1 un.","Filtro Performance — 2 un.",2,"WhatsApp",False],
[92013,"Hospital Bela Vista","Ana",4600,"Propose",52,7,15,17,8,5,"Filtro Performance — 2 un.","Kit Preventivo Alpha — 1 un.",5,"Email",False],
[92014,"Rede Saúde Prime","Bruno",56000,"Win Closed",86,25,22,20,11,8,"Kit Preventivo Alpha — 3 un.","—",0,"Email",False],
[92015,"Instituto Lumina","Carla",33000,"Lost Closed",61,16,18,12,8,7,"Sensor de Fluxo Pro — 2 un.","—",0,"Email",False],
[92016,"Hospital Porto Azul","Ana",118000,"Order Promised",81,25,20,18,11,7,"Contrato Preventivo 12M — 1 un.","—",0,"Email",False],
[92017,"Centro Clínico Atlas","Bruno",89000,"Win Closed",83,26,21,18,10,8,"Módulo Eletrônico X — 2 un.","—",0,"WhatsApp",False],
[92018,"Rede Integra Norte","Carla",41000,"Lost Closed",64,18,18,12,9,7,"Bateria Backup Plus — 2 un.","—",0,"Email",False],
]
COL=["OPP","Customer","Seller","Value","SF Stage","Score","Revenue","Conversion","Inventory","SLA","Credit","Items in Quote","Cross Sell / Up Sell","Days Waiting","Source","Needs Review"]


def next_fup_date(days_waiting):
    """Demo cadence: D+2 → D+5 → D+10 → every +5 days."""
    d = int(days_waiting)
    if d < 2:
        delta = 2 - d
    elif d < 5:
        delta = 5 - d
    elif d < 10:
        delta = 10 - d
    else:
        next_mark = ((d - 10) // 5 + 1) * 5 + 10
        delta = max(next_mark - d, 0)
    return date.today() + timedelta(days=delta)

# ---------- V14.4 FIX2 SCALE SCENARIO ----------
# 100 unique customers per owner:
# 30 in Workflow / Identify + 70 in FUP / Develop-Propose.
# Customer names are 100% fictitious and never repeat between Workflow and FUP.
def build_scaled_opportunity_scenario():
    owners = ["Ana","Bruno","Carla","Filipe"]
    prefixes = [
        "Centro Clínico","Hospital","Instituto","Clínica","Centro Médico",
        "Rede Hospitalar","Núcleo de Saúde","Unidade Médica","Complexo Clínico","Serviços Hospitalares"
    ]
    suffixes = [
        "Atlas","Aurora","Horizonte","Vértice","Pioneiro","Alvorada","Solaris","Planalto","Estrela","Vale Azul",
        "Jardins","Nova Vida","Integra","Prime","Central","Litoral","Montes","Veredas","Pontal","Sereno",
        "América","Bela Vista","São Lucas","Esperança","Vila Nova","Riviera","Primavera","Imperial","Nobre","União",
        "Aquarela","Liberdade","Ipê","Vitória","Harmonia","Progresso","Conexão","Excelência","Vanguarda","Essencial"
    ]
    products = [
        "Preventive Kit","Flow Sensor","Backup Battery","Inspiratory Valve",
        "Electronic Module","Patient Circuit","Consumables Pack","Service Contract",
        "Filter Kit","Accessory Set"
    ]
    sources = ["WhatsApp","Email","Service Call"]
    rows = []
    opp_id = 1000

    # Unique customer naming by owner + queue + sequential id guarantees no overlap.
    for owner_i, owner in enumerate(owners):
        # WORKFLOW: exactly 30 per owner, Identify only, no FUP started.
        for i in range(30):
            opp_id += 1
            customer = f"{prefixes[(i+owner_i)%len(prefixes)]} {suffixes[(i*3+owner_i)%len(suffixes)]} W{owner_i+1}-{i+1:02d}"
            value = 4500 + ((i * 7300 + owner_i * 4100) % 118000)
            priority = ["Normal","Alta","Altíssima"][(i + owner_i) % 3]
            item = products[(i + owner_i) % len(products)]
            optional = 0 if i % 3 else 2500 + ((i * 900) % 9000)
            rows.append({
                "OPP":opp_id,
                "Customer":customer,
                "Owner":owner,
                "Seller":owner,
                "Priority":priority,
                "Score":55 + ((i*7 + owner_i*3) % 44),
                "Revenue":["Normal","Alta","Altíssima"][(i+1+owner_i)%3],
                "Conversion":["Normal","Alta","Altíssima"][(i+2+owner_i)%3],
                "Inventory":["Normal","Alta","Altíssima"][(i+owner_i)%3],
                "SLA":["Normal","Alta","Altíssima"][(i+1)%3],
                "Credit":["Normal","Alta","Altíssima"][(i+2)%3],
                "Value":value,
                "SF Stage":"Identify",
                "FUP Status":"Not Started",
                "Days Waiting":i % 3,
                "Source":sources[(i+owner_i)%3],
                "Items in Quote":1 + (i % 5),
                "Cross Sell / Up Sell":item,
                "Optional Value":optional,
                "Needs Review":False,
                "Action":"First commercial contact",
                "Demand Description":f"Inbound request received via {sources[(i+owner_i)%3]} for {item}. Opportunity automatically created by the agent.",
                "Channel Detail":sources[(i+owner_i)%3]
            })

        # FUP: exactly 70 per owner, only Develop or Propose.
        for i in range(70):
            opp_id += 1
            customer = f"{prefixes[(i+owner_i+4)%len(prefixes)]} {suffixes[(i*5+owner_i+7)%len(suffixes)]} F{owner_i+1}-{i+1:02d}"
            stage = "Develop" if i % 2 == 0 else "Propose"
            waiting = 1 + ((i*2 + owner_i) % 24)
            fup_status = "Overdue" if waiting >= 6 and i % 3 != 0 else "On Time"
            value = 7000 + ((i * 9100 + owner_i * 6700) % 185000)
            priority = ["Normal","Alta","Altíssima"][(i*2 + owner_i) % 3]
            item = products[(i*2 + owner_i) % len(products)]
            optional = 0 if i % 4 else 3500 + ((i * 1100) % 14000)
            action = (
                "Review customer feedback and adjust proposal"
                if stage == "Propose"
                else "Follow up commercial discussion and advance scope"
            )
            rows.append({
                "OPP":opp_id,
                "Customer":customer,
                "Owner":owner,
                "Seller":owner,
                "Priority":priority,
                "Score":58 + ((i*5 + owner_i*4) % 41),
                "Revenue":["Normal","Alta","Altíssima"][(i+2+owner_i)%3],
                "Conversion":["Normal","Alta","Altíssima"][(i+owner_i)%3],
                "Inventory":["Normal","Alta","Altíssima"][(i+1+owner_i)%3],
                "SLA":["Normal","Alta","Altíssima"][(i+2)%3],
                "Credit":["Normal","Alta","Altíssima"][(i+1)%3],
                "Value":value,
                "SF Stage":stage,
                "FUP Status":fup_status,
                "Days Waiting":waiting,
                "Source":sources[(i+owner_i+1)%3],
                "Items in Quote":1 + (i % 6),
                "Cross Sell / Up Sell":item,
                "Optional Value":optional,
                "Needs Review":stage=="Propose" and i % 3 == 1,
                "Action":action,
                "Demand Description":f"Customer interaction already started. Commercial follow-up for {item}.",
                "Channel Detail":sources[(i+owner_i+1)%3]
            })

    df = pd.DataFrame(rows)
    df["Total Opportunity Value"] = df["Value"] + df["Optional Value"]
    df["Next FUP"] = df["Days Waiting"].apply(next_fup_date)
    return df

if "opps" not in st.session_state or len(st.session_state.opps) != 400:
    st.session_state.opps = build_scaled_opportunity_scenario()

opps=st.session_state.opps

# V14.4 FIX2 FIX2 — backward compatibility for older session-state datasets
driver_defaults = {
    "Revenue":"Alta",
    "Conversion":"Alta",
    "Inventory":"Normal",
    "SLA":"Alta",
    "Credit":"Normal"
}
for col, default_value in driver_defaults.items():
    if col not in opps.columns:
        opps[col] = default_value

# V14.3 commercial-stage governance

# V14.4 FIX2 commercial-stage governance
# Workflow = newly created opportunities from inbound WhatsApp / Email / Service Call.
# They remain in Identify until the seller actually starts commercial interaction.
workflow_mask = opps["SF Stage"].isin(["Identify","Develop"]) & opps["FUP Status"].eq("Not Started")
opps.loc[workflow_mask, "SF Stage"] = "Identify"

# FUP = customer interaction / negotiation has already started.
# Therefore active FUP can only be Develop or Propose.
fup_mask = opps["FUP Status"].isin(["On Time","Overdue"])
opps.loc[fup_mask & ~opps["SF Stage"].eq("Propose"), "SF Stage"] = "Develop"

st.session_state.opps = opps
if "Demand Description" not in opps.columns:
    opps["Demand Description"] = [
        "Customer requested preventive kit availability and commercial proposal.",
        "Customer requested sensor replacement and delivery timing.",
        "Customer asked for consumables quotation and availability.",
        "Technical call converted into commercial demand for electronic module.",
        "Customer requested backup battery replacement.",
        "Service discussion evolved into annual preventive contract opportunity.",
        "Customer requested preventive kit replenishment.",
        "Urgent request for inspiratory valve availability.",
        "Customer requested flow sensor quotation.",
        "Upgrade opportunity already in order process.",
        "Low-value consumables request received via WhatsApp.",
        "Battery replacement request with accessory opportunity.",
        "Consumables proposal already sent.",
        "Closed-won preventive kit opportunity.",
        "Closed-lost sensor opportunity.",
        "Service contract in order process.",
        "Closed-won module opportunity.",
        "Closed-lost battery opportunity.",
    ]
if "Channel Detail" not in opps.columns:
    opps["Channel Detail"] = opps["Source"].map({"Email":"Commercial email","WhatsApp":"WhatsApp request"}).fillna("Service call")
opps["Priority"]=opps.Score.map(priority)
# V14.4 FIX2 scaled demo preserves the assigned owner counts (30 Workflow + 70 FUP per owner).
opps["Optional Value"]=opps.apply(lambda r: round(float(r.Value)*0.12,2) if r["Cross Sell / Up Sell"]!="—" else 0,axis=1)
opps["Total Opportunity Value"]=opps["Value"]+opps["Optional Value"]


if "Action" not in opps.columns:
    opps["Action"] = opps.apply(
        lambda r: (
            "Review customer feedback / proposal adjustment"
            if r["SF Stage"] == "Propose"
            else "Contact customer and advance opportunity"
        ),
        axis=1
    )

if "Next FUP" not in opps.columns:
    opps["Next FUP"] = opps["Days Waiting"].apply(next_fup_date)

# Filipe always owns Growth: 40 actions today (fictitious), within <= R$50K each
customers=["Hospital Horizonte","Rede Vida Nova","Instituto Aurora","Hospital Monte Azul","Clínica Integra","Grupo Santa Luz","Hospital Nova Esperança","Centro Médico Solaris","Rede Plena Saúde","Hospital Parque Central","Clínica Vale Verde","Centro Diagnóstico Orion","Hospital Bela Vista","Rede Saúde Prime","Instituto Lumina","Hospital Porto Azul","Centro Clínico Atlas","Rede Integra Norte"]
items=[("Part","Kit Preventivo Alpha"),("Part","Sensor de Fluxo Pro"),("Service","Contrato Preventivo 12M"),("Part","Bateria Backup Plus"),("Service","Upgrade Performance")]
stages_growth=["Identified","Approached","Interacted","OPP Created"]
growth_rows=[]
for i in range(40):
    cust=customers[i%len(customers)]; typ,item=items[i%len(items)]; potential=12000+(i*1730)%37000
    stage=stages_growth[i%4]
    growth_rows.append([f"G-{1300+i}",cust,"Filipe",typ,item,1+(i%4),potential,stage,"Today", "Create value conversation before reactive demand"])
growth=pd.DataFrame(growth_rows,columns=["Growth ID","Customer","Responsible","Type","Suggested Item","Qty","Growth Potential","Growth Stage","Due","Value Proposition"])

team=pd.DataFrame([
["Ana",87,31.5,94,93,68],["Bruno",79,27.8,88,86,54],["Carla",84,29.4,91,90,62],["Filipe",86,34.0,97,96,42]],
columns=["Owner","Performance Index","Conversion Rate","First Response SLA","FUP Compliance","Commercial Load Index"])

# ---------------------------- Helpers ----------------------------
def filter_owner(df, owner, col="Owner"):
    return df if owner=="All" else df[df[col]==owner]

def stage_summary(df):
    rows=[]
    for s in STAGES:
        q=df[df["SF Stage"]==s]
        rows.append([s,len(q),float(q.Value.sum())])
    return pd.DataFrame(rows,columns=["SF Stage","OPPs","Value"])

def proposal_pdf(r, include_optional=True, revision=False):
    b=BytesIO(); styles=getSampleStyleSheet(); doc=SimpleDocTemplate(b,pagesize=A4,rightMargin=16*mm,leftMargin=16*mm,topMargin=16*mm,bottomMargin=16*mm)
    title="REVISED COMMERCIAL PROPOSAL" if revision else "COMMERCIAL PROPOSAL"
    story=[Paragraph(f"INSIDE SALES SMART HUB — {title}",styles['Title']),Spacer(1,5),Paragraph("DADOS 100% FICTÍCIOS / NÃO UTILIZAR COM CLIENTES",styles['Heading3']),Spacer(1,8),Paragraph(f"Customer: {r['Customer']} &nbsp;&nbsp; | &nbsp;&nbsp; Date: {datetime.now().strftime('%d/%m/%Y')} &nbsp;&nbsp; | &nbsp;&nbsp; OPP: DEMO-{int(r['OPP'])}",styles['BodyText']),Spacer(1,12)]
    main=float(r.Value); opt=float(r['Optional Value'])
    data=[["Código","Descrição","Qtd.","Valor Unitário","Valor Total"],["DEMO-001",r['Items in Quote'],"1",brl(main),brl(main)]]
    if include_optional and opt>0:
        data.append(["OPTIONAL",f"OPCIONAL — {r['Cross Sell / Up Sell']}","1",brl(opt),brl(opt)])
    t=Table(data,colWidths=[25*mm,78*mm,16*mm,29*mm,29*mm]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0b4f82')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#cbd8e3')),('VALIGN',(0,0),(-1,-1),'TOP'),('FONTSIZE',(0,0),(-1,-1),8),('BACKGROUND',(0,2),(-1,2),colors.HexColor('#fff7d6')) if len(data)>2 else ('FONTSIZE',(0,0),(-1,-1),8)]))
    story += [t,Spacer(1,10),Paragraph(f"Main Proposal Value: <b>{brl(main)}</b>",styles['BodyText'])]
    if include_optional and opt>0:
        story += [Paragraph(f"Optional Items: <b>{brl(opt)}</b>",styles['BodyText']),Paragraph(f"Total if Optional Items are Accepted: <b>{brl(main+opt)}</b>",styles['BodyText'])]
    story += [Spacer(1,10),Paragraph("Payment, delivery and commercial conditions are fictitious for MVP demonstration. Customer-facing proposal does not display list price, discount, margin or COGS.",styles['BodyText'])]
    doc.build(story); b.seek(0); return b

def growth_message(r):
    if r['Type']=="Service": return f"Olá. Pela sua base instalada, identificamos uma oportunidade relacionada a {r['Suggested Item']} para aumentar disponibilidade, reduzir paradas não planejadas e trazer maior previsibilidade à manutenção. Posso avaliar essa necessidade com você?"
    return f"Olá. Identificamos uma oportunidade relacionada a {r['Suggested Item']}. Pode fazer sentido manter {int(r['Qty'])} unidade(s) em estoque para reduzir o risco de parada enquanto uma nova peça é adquirida e entregue. Posso avaliar essa necessidade com você?"

def filipe_answer(q, owner):
    txt=q.lower(); od=filter_owner(opps,owner); open_od=od[od['SF Stage'].isin(OPEN_STAGES)]
    if "demanda" in txt or "o que" in txt and "hoje" in txt:
        new=len(od[od['SF Stage']=='Identify']); fup=od[(od['SF Stage'].isin(['Develop','Propose'])) & (od['Days Waiting']>0)]; nego=od[(od['SF Stage']=='Propose') & (od['Needs Review'])]; grow=growth if owner in ['All','Filipe'] else growth.iloc[0:0]
        return f"{owner}: {new} New Opportunities, {len(fup)} FUP actions ({brl(fup.Value.sum())}), {len(nego)} Proposal Reviews dentro do FUP e {len(grow)} Growth actions hoje."
    if "pipeline" in txt: return f"Open Pipeline de {owner}: {brl(open_od.Value.sum())} em {len(open_od)} oportunidades."
    if "growth" in txt: return f"Filipe possui {len(growth)} Growth actions planejadas hoje, com {brl(growth['Growth Potential'].sum())} de potencial interno. OPP só nasce após interação/interesse do cliente."
    if "fup" in txt: 
        f=od[od['SF Stage'].isin(['Develop','Propose'])]; ov=f[f['Days Waiting']>10]; return f"{owner}: {len(f)} FUPs, sendo {len(ov)} overdue e {brl(ov.Value.sum())} em atraso."
    return "Posso responder sobre demandas do dia, Open Pipeline, FUP, Proposal Review, Growth, Salesforce stages e performance usando os dados fictícios deste Smart Hub."

# ---------------------------- Navigation ----------------------------
st.sidebar.markdown("## PHILIPS\n**Health Systems**")
st.sidebar.markdown('<span style="font-size:12px;opacity:.75">INSIDE SALES SMART HUB</span><br><span style="display:inline-block;margin-top:6px;background:#ffffff22;border:1px solid #ffffff55;border-radius:12px;padding:2px 9px;font-size:11px;font-weight:850">VERSION 14.4 FIX2</span>',unsafe_allow_html=True)
page=st.sidebar.radio("Navigation",["Executive Dashboard","Account 360","Management"],label_visibility="collapsed")

# Compact Salesforce context, always exact stage order
ss=stage_summary(opps)
open_value=float(opps[opps['SF Stage'].isin(OPEN_STAGES)].Value.sum()); open_count=int(opps['SF Stage'].isin(OPEN_STAGES).sum())
st.sidebar.markdown("---")
st.sidebar.markdown(f'<div style="font-size:14px;font-weight:850">SALESFORCE PIPELINE</div><div style="font-size:22px;font-weight:900;margin-top:4px">{brl(open_value)}</div><div style="font-size:11px;opacity:.8;margin-bottom:8px">{open_count} Open OPPs · AOP Coverage {pct(open_value/AOP*100)}</div>',unsafe_allow_html=True)
for s in STAGES:
    r=ss[ss['SF Stage']==s].iloc[0]
    st.sidebar.markdown(f'<div style="display:flex;justify-content:space-between;font-size:11px;padding:2px 0"><b>{s}</b><span>{int(r.OPPs)} · {brl(r.Value)}</span></div>',unsafe_allow_html=True)
st.sidebar.progress(min(open_value/AOP,1.0))
st.sidebar.markdown("---")
st.sidebar.markdown('<div style="font-size:12px;font-weight:850;margin-bottom:5px">AI AGENTS</div>',unsafe_allow_html=True)
st.sidebar.markdown('<div style="font-size:10px;line-height:1.65;opacity:.92">● Filipe — Active<br>● CRM Agent — Active<br>● Priority Agent — Active<br>● Operations Agent — SAP API Ready<br>● Proposal Agent — Active</div>',unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>INSIDE SALES <span class="smart">SMART HUB</span></h1><p>One dashboard. One commercial operating rhythm. · V14.4 FIX2 · 100% fictitious demo data</p></div>',unsafe_allow_html=True)

# ---------------------------- Executive Dashboard ----------------------------
if page=="Executive Dashboard":
    st.markdown('<div class="section-title">Executive Sales Dashboard</div>',unsafe_allow_html=True)
    owner=st.selectbox("Owner",["All"]+OWNERS,index=0,key="owner_filter")
    od=filter_owner(opps,owner); open_od=od[od['SF Stage'].isin(OPEN_STAGES)]
    closed_od=od[od['SF Stage'].isin(['Win Closed','Lost Closed'])]
    won_od=od[od['SF Stage']=='Win Closed']; lost_od=od[od['SF Stage']=='Lost Closed']
    fup_od=od[od['SF Stage'].isin(['Develop','Propose'])].copy(); fup_od['FUP Status']=fup_od['Days Waiting'].apply(lambda d:'Overdue' if d>10 else ('Today' if d in [2,5,10] else 'Scheduled'))
    overdue=fup_od[fup_od['FUP Status']=='Overdue']
    negotiation=od[(od['SF Stage']=='Propose') & (od['Needs Review'])]
    growth_od=growth if owner in ['All','Filipe'] else growth.iloc[0:0]
    revenue_risk=open_od[(open_od['Priority']=='Altíssima') & ((open_od['Inventory']<16)|(open_od['Days Waiting']>10))].Value.sum()
    win_rate=(len(won_od)/len(closed_od)*100) if len(closed_od) else 0
    conv=float(team.loc[team.Owner==owner,'Conversion Rate'].iloc[0]) if owner in OWNERS else 30.7

    cols=st.columns(7)
    metrics=[
        ("Open Pipeline",brl(open_od.Value.sum()),f"{len(open_od)} open OPPs"),
        ("AOP Attainment",pct((won_od.Value.sum()+open_od.Value.sum())/AOP*100),f"AOP {brl(AOP)}"),
        ("Conversion Rate",pct(conv),"Commercial effectiveness"),
        ("Revenue at Risk",brl(revenue_risk),"High priority exposure"),
        ("Overdue FUP",str(len(overdue)),brl(overdue.Value.sum())),
        ("Growth Actions",str(len(growth_od)),brl(growth_od['Growth Potential'].sum()) if len(growth_od) else "Filipe only"),
        ("Win Rate",pct(win_rate),f"{len(won_od)} Won / {len(lost_od)} Lost"),
    ]
    for c,v in zip(cols,metrics):
        with c:kpi(*v)

    st.markdown('<div class="section-title">Executive Analytics</div>',unsafe_allow_html=True)
    c1,c2,c3=st.columns([1.2,1,1])
    with c1:
        s=stage_summary(od)
        chart=alt.Chart(s).mark_bar(cornerRadiusEnd=5).encode(y=alt.Y('SF Stage:N',sort=STAGES,title=None),x=alt.X('Value:Q',title='Pipeline Value'),color=alt.Color('SF Stage:N',legend=None,scale=alt.Scale(domain=STAGES,range=['#5da5da','#4e79a7','#f2b134','#8b6bb1','#34a66f','#d95555'])),tooltip=['SF Stage','OPPs',alt.Tooltip('Value:Q',format=',.0f')]).properties(height=250,title='Salesforce Funnel — exact stage order')
        st.altair_chart(chart,use_container_width=True)
    with c2:
        po=opps[opps['SF Stage'].isin(OPEN_STAGES)].groupby('Owner',as_index=False)['Value'].sum()
        if owner!='All': po=po[po.Owner==owner]
        chart=alt.Chart(po).mark_bar(cornerRadiusTopLeft=4,cornerRadiusTopRight=4,color='#0878c9').encode(x=alt.X('Owner:N',title=None),y=alt.Y('Value:Q',title='Open Pipeline'),tooltip=['Owner',alt.Tooltip('Value:Q',format=',.0f')]).properties(height=250,title='Open Pipeline by Owner')
        st.altair_chart(chart,use_container_width=True)
    with c3:
        pm=open_od['Priority'].value_counts().reindex(['Altíssima','Alta','Normal']).fillna(0).reset_index(); pm.columns=['Priority','OPPs']
        chart=alt.Chart(pm).mark_arc(innerRadius=55).encode(theta='OPPs:Q',color=alt.Color('Priority:N',scale=alt.Scale(domain=['Altíssima','Alta','Normal'],range=['#df4343','#f4bd2a','#18a36f']),legend=alt.Legend(title=None)),tooltip=['Priority','OPPs']).properties(height=250,title='Priority Mix')
        st.altair_chart(chart,use_container_width=True)

    c1,c2,c3=st.columns(3)
    with c1:
        buckets=pd.cut(fup_od['Days Waiting'],[-1,2,5,10,999],labels=['0–2 days','3–5 days','6–10 days','>10 days']); aging=fup_od.assign(Bucket=buckets).groupby('Bucket',observed=False,as_index=False)['Value'].sum()
        chart=alt.Chart(aging).mark_bar(color='#f28e2b').encode(x=alt.X('Bucket:N',sort=['0–2 days','3–5 days','6–10 days','>10 days'],title=None),y=alt.Y('Value:Q',title='Pipeline Value'),tooltip=['Bucket',alt.Tooltip('Value:Q',format=',.0f')]).properties(height=220,title='FUP Aging')
        st.altair_chart(chart,use_container_width=True)
    with c2:
        perf=team if owner=='All' else team[team.Owner==owner]
        chart=alt.Chart(perf).mark_bar(color='#7456b8').encode(x=alt.X('Owner:N',title=None),y=alt.Y('Performance Index:Q',scale=alt.Scale(domain=[0,100]),title='Index'),tooltip=['Owner','Performance Index','FUP Compliance','Commercial Load Index']).properties(height=220,title='Performance Index')
        st.altair_chart(chart,use_container_width=True)
    with c3:
        gcounts=growth['Growth Stage'].value_counts().reindex(['Identified','Approached','Interacted','OPP Created']).fillna(0).reset_index(); gcounts.columns=['Growth Stage','Actions']
        if owner not in ['All','Filipe']: gcounts['Actions']=0
        chart=alt.Chart(gcounts).mark_bar(color='#18a36f').encode(x=alt.X('Growth Stage:N',sort=['Identified','Approached','Interacted','OPP Created'],title=None),y=alt.Y('Actions:Q',title='Actions'),tooltip=['Growth Stage','Actions']).properties(height=220,title='Filipe Growth Funnel — 30–50 actions/day')
        st.altair_chart(chart,use_container_width=True)

    st.markdown('<div class="section-title">Daily Commercial Queues</div>',unsafe_allow_html=True)
    scenario_owner = od
    workflow_count = len(scenario_owner[(scenario_owner["SF Stage"].eq("Identify")) & (scenario_owner["FUP Status"].eq("Not Started"))])
    fup_count = len(scenario_owner[(scenario_owner["SF Stage"].isin(["Develop","Propose"])) & (scenario_owner["FUP Status"].isin(["On Time","Overdue"]))])
    qc1,qc2,qc3=st.columns(3)
    qc1.metric("Workflow Customers", workflow_count, "30 per seller" if owner!="All" else "120 total")
    qc2.metric("FUP Customers", fup_count, "70 per seller" if owner!="All" else "280 total")
    qc3.metric("Unique Active Customers", workflow_count+fup_count, "No Workflow/FUP duplication")
    tabs=st.tabs(["Workflow","FUP + Proposal Review","Growth"])

    with tabs[0]:
        st.caption("Workflow contains only newly created inbound opportunities in Identify. They came from WhatsApp, Email or Service Call and have not yet entered commercial negotiation.")
        wf=od[(od['SF Stage'].eq('Identify')) & (od['FUP Status'].eq('Not Started'))].copy()
        if len(wf):
            view=wf[["OPP","Priority","Customer","Owner","Demand Description","Items in Quote","Value","Cross Sell / Up Sell","Optional Value","Total Opportunity Value","SF Stage"]].copy()
            view['Add to Proposal']=False
            view['Generate Proposal']=False
            view['Value']=view.Value.map(brl)
            view['Optional Value']=view['Optional Value'].map(brl)
            view['Total Opportunity Value']=view['Total Opportunity Value'].map(brl)
            edited=st.data_editor(
                view,
                use_container_width=True,
                hide_index=True,
                disabled=['OPP','Priority','Customer','Owner','Demand Description','Items in Quote','Value','Cross Sell / Up Sell','Optional Value','Total Opportunity Value','SF Stage'],
                column_config={
                    'OPP':None,
                    'Demand Description':st.column_config.TextColumn('Demand / Call Description',width='large'),
                    'Add to Proposal':st.column_config.CheckboxColumn('Add to Proposal'),
                    'Generate Proposal':st.column_config.CheckboxColumn('Generate Proposal')
                },
                key=f"wf_{owner}"
            )
            req=edited[edited['Generate Proposal']]
            for _,er in req.iterrows():
                rr=opps[opps.OPP==er.OPP].iloc[0]
                st.download_button(
                    f"Download Proposal — {rr.Customer}",
                    proposal_pdf(rr,bool(er['Add to Proposal'])),
                    file_name=f"proposal_demo_{int(rr.OPP)}.pdf",
                    mime='application/pdf',
                    key=f"p_{owner}_{int(rr.OPP)}"
                )
        else:
            st.info("No Identify opportunities waiting for first commercial interaction for this owner.")

    with tabs[1]:
        st.caption("All follow-up and post-proposal negotiation live here. The seller can edit the Action and define the Next FUP date directly in the table.")
        f=fup_od.copy()
        if len(f):
            f['Opportunity Value']=f.Value.map(brl)
            f['Action']=f['Action'].fillna("")
            f['Next FUP']=pd.to_datetime(f['Next FUP']).dt.date

            fup_view=f[['OPP','Owner','Customer','SF Stage','Opportunity Value','Days Waiting','FUP Status','Action','Next FUP']].copy()

            fup_edit=st.data_editor(
                fup_view,
                use_container_width=True,
                hide_index=True,
                disabled=['OPP','Owner','Customer','SF Stage','Opportunity Value','Days Waiting','FUP Status'],
                column_config={
                    'OPP':None,
                    'Action':st.column_config.TextColumn(
                        'Action',
                        help='Editable field for the seller to describe the next commercial action.',
                        width='large'
                    ),
                    'Next FUP':st.column_config.DateColumn(
                        'Next FUP',
                        help='Editable date for the next follow-up.',
                        format='DD/MM/YYYY'
                    )
                },
                key=f"fup_editor_{owner}"
            )

            if st.button("Save FUP Updates", key=f"save_fup_{owner}"):
                for _,row in fup_edit.iterrows():
                    idx=opps.index[opps.OPP==row.OPP]
                    if len(idx):
                        opps.loc[idx,'Action']=row['Action']
                        opps.loc[idx,'Next FUP']=row['Next FUP']
                st.session_state.opps=opps
                st.success("FUP actions and next follow-up dates updated in the Smart Hub demo.")

            st.markdown("#### Proposal Adjustment")
            st.caption("If the customer requests price, volume or scope changes after the proposal is sent, the review stays inside FUP — there is no separate Negotiation queue.")
            n=f[f['SF Stage'].eq('Propose')].copy()

            if len(n):
                pick=st.selectbox(
                    'Opportunity for Proposal Review',
                    n.OPP.tolist(),
                    format_func=lambda z:n.loc[n.OPP==z,'Customer'].iloc[0],
                    key=f"rev_{owner}"
                )
                rr=n[n.OPP==pick].iloc[0]
                review_type=st.selectbox(
                    "Adjustment Type",
                    ["Price","Volume","Scope","Price / Volume / Scope"],
                    key=f"review_type_{owner}_{int(pick)}"
                )
                review_note=st.text_area(
                    "Proposal Adjustment Notes",
                    value=str(rr['Action']) if pd.notna(rr['Action']) else "",
                    placeholder="Ex.: Customer requested 8 units instead of 5 and asked for revised commercial conditions.",
                    key=f"review_note_{owner}_{int(pick)}"
                )
                cpa1,cpa2=st.columns([1,1])
                with cpa1:
                    if st.button("Update FUP Action",key=f"update_action_{owner}_{int(pick)}"):
                        idx=opps.index[opps.OPP==pick]
                        if len(idx):
                            opps.loc[idx,'Action']=f"{review_type}: {review_note}".strip()
                            st.session_state.opps=opps
                            st.success("Proposal review registered as the FUP action.")
                with cpa2:
                    st.download_button(
                        'Download Revised Proposal',
                        proposal_pdf(rr,True,True),
                        file_name=f"revised_proposal_demo_{int(rr.OPP)}.pdf",
                        mime='application/pdf',
                        key=f"rd_{owner}_{int(rr.OPP)}"
                    )
            else:
                st.info("No Propose-stage opportunities for proposal review in this filter.")
        else:
            st.info("No FUP actions for this owner.")

    with tabs[2]:
        st.caption("Growth is always executed by Filipe. Target operating rhythm: 30–50 proactive portfolio actions/day. A signal becomes a Salesforce opportunity only after customer interaction/interest.")
        if owner not in ['All','Filipe']:
            st.info("Growth is owned by Filipe. Select All or Filipe to view the Growth queue.")
        else:
            g=growth.copy()
            gv=g[['Growth ID','Customer','Responsible','Type','Suggested Item','Qty','Growth Potential','Growth Stage','Due']].copy()
            gv['Growth Potential']=gv['Growth Potential'].map(brl)
            st.dataframe(gv,use_container_width=True,hide_index=True,height=370)
            idx=st.selectbox('Generate Outreach Text',g.index.tolist(),format_func=lambda i:f"{g.loc[i,'Customer']} — {g.loc[i,'Suggested Item']}",key='gtxt')
            if st.button('Generate Text',key='gbutton'):
                st.text_area('Suggested WhatsApp / Email',growth_message(g.loc[idx]),height=110)

    st.markdown('<div class="section-title">AI Demand Intake & Agent Orchestration</div>',unsafe_allow_html=True)
    st.caption("The seller does not fill a Salesforce form. The Hub interprets the incoming demand, completes the available context automatically and asks only for missing mandatory information.")

    ai1,ai2=st.columns([1.45,1.0])
    with ai1:
        st.markdown("#### Incoming Demand")
        incoming_text=st.text_area(
            "Call / E-mail / WhatsApp content",
            value="Centro Clínico Atlas solicita 3 unidades do kit preventivo com urgência para reposição.",
            height=115,
            key="ai_incoming_demand"
        )
        incoming_channel=st.selectbox("Detected / informed channel",["Service Call","Email","WhatsApp"],key="ai_incoming_channel")
        if st.button("Run AI Intake",type="primary",key="run_ai_intake"):
            st.session_state["ai_intake_done"]=True

    with ai2:
        st.markdown("#### Agent Status")
        status_rows=[
            ["CRM Agent","Ready","Account match • demand • Salesforce"],
            ["Operations Agent","Ready","SAP inventory • credit"],
            ["Priority Agent","Ready","Score • SLA • routing"],
            ["Filipe","Ready","Reactive • FUP • Growth"],
            ["Proposal Agent","Standby","Proposal when applicable"],
        ]
        st.dataframe(pd.DataFrame(status_rows,columns=["Agent","Status","Action"]),use_container_width=True,hide_index=True)

    if st.session_state.get("ai_intake_done",False):
        st.markdown("#### Agent Orchestration Result")
        r1,r2,r3,r4=st.columns(4)
        with r1:
            st.success("CRM Agent")
            st.markdown("**Customer:** Centro Clínico Atlas  \n**Account:** Matched ✓  \n**Demand:** Structured ✓  \n**SF Stage:** Identify")
        with r2:
            st.info("Operations Agent")
            st.markdown("**Inventory:** Available ✓  \n**Credit:** Released ✓  \n**SAP:** API-ready lookup")
        with r3:
            st.warning("Priority Agent")
            st.markdown("**Score:** 82 / 100  \n**Priority:** Alta  \n**Routing:** Human seller")
        with r4:
            st.info("Commercial Routing")
            st.markdown("**Assigned to:** Ana  \n**Next Action:** Contact customer  \n**FUP:** Not started")

        sf_record=pd.DataFrame([{
            "Customer":"Centro Clínico Atlas",
            "Channel":incoming_channel,
            "Demand Type":"Part",
            "Demand Description":incoming_text,
            "Estimated Value":"R$ 25.000",
            "Owner":"Ana",
            "Salesforce Stage":"Identify",
            "Priority Score":82,
            "Priority":"Alta"
        }])
        st.markdown("##### Structured Salesforce Record")
        st.dataframe(sf_record,use_container_width=True,hide_index=True)
        st.success("The opportunity is prepared automatically. Human intervention is required only when mandatory information or commercial judgment is missing.")
        st.caption("Demo behavior: Salesforce and SAP are represented as API-ready integrations; no live Philips write is claimed.")

    st.markdown('<div class="section-title">Priority Explainability</div>',unsafe_allow_html=True)
    q=open_od.sort_values('Score',ascending=False).head(8).copy()
    for c,m in [('Revenue',30),('Conversion',25),('Inventory',20),('SLA',15),('Credit',10)]: q[c]=q[c].apply(lambda x:f"{component_icon(component_level(x,m))} {component_level(x,m)}")
    st.dataframe(q[['Customer','Owner','Score','Revenue','Conversion','Inventory','SLA','Credit','SF Stage']].rename(columns={'Score':'Priority Score'}),use_container_width=True,hide_index=True)
    st.caption("Priority Score remains numeric (0–100). Revenue, Conversion, Inventory, SLA and Credit are visually classified. Conversion is composed of customer historical conversion (40%), product/family conversion (25%), purchase recency & recurrence (20%) and demand maturity (15%).")

# ---------------------------- Account 360 ----------------------------
elif page=="Account 360":
    st.markdown('<div class="section-title">Account 360</div>',unsafe_allow_html=True)
    cli=st.selectbox('Customer',sorted(opps.Customer.unique())); x=opps[opps.Customer==cli]; gx=growth[growth.Customer==cli]
    c1,c2,c3,c4=st.columns(4); c1.metric('Open Pipeline',brl(x[x['SF Stage'].isin(OPEN_STAGES)].Value.sum())); c2.metric('OPPs',len(x)); c3.metric('Highest Priority Score',int(x.Score.max())); c4.metric('Growth Signals',len(gx))
    st.dataframe(x[['Priority','SF Stage','Value','Items in Quote','Cross Sell / Up Sell','Owner']].assign(Value=lambda d:d.Value.map(brl)),use_container_width=True,hide_index=True)
    if len(gx):
        st.markdown('#### Filipe Growth Signals'); y=gx.copy(); y['Growth Potential']=y['Growth Potential'].map(brl); st.dataframe(y,use_container_width=True,hide_index=True)

# ---------------------------- Management ----------------------------
else:
    st.markdown('<div class="section-title">Management & Governance</div>',unsafe_allow_html=True)
    tab1,tab2=st.tabs(['Architecture','Presentation Mode'])
    with tab1:
        st.markdown("""**Salesforce stage order — always:**  
**Identify → Develop → Propose → Order Promised → Win Closed → Lost Closed**

**Reactive sales**  
Incoming call / Email / WhatsApp → structured OPP in **Identify** → enrichment → Priority Score → owner. Governed **Normal OPPs ≤ R$10K** are owned by **Filipe**, including their FUP. Higher-value or higher-priority opportunities remain with human sellers.

**Growth**  
Filipe executes **30–50 proactive actions/day** across the installed-base portfolio. A Growth Signal is *not* a Salesforce OPP. Only when the customer interacts or demonstrates interest is an OPP automatically created in **Identify**.

**Governance**  
Pricing exceptions, credit issues, inventory constraints, out-of-policy negotiations and final commercial commitments remain under human approval. Filipe automates governed volume and preserves seller time for higher-value judgment.""")
    with tab2:
        st.markdown("""### Inside Sales Smart Hub — From Reactive Requests to Intelligent Revenue Growth
**1. Smart Workflow | Productivity** — organize inbound demand and commercial creation.  
**2. Smart Priority | Conversion** — explainable score and focus.  
**3. Smart Growth | Incremental Revenue** — Filipe creates demand before the next call.

**Executive principle:** *Automate governed volume. Preserve human sellers for commercial judgment and higher-impact decisions.*

**Operational rhythm:** one Executive Dashboard, one owner filter, three queues: **Workflow | FUP + Proposal Review | Growth**.

**V14 transformation layer:** five coordinated agents — Filipe, CRM Agent, Priority Agent, Operations Agent and Proposal Agent — with Salesforce and SAP API-ready integration and human governance at financial-risk decisions.""")

# ---------------------------- Filipe everywhere ----------------------------
st.markdown('---')
st.markdown('<div class="section-title">💬 Filipe — AI Sales Assistant & Agent</div>',unsafe_allow_html=True)
fc1,fc2=st.columns([1,3]); fctx=fc1.selectbox('Owner context',["All"]+OWNERS,key='fctx'); q=fc2.text_input('Ask Filipe',placeholder='Ex.: O que eu preciso fazer hoje? | Quais são as demandas da Ana? | Quantos Growth actions você tem hoje?')
if st.button('Ask Filipe',key='ask') and q:
    st.markdown(f'<div class="chat-answer"><b>Filipe</b><br>{filipe_answer(q,fctx)}</div>',unsafe_allow_html=True)
