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

st.set_page_config(page_title="Inside Sales Smart Hub V15", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

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
OPEN_STAGES=["Identify","Develop","Propose"]
ACTIVE_WORKFLOW=["Identify"]
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


# ---------------------------- V15 transactional helpers ----------------------------
def stage_bucket(stage):
    if stage == "Identify":
        return "Workflow"
    if stage in ["Develop","Propose"]:
        return "FUP"
    if stage in ["Order Promised","Win Closed"]:
        return "Orders / Won"
    if stage == "Lost Closed":
        return "Lost"
    return "Other"

def queue_sort(df):
    """Priority Score desc; tie-break SLA criticality, value and waiting days."""
    if df.empty:
        return df
    x=df.copy()
    level_rank={"Normal":1,"Alta":2,"Altíssima":3}
    x["_sla_rank"]=x["SLA"].map(level_rank).fillna(0)
    x["_value_num"]=pd.to_numeric(x["Value"],errors="coerce").fillna(0)
    x["_wait_num"]=pd.to_numeric(x["Days Waiting"],errors="coerce").fillna(0)
    return x.sort_values(
        ["Score","_sla_rank","_value_num","_wait_num"],
        ascending=[False,False,False,False]
    ).drop(columns=["_sla_rank","_value_num","_wait_num"])


def cross_sell_recommendation(row):
    """Explainable fictitious recommendation based on demo customer profile signals."""
    main=str(row.get("Main Item",""))
    mapping={
        "Patient Circuit":("Preventive Kit","Cross Sell","High Fit",
            "The customer profile indicates recurring use of patient circuits and preventive consumables. Adding a preventive kit can reduce emergency replacement risk and support equipment availability."),
        "Flow Sensor":("Preventive Kit","Cross Sell","High Fit",
            "Purchase recurrence in the same maintenance family suggests a preventive kit as a complementary item, reducing the risk of an additional intervention."),
        "Backup Battery":("Service Contract","Cross Sell","Medium Fit",
            "The installed-base profile suggests value in combining backup power availability with planned service coverage and greater maintenance predictability."),
        "Inspiratory Valve":("Patient Circuit","Cross Sell","High Fit",
            "The requested component is commonly associated with the same respiratory circuit maintenance context. The additional item can reduce a second purchasing cycle."),
        "Electronic Module":("Service Contract","Cross Sell","High Fit",
            "The higher-complexity component and service history indicate an opportunity to offer planned service coverage and reduce unplanned downtime."),
        "Preventive Kit":("Filter Kit","Cross Sell","High Fit",
            "The customer's preventive-maintenance profile indicates complementary filter consumption. Including the filter kit can consolidate the maintenance need in one commercial cycle."),
        "Consumables Pack":("Preventive Kit","Up Sell","Medium Fit",
            "Recurring consumables demand indicates potential to broaden the preventive package and increase stock coverage for the customer."),
        "Service Contract":("Upgrade Package","Up Sell","Medium Fit",
            "The service relationship creates an opportunity to evaluate installed-base modernization and additional coverage."),
        "Filter Kit":("Preventive Kit","Cross Sell","High Fit",
            "The maintenance profile suggests filters and preventive kits are complementary needs within the same service cycle."),
        "Accessory Set":("Service Contract","Cross Sell","Medium Fit",
            "The installed-base and accessory demand suggest an opportunity to add planned service coverage and improve equipment availability.")
    }
    item,kind,fit,reason=mapping.get(main,(
        "Preventive Kit","Cross Sell","Medium Fit",
        "Purchase history, installed-base profile and portfolio affinity indicate a complementary preventive-maintenance opportunity."
    ))
    # Fictitious commercial suggestion; seller retains decision.
    qty=max(1,min(int(row.get("Quantity",1)),3))
    unit=3900.0 if "Kit" in item else 7200.0
    return {"item":item,"type":kind,"fit":fit,"reason":reason,"qty":qty,"unit":unit}

def create_change_ticket(opp_id, owner, changes, action_text):
    """Demo Salesforce mirror: creates a traceable activity/ticket for API sync."""
    if "activity_log" not in st.session_state:
        st.session_state.activity_log=[]
    if "sf_sync_queue" not in st.session_state:
        st.session_state.sf_sync_queue=[]
    ticket=f"SF-{datetime.now().strftime('%H%M%S')}-{int(opp_id)}"
    now=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    change_text="; ".join([f"{k}: {v[0]} → {v[1]}" for k,v in changes.items()]) if changes else "Commercial action updated"
    record={
        "Ticket":ticket,"Date/Time":now,"OPP":int(opp_id),"Owner":owner,
        "Action":action_text,"Changes":change_text,"SF Sync Status":"Queued / API-ready"
    }
    st.session_state.activity_log.insert(0,record)
    st.session_state.sf_sync_queue.insert(0,record.copy())
    return ticket

def update_opportunity(opp_id, updates, action_text):
    idx=opps.index[opps["OPP"]==opp_id]
    if not len(idx):
        return None, {}
    i=idx[0]
    changes={}
    for field,new_value in updates.items():
        old_value=opps.at[i,field] if field in opps.columns else None
        # normalize dates/NaN for comparison
        old_cmp="" if pd.isna(old_value) else str(old_value)
        new_cmp="" if pd.isna(new_value) else str(new_value)
        if old_cmp != new_cmp:
            changes[field]=(old_value,new_value)
            opps.at[i,field]=new_value

    qty=max(int(opps.at[i,"Quantity"]),1)
    unit=max(float(opps.at[i,"Unit Price"]),0)
    opps.at[i,"Value"]=qty*unit
    opps.at[i,"Items in Quote"]=f"{opps.at[i,'Main Item']} — {qty} un."

    cs_qty=max(int(opps.at[i,"Cross Sell Qty"]),0)
    cs_unit=max(float(opps.at[i,"Cross Sell Unit Price"]),0)
    if str(opps.at[i,"Cross Sell / Up Sell"]).strip() in ["","—"] or cs_qty==0:
        opps.at[i,"Optional Value"]=0.0
    else:
        opps.at[i,"Optional Value"]=cs_qty*cs_unit
    opps.at[i,"Total Opportunity Value"]=float(opps.at[i,"Value"])+float(opps.at[i,"Optional Value"])

    stage=opps.at[i,"SF Stage"]
    if stage=="Identify":
        opps.at[i,"FUP Status"]="Not Started"
        opps.at[i,"Days Waiting"]=0
    elif stage in ["Develop","Propose"]:
        if str(opps.at[i,"FUP Status"])=="Not Started":
            opps.at[i,"FUP Status"]="On Time"
        if int(opps.at[i,"Days Waiting"])<=0:
            opps.at[i,"Days Waiting"]=1
    else:
        opps.at[i,"FUP Status"]="Closed"

    st.session_state.opps=opps
    ticket=create_change_ticket(opp_id,opps.at[i,"Owner"],changes,action_text)
    return ticket,changes


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

# ---------- V15 SCALE SCENARIO ----------
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
    cross_items=[
        "Filter Kit","Preventive Kit","Accessory Set","Backup Battery",
        "Service Contract","Patient Circuit","Flow Sensor","Upgrade Package"
    ]
    sources = ["WhatsApp","Email","Service Call"]
    rows=[]
    opp_id=1000
    today=date.today()

    for owner_i,owner in enumerate(owners):
        # 30 unique Workflow customers per seller — Identify only
        for i in range(30):
            opp_id+=1
            customer=f"{prefixes[(i+owner_i)%len(prefixes)]} {suffixes[(i*3+owner_i)%len(suffixes)]} W{owner_i+1}-{i+1:02d}"
            score=55+((i*7+owner_i*3)%44)
            main_item=products[(i+owner_i)%len(products)]
            qty=1+(i%5)
            unit=3500+((i*1450+owner_i*700)%14500)
            cs=cross_items[(i+owner_i)%len(cross_items)] if i%3==0 else "—"
            cs_qty=1 if cs!="—" else 0
            cs_unit=2900+((i*650)%7200) if cs!="—" else 0
            opened=today-timedelta(days=(i%12))
            rows.append({
                "OPP":opp_id,"Customer":customer,"Owner":owner,"Seller":owner,
                "Priority":priority(score),"Score":score,
                "Revenue":["Normal","Alta","Altíssima"][(i+1+owner_i)%3],
                "Conversion":["Normal","Alta","Altíssima"][(i+2+owner_i)%3],
                "Inventory":["Normal","Alta","Altíssima"][(i+owner_i)%3],
                "SLA":["Normal","Alta","Altíssima"][(i+1)%3],
                "Credit":["Normal","Alta","Altíssima"][(i+2)%3],
                "Main Item":main_item,"Quantity":qty,"Unit Price":unit,
                "Value":qty*unit,"Items in Quote":f"{main_item} — {qty} un.",
                "Cross Sell / Up Sell":cs,"Cross Sell Qty":cs_qty,"Cross Sell Unit Price":cs_unit,
                "Optional Value":cs_qty*cs_unit,"Total Opportunity Value":qty*unit+cs_qty*cs_unit,
                "SF Stage":"Identify","FUP Status":"Not Started","Days Waiting":0,
                "Source":sources[(i+owner_i)%3],"Needs Review":False,
                "Action":"First commercial contact",
                "Description":f"New inbound opportunity automatically created from {sources[(i+owner_i)%3]}.",
                "Demand Description":f"Inbound request received via {sources[(i+owner_i)%3]} for {main_item}.",
                "Channel Detail":sources[(i+owner_i)%3],
                "OPP Open Date":opened,"Next FUP":next_fup_date(0),"Opportunity Source":"Inbound","Growth Conversation":"—"
            })

        # 70 unique FUP customers per seller — Develop or Propose only
        for i in range(70):
            opp_id+=1
            customer=f"{prefixes[(i+owner_i+4)%len(prefixes)]} {suffixes[(i*5+owner_i+7)%len(suffixes)]} F{owner_i+1}-{i+1:02d}"
            stage="Develop" if i%2==0 else "Propose"
            waiting=1+((i*2+owner_i)%24)
            score=58+((i*5+owner_i*4)%41)
            main_item=products[(i*2+owner_i)%len(products)]
            qty=1+(i%6)
            unit=4500+((i*1720+owner_i*900)%21500)
            cs=cross_items[(i+owner_i+2)%len(cross_items)] if i%4==0 else "—"
            cs_qty=1+(i%2) if cs!="—" else 0
            cs_unit=3200+((i*790)%9000) if cs!="—" else 0
            opened=today-timedelta(days=8+(i%45))
            rows.append({
                "OPP":opp_id,"Customer":customer,"Owner":owner,"Seller":owner,
                "Priority":priority(score),"Score":score,
                "Revenue":["Normal","Alta","Altíssima"][(i+2+owner_i)%3],
                "Conversion":["Normal","Alta","Altíssima"][(i+owner_i)%3],
                "Inventory":["Normal","Alta","Altíssima"][(i+1+owner_i)%3],
                "SLA":["Normal","Alta","Altíssima"][(i+2)%3],
                "Credit":["Normal","Alta","Altíssima"][(i+1)%3],
                "Main Item":main_item,"Quantity":qty,"Unit Price":unit,
                "Value":qty*unit,"Items in Quote":f"{main_item} — {qty} un.",
                "Cross Sell / Up Sell":cs,"Cross Sell Qty":cs_qty,"Cross Sell Unit Price":cs_unit,
                "Optional Value":cs_qty*cs_unit,"Total Opportunity Value":qty*unit+cs_qty*cs_unit,
                "SF Stage":stage,
                "FUP Status":"Overdue" if waiting>10 else "On Time",
                "Days Waiting":waiting,"Source":sources[(i+owner_i+1)%3],
                "Needs Review":stage=="Propose" and i%3==1,
                "Action":"Review proposal / customer feedback" if stage=="Propose" else "Advance commercial discussion",
                "Description":"Commercial interaction already started. Follow-up is active.",
                "Demand Description":f"Commercial follow-up for {main_item}.",
                "Channel Detail":sources[(i+owner_i+1)%3],
                "OPP Open Date":opened,"Next FUP":next_fup_date(waiting),"Opportunity Source":"Inbound","Growth Conversation":"—"
            })
    return pd.DataFrame(rows)

required_v15_cols={"Main Item","Quantity","Unit Price","Cross Sell Qty","Cross Sell Unit Price","Description","OPP Open Date"}
if "opps" not in st.session_state or len(st.session_state.opps) != 400 or not required_v15_cols.issubset(set(st.session_state.opps.columns)):
    st.session_state.opps = build_scaled_opportunity_scenario()
if "activity_log" not in st.session_state:
    st.session_state.activity_log=[]
if "sf_sync_queue" not in st.session_state:
    st.session_state.sf_sync_queue=[]
if "interaction_validation" not in st.session_state:
    st.session_state.interaction_validation=[
        {"Validation ID":"IV-001","Customer":"Instituto Solaris","Growth Type":"Service Contract","Estimated Potential":42000.0,
         "Filipe Message":"Olá, Mariana. Pela base instalada de vocês, identificamos uma oportunidade de contrato de serviço para aumentar a disponibilidade dos equipamentos, reduzir paradas não planejadas e trazer maior previsibilidade à manutenção. Posso te apresentar rapidamente essa possibilidade?",
         "Customer Reply":"Sim, temos interesse. Hoje temos 12 equipamentos e estamos justamente avaliando alternativas para manutenção. Pode nos explicar melhor como funcionaria?",
         "AI Summary":"Customer demonstrated explicit interest in a service contract and informed an installed base of 12 units. Commercial qualification is recommended before creating a Salesforce opportunity.",
         "Assigned Validator":"Ana","Commercial Load Index":34,"Status":"Pending Human Validation","Received":datetime.now().strftime("%d/%m/%Y %H:%M")},
        {"Validation ID":"IV-002","Customer":"Hospital Vértice","Growth Type":"Preventive Kit","Estimated Potential":28500.0,
         "Filipe Message":"Olá, Carlos. Identificamos pela sua base instalada uma oportunidade de reforçar o estoque preventivo e reduzir risco de parada por reposição emergencial. Posso avaliar essa necessidade com você?",
         "Customer Reply":"Pode sim. Tivemos duas reposições urgentes nos últimos meses. Me envie uma sugestão do que deveríamos manter disponível.",
         "AI Summary":"Customer reported recent emergency replacements and requested a preventive-stock recommendation. Response indicates a qualified commercial signal.",
         "Assigned Validator":"Bruno","Commercial Load Index":39,"Status":"Pending Human Validation","Received":datetime.now().strftime("%d/%m/%Y %H:%M")}
    ]

opps=st.session_state.opps

# V15 FIX2 — backward compatibility for older session-state datasets
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

# V15 commercial-stage governance
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
# V15 scaled demo preserves the assigned owner counts (30 Workflow + 70 FUP per owner).
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
st.sidebar.markdown('<span style="font-size:12px;opacity:.75">INSIDE SALES SMART HUB</span><br><span style="display:inline-block;margin-top:6px;background:#ffffff22;border:1px solid #ffffff55;border-radius:12px;padding:2px 9px;font-size:11px;font-weight:850">VERSION 16.4</span>',unsafe_allow_html=True)
page=st.sidebar.radio("Navigation",["Executive Dashboard","Account 360","Activity & Salesforce Sync","Management"],label_visibility="collapsed")

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

st.markdown('<div class="hero"><h1>INSIDE SALES <span class="smart">SMART HUB</span></h1><p>One dashboard. One commercial operating rhythm. · V16.4 · 100% fictitious demo data</p></div>',unsafe_allow_html=True)

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
    revenue_risk=open_od[
    (open_od['Priority']=='Altíssima') &
    (
        (open_od['Inventory'].isin(['Alta','Altíssima'])) |
        (pd.to_numeric(open_od['Days Waiting'], errors='coerce').fillna(0) > 10)
    )
].Value.sum()
    win_rate=(len(won_od)/len(closed_od)*100) if len(closed_od) else 0
    conv=float(team.loc[team.Owner==owner,'Conversion Rate'].iloc[0]) if owner in OWNERS else 30.7

    cols=st.columns(7)
    metrics=[
        ("Open Pipeline",brl(open_od.Value.sum()),f"{len(open_od)} open OPPs"),
        ("AOP Attainment",pct((od[od["SF Stage"].isin(["Order Promised","Win Closed"])].Value.sum())/AOP*100),f"Secured vs AOP {brl(AOP)}"),
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

    scenario_owner=od
    workflow_count=len(scenario_owner[scenario_owner["SF Stage"].eq("Identify")])
    fup_count=len(scenario_owner[scenario_owner["SF Stage"].isin(["Develop","Propose"])])
    orderwon_count=len(scenario_owner[scenario_owner["SF Stage"].isin(["Order Promised","Win Closed"])])
    lost_count=len(scenario_owner[scenario_owner["SF Stage"].eq("Lost Closed")])
    qc1,qc2,qc3,qc4=st.columns(4)
    qc1.metric("Workflow",workflow_count,"Identify")
    qc2.metric("FUP",fup_count,"Develop / Propose")
    qc3.metric("Orders / Won",orderwon_count,"Order Promised / Win Closed")
    qc4.metric("Lost",lost_count,"Excluded from open pipeline")

    tabs=st.tabs(["Workflow","FUP","Growth","Interaction Validation","Orders / Won","Lost"])

    # ---------------- Workflow ----------------
    with tabs[0]:
        st.caption("Identify only. Rows are sorted automatically by Priority Score ↓, then SLA criticality, Opportunity Value and Days Waiting. Click a row to open Opportunity Editor.")
        wf=queue_sort(od[od["SF Stage"].eq("Identify")].copy())
        if len(wf):
            wf_view=wf[["OPP","OPP Open Date","Priority","Score","Customer","Owner","Main Item","Quantity","Value","SF Stage","Description"]].copy()
            wf_view["OPP Open Date"]=pd.to_datetime(wf_view["OPP Open Date"]).dt.date
            wf_view["Value"]=wf_view["Value"].map(brl)
            wf_view=wf_view.rename(columns={"Score":"Priority Score","Value":"Opportunity Value"})
            event=st.dataframe(
                wf_view,
                use_container_width=True,
                hide_index=True,
                height=390,
                on_select="rerun",
                selection_mode="single-row",
                key=f"workflow_select_{owner}"
            )
            selected_rows=event.selection.rows if event and hasattr(event,"selection") else []
            if selected_rows:
                selected_opp=int(wf.iloc[selected_rows[0]]["OPP"])
                rr=opps[opps.OPP==selected_opp].iloc[0]
                with st.container(border=True):
                    st.markdown(f"### Opportunity Editor — {rr.Customer}")
                    st.caption(f"OPP {int(rr.OPP)} • Opened {pd.to_datetime(rr['OPP Open Date']).strftime('%d/%m/%Y')} • Current stage: {rr['SF Stage']}")
                    opp_logs=[x for x in st.session_state.activity_log if int(x.get("OPP",-1))==int(rr.OPP)]
                    st.caption(f"Last Salesforce Activity: {opp_logs[0]['SF Sync Status']} • {opp_logs[0]['Date/Time']}" if opp_logs else "Last Salesforce Activity: No pending changes")
                    e1,e2,e3=st.columns(3)
                    with e1:
                        main_item=st.text_input("Main Item",str(rr["Main Item"]),key=f"wf_item_{selected_opp}")
                        qty=st.number_input("Quantity",min_value=1,value=int(rr["Quantity"]),step=1,key=f"wf_qty_{selected_opp}")
                        unit=st.number_input("Unit Price (R$)",min_value=0.0,value=float(rr["Unit Price"]),step=100.0,key=f"wf_unit_{selected_opp}")
                    with e2:
                        sf_stage=st.selectbox("Salesforce Stage",["Identify","Develop","Propose"],index=["Identify","Develop","Propose"].index(rr["SF Stage"]),key=f"wf_stage_{selected_opp}")
                        action=st.text_input("Action",str(rr["Action"]),key=f"wf_action_{selected_opp}")
                        next_fup=st.date_input("Next FUP",value=pd.to_datetime(rr["Next FUP"]).date(),key=f"wf_nf_{selected_opp}")
                    with e3:
                        description=st.text_area("Description / Commercial Notes",str(rr["Description"]),height=132,key=f"wf_desc_{selected_opp}")

                    st.markdown("#### AI Cross Sell / Up Sell Recommendation")
                    rec=cross_sell_recommendation(rr)
                    rc1,rc2,rc3=st.columns(3)
                    rc1.metric("Recommendation",rec["item"])
                    rc2.metric("Type",rec["type"])
                    rc3.metric("Opportunity Fit",rec["fit"])
                    st.info(f"**Why this recommendation:** {rec['reason']}")
                    accept_rec=st.checkbox("Add recommendation to proposal",value=False,key=f"wf_accept_rec_{selected_opp}")
                    c1,c2,c3=st.columns(3)
                    with c1:
                        cs_item=st.text_input("Optional Item",rec["item"],key=f"wf_cs_{selected_opp}")
                    with c2:
                        cs_qty=st.number_input("Suggested Qty",min_value=0,value=int(rec["qty"]),step=1,key=f"wf_csq_{selected_opp}")
                    with c3:
                        cs_unit=st.number_input("Suggested Unit Price (R$)",min_value=0.0,value=float(rec["unit"]),step=100.0,key=f"wf_csu_{selected_opp}")
                    st.caption("Quantity and price are prefilled by the recommendation engine. The seller can edit them before adding the item to the proposal.")

                    projected=qty*unit+(cs_qty*cs_unit if accept_rec else 0)
                    st.info(f"Projected opportunity value: {brl(projected)}")

                    b1,b2=st.columns([1,1])
                    with b1:
                        if st.button("Save Opportunity + Create Salesforce Call",type="primary",key=f"wf_save_{selected_opp}"):
                            ticket,changes=update_opportunity(
                                selected_opp,
                                {
                                    "Main Item":main_item,"Quantity":qty,"Unit Price":unit,
                                    "SF Stage":sf_stage,"Action":action,"Next FUP":next_fup,
                                    "Description":description,"Cross Sell / Up Sell":(cs_item if accept_rec else "—"),
                                    "Cross Sell Qty":(cs_qty if accept_rec else 0),"Cross Sell Unit Price":(cs_unit if accept_rec else 0.0)
                                },
                                action
                            )
                            st.success(f"Saved. Salesforce call/ticket {ticket} created. Stage routing applied automatically.")
                            st.rerun()
                    with b2:
                        pr=opps[opps.OPP==selected_opp].iloc[0].copy()
                        pr["Main Item"]=main_item; pr["Quantity"]=qty; pr["Unit Price"]=unit
                        pr["Items in Quote"]=f"{main_item} — {qty} un."
                        pr["Value"]=qty*unit
                        pr["Cross Sell / Up Sell"]=cs_item if accept_rec else "—"; pr["Optional Value"]=(cs_qty*cs_unit if accept_rec else 0)
                        st.download_button(
                            "Generate Proposal PDF",
                            proposal_pdf(pr,include_optional=(accept_rec and cs_qty>0),revision=False),
                            file_name=f"proposal_demo_{selected_opp}.pdf",
                            mime="application/pdf",
                            key=f"wf_pdf_{selected_opp}"
                        )
                    st.caption("Changing SF Stage to Develop or Propose removes the opportunity from Workflow and routes it automatically to FUP after Save.")
        else:
            st.info("No Identify opportunities for this filter.")

    # ---------------- FUP ----------------
    with tabs[1]:
        st.caption("Develop / Propose only. Sorted automatically by Priority Score ↓. Click a row to edit pricing, items, quantity, Salesforce stage, description, Action, Next FUP and proposal.")
        f=queue_sort(od[od["SF Stage"].isin(["Develop","Propose"])].copy())
        if len(f):
            f_view=f[["OPP","OPP Open Date","Priority","Score","Customer","Owner","SF Stage","Value","Days Waiting","Action","Next FUP","Description"]].copy()
            f_view["OPP Open Date"]=pd.to_datetime(f_view["OPP Open Date"]).dt.date
            f_view["Next FUP"]=pd.to_datetime(f_view["Next FUP"]).dt.date
            f_view["Value"]=f_view["Value"].map(brl)
            f_view=f_view.rename(columns={"Score":"Priority Score","Value":"Opportunity Value"})
            event=st.dataframe(
                f_view,
                use_container_width=True,
                hide_index=True,
                height=420,
                on_select="rerun",
                selection_mode="single-row",
                key=f"fup_select_{owner}"
            )
            selected_rows=event.selection.rows if event and hasattr(event,"selection") else []
            if selected_rows:
                selected_opp=int(f.iloc[selected_rows[0]]["OPP"])
                rr=opps[opps.OPP==selected_opp].iloc[0]
                with st.container(border=True):
                    st.markdown(f"### Opportunity Editor — {rr.Customer}")
                    st.caption(f"OPP {int(rr.OPP)} • Opened {pd.to_datetime(rr['OPP Open Date']).strftime('%d/%m/%Y')} • Current stage: {rr['SF Stage']}")
                    opp_logs=[x for x in st.session_state.activity_log if int(x.get("OPP",-1))==int(rr.OPP)]
                    st.caption(f"Last Salesforce Activity: {opp_logs[0]['SF Sync Status']} • {opp_logs[0]['Date/Time']}" if opp_logs else "Last Salesforce Activity: No pending changes")
                    e1,e2,e3=st.columns(3)
                    with e1:
                        main_item=st.text_input("Main Item",str(rr["Main Item"]),key=f"fu_item_{selected_opp}")
                        qty=st.number_input("Quantity",min_value=1,value=int(rr["Quantity"]),step=1,key=f"fu_qty_{selected_opp}")
                        unit=st.number_input("Unit Price (R$)",min_value=0.0,value=float(rr["Unit Price"]),step=100.0,key=f"fu_unit_{selected_opp}")
                    with e2:
                        stage_options=["Develop","Propose","Order Promised","Win Closed","Lost Closed"]
                        sf_stage=st.selectbox("Salesforce Stage",stage_options,index=stage_options.index(rr["SF Stage"]),key=f"fu_stage_{selected_opp}")
                        action=st.text_input("Action",str(rr["Action"]),key=f"fu_action_{selected_opp}")
                        next_fup=st.date_input("Next FUP",value=pd.to_datetime(rr["Next FUP"]).date(),key=f"fu_nf_{selected_opp}")
                    with e3:
                        description=st.text_area("Description / Commercial Notes",str(rr["Description"]),height=132,key=f"fu_desc_{selected_opp}")

                    st.markdown("#### AI Cross Sell / Up Sell Recommendation")
                    rec=cross_sell_recommendation(rr)
                    rc1,rc2,rc3=st.columns(3)
                    rc1.metric("Recommendation",rec["item"])
                    rc2.metric("Type",rec["type"])
                    rc3.metric("Opportunity Fit",rec["fit"])
                    st.info(f"**Why this recommendation:** {rec['reason']}")
                    accept_rec=st.checkbox("Add recommendation to proposal",value=False,key=f"fu_accept_rec_{selected_opp}")
                    c1,c2,c3=st.columns(3)
                    with c1:
                        cs_item=st.text_input("Optional Item",rec["item"],key=f"fu_cs_{selected_opp}")
                    with c2:
                        cs_qty=st.number_input("Suggested Qty",min_value=0,value=int(rec["qty"]),step=1,key=f"fu_csq_{selected_opp}")
                    with c3:
                        cs_unit=st.number_input("Suggested Unit Price (R$)",min_value=0.0,value=float(rec["unit"]),step=100.0,key=f"fu_csu_{selected_opp}")
                    st.caption("Quantity and price are prefilled by the recommendation engine. The seller can edit them before adding the item to the proposal.")

                    projected=qty*unit+(cs_qty*cs_unit if accept_rec else 0)
                    st.info(f"Projected opportunity value: {brl(projected)}")

                    b1,b2=st.columns([1,1])
                    with b1:
                        if st.button("Save Opportunity + Create Salesforce Call",type="primary",key=f"fu_save_{selected_opp}"):
                            ticket,changes=update_opportunity(
                                selected_opp,
                                {
                                    "Main Item":main_item,"Quantity":qty,"Unit Price":unit,
                                    "SF Stage":sf_stage,"Action":action,"Next FUP":next_fup,
                                    "Description":description,"Cross Sell / Up Sell":(cs_item if accept_rec else "—"),
                                    "Cross Sell Qty":(cs_qty if accept_rec else 0),"Cross Sell Unit Price":(cs_unit if accept_rec else 0.0)
                                },
                                action
                            )
                            st.success(f"Saved. Salesforce call/ticket {ticket} created. Opportunity routed to {stage_bucket(sf_stage)}.")
                            st.rerun()
                    with b2:
                        pr=opps[opps.OPP==selected_opp].iloc[0].copy()
                        pr["Main Item"]=main_item; pr["Quantity"]=qty; pr["Unit Price"]=unit
                        pr["Items in Quote"]=f"{main_item} — {qty} un."
                        pr["Value"]=qty*unit
                        pr["Cross Sell / Up Sell"]=cs_item if accept_rec else "—"; pr["Optional Value"]=(cs_qty*cs_unit if accept_rec else 0)
                        st.download_button(
                            "Generate Revised Proposal" if rr["SF Stage"]=="Propose" else "Generate Proposal PDF",
                            proposal_pdf(pr,include_optional=(accept_rec and cs_qty>0),revision=(rr["SF Stage"]=="Propose")),
                            file_name=f"{'revised_' if rr['SF Stage']=='Propose' else ''}proposal_demo_{selected_opp}.pdf",
                            mime="application/pdf",
                            key=f"fu_pdf_{selected_opp}"
                        )
                    st.caption("Order Promised / Win Closed move to Orders / Won. Lost Closed moves to Lost and is automatically excluded from Open Pipeline and active opportunity values.")
        else:
            st.info("No Develop / Propose opportunities for this filter.")

    # ---------------- Growth ----------------
    with tabs[2]:
        st.caption("Growth remains owned by Filipe. A signal becomes an opportunity only after customer interaction.")
        if owner not in ["All","Filipe"]:
            st.info("Growth is owned by Filipe. Select All or Filipe to view Growth.")
        else:
            g=growth.copy()
            gv=g[["Growth ID","Customer","Responsible","Type","Suggested Item","Qty","Growth Potential","Growth Stage","Due"]].copy()
            gv["Growth Potential"]=gv["Growth Potential"].map(brl)
            st.dataframe(gv,use_container_width=True,hide_index=True,height=390)
            gx=st.selectbox("Generate Outreach Text",g.index.tolist(),format_func=lambda i:f"{g.loc[i,'Customer']} — {g.loc[i,'Suggested Item']}",key="gtxt_v15")
            if st.button("Generate Text",key="gbutton_v15"):
                st.text_area("Suggested WhatsApp / Email",growth_message(g.loc[gx]),height=110)

    # ---------------- Interaction Validation ----------------
    with tabs[3]:
        st.caption("Filipe Growth replies are reviewed by a human seller before any Salesforce opportunity is created.")
        validations=pd.DataFrame(st.session_state.interaction_validation)
        pending=validations[validations["Status"]=="Pending Human Validation"].copy() if len(validations) else pd.DataFrame()
        if owner!="All" and len(pending): pending=pending[pending["Assigned Validator"]==owner]
        if len(pending):
            vv=pending[["Validation ID","Customer","Growth Type","Estimated Potential","Assigned Validator","Commercial Load Index","Status","Received"]].copy()
            vv["Estimated Potential"]=vv["Estimated Potential"].map(brl)
            st.dataframe(vv,use_container_width=True,hide_index=True,height=220)
            selected_id=st.selectbox("Interaction to validate",pending["Validation ID"].tolist(),
                format_func=lambda x:f"{x} — {pending.loc[pending['Validation ID']==x,'Customer'].iloc[0]}",key=f"iv_{owner}")
            rec=next(x for x in st.session_state.interaction_validation if x["Validation ID"]==selected_id)
            with st.container(border=True):
                st.markdown(f"### Interaction Validation — {rec['Customer']}")
                c1,c2,c3=st.columns(3)
                c1.metric("Estimated Potential",brl(rec["Estimated Potential"]))
                c2.metric("Assigned Validator",rec["Assigned Validator"])
                c3.metric("Commercial Load Index",rec["Commercial Load Index"])
                st.caption("Validation routing uses seller capacity / Commercial Load Index, not Priority Score.")
                st.markdown("#### Conversation — Filipe ↔ Customer")
                st.markdown(f"**Filipe:** {rec['Filipe Message']}")
                st.markdown(f"**Customer:** {rec['Customer Reply']}")
                st.info(f"**AI Summary:** {rec['AI Summary']}")
                q1,q2=st.columns(2)
                with q1:
                    note=st.text_area("Human Qualification / Validation Note","Customer response indicates a valid commercial opportunity.",key=f"iv_note_{selected_id}")
                    close_reason=st.selectbox(
                        "Close Reason (only if no opportunity is created)",
                        ["No current interest","No budget","No fit / need","Wrong contact","Timing / revisit later","Other"],
                        key=f"iv_close_reason_{selected_id}"
                    )
                with q2:
                    sellers=["Ana","Bruno","Carla"]
                    validator=rec["Assigned Validator"] if rec["Assigned Validator"] in sellers else "Ana"
                    proposed_owner=st.selectbox("Opportunity Owner",sellers,index=sellers.index(validator),key=f"iv_owner_{selected_id}")
                    estimated_value=st.number_input("Validated Estimated Value (R$)",min_value=0.0,value=float(rec["Estimated Potential"]),step=500.0,key=f"iv_value_{selected_id}")
                b1,b2=st.columns(2)
                with b1:
                    if st.button("Create Opportunity",type="primary",key=f"iv_create_{selected_id}"):
                        current=st.session_state.opps
                        new_id=int(current["OPP"].max())+1; score=78
                        new_row={"OPP":new_id,"Customer":rec["Customer"],"Owner":proposed_owner,"Seller":proposed_owner,
                            "Priority":priority(score),"Score":score,"Revenue":"Alta","Conversion":"Alta","Inventory":"Normal","SLA":"Alta","Credit":"Normal",
                            "Main Item":rec["Growth Type"],"Quantity":1,"Unit Price":float(estimated_value),"Value":float(estimated_value),
                            "Items in Quote":f"{rec['Growth Type']} — 1 un.","Cross Sell / Up Sell":"—","Cross Sell Qty":0,"Cross Sell Unit Price":0.0,
                            "Optional Value":0.0,"Total Opportunity Value":float(estimated_value),"SF Stage":"Identify","FUP Status":"Not Started","Days Waiting":0,
                            "Source":"Filipe Growth","Needs Review":False,"Action":"Human-qualified Growth opportunity — first commercial follow-up",
                            "Description":note,"Demand Description":rec["AI Summary"],"Channel Detail":"Filipe Growth Interaction",
                            "OPP Open Date":date.today(),"Next FUP":next_fup_date(0),"Opportunity Source":"Growth / Filipe",
                            "Growth Conversation":f"Filipe: {rec['Filipe Message']} | Customer: {rec['Customer Reply']}"}
                        st.session_state.opps=pd.concat([current,pd.DataFrame([new_row])],ignore_index=True)
                        for item in st.session_state.interaction_validation:
                            if item["Validation ID"]==selected_id:
                                item["Status"]="Converted to Opportunity"; item["Created OPP"]=new_id
                        create_change_ticket(new_id,proposed_owner,{"SF Stage":("No OPP","Identify")},"Human validated Filipe interaction and created Salesforce opportunity")
                        st.success(f"OPP {new_id} created in Identify and routed to {proposed_owner}'s Workflow with the full conversation attached.")
                        st.rerun()
                with b2:
                    if st.button("Close as Not Qualified",key=f"iv_dismiss_{selected_id}"):
                        for item in st.session_state.interaction_validation:
                            if item["Validation ID"]==selected_id:
                                item["Status"]="Closed — Not Qualified"; item["Validation Note"]=note
                                item["Close Reason"]=close_reason
                        st.success("Interaction closed as Not Qualified. No Salesforce opportunity was created; the conversation remains stored in Growth history.")
                        st.rerun()
        else:
            st.info("No customer interactions are awaiting human validation for this filter.")

    # ---------------- Orders / Won ----------------
    with tabs[4]:
        st.caption("Order Promised and Win Closed leave active FUP and are reported here.")
        ow=queue_sort(od[od["SF Stage"].isin(["Order Promised","Win Closed"])].copy())
        if len(ow):
            owv=ow[["OPP","OPP Open Date","Customer","Owner","SF Stage","Value","Total Opportunity Value","Description"]].copy()
            owv["OPP Open Date"]=pd.to_datetime(owv["OPP Open Date"]).dt.date
            owv["Value"]=owv["Value"].map(brl); owv["Total Opportunity Value"]=owv["Total Opportunity Value"].map(brl)
            st.dataframe(owv,use_container_width=True,hide_index=True,height=350)
            o1,o2=st.columns(2)
            o1.metric("Orders / Won OPPs",len(ow))
            o2.metric("Orders / Won Value",brl(ow["Value"].sum()))
        else:
            st.info("No Order Promised / Win Closed opportunities for this filter.")

    # ---------------- Lost ----------------
    with tabs[5]:
        st.caption("Lost Closed opportunities leave active FUP. Their values are excluded from Open Pipeline, Revenue at Risk and active opportunity totals.")
        lo=od[od["SF Stage"].eq("Lost Closed")].copy()
        if len(lo):
            lov=lo[["OPP","OPP Open Date","Customer","Owner","Value","Description","Action"]].copy()
            lov["OPP Open Date"]=pd.to_datetime(lov["OPP Open Date"]).dt.date
            lov["Value"]=lov["Value"].map(brl)
            st.dataframe(lov,use_container_width=True,hide_index=True,height=350)
            l1,l2=st.columns(2)
            l1.metric("Lost OPPs",len(lo))
            l2.metric("Lost Value",brl(lo["Value"].sum()))
        else:
            st.info("No Lost Closed opportunities for this filter.")


    st.markdown('<div class="section-title">Automatic Inbound Intake</div>',unsafe_allow_html=True)
    st.caption("Inbound e-mail, WhatsApp and service-call demands are processed automatically in the background. No seller re-entry or manual AI Intake is required.")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Inbound Capture","Automatic"); c2.metric("Salesforce Stage","Identify")
    c3.metric("Destination","Workflow"); c4.metric("Human Touch","Exceptions only")
    st.info("Message received → customer/account match → SAP inventory & credit lookup → Priority Score → Salesforce OPP in Identify → responsible seller's Workflow.")
    with st.expander("View background agent orchestration",expanded=False):
        bg=pd.DataFrame([["CRM Agent","Account match + demand structuring + Salesforce record","Background / API-ready"],
                         ["Operations Agent","SAP inventory + credit lookup","Background / API-ready"],
                         ["Priority Agent","Priority Score + SLA + routing","Background"],
                         ["Human Seller","Commercial judgment when required","Exception / Workflow"]],
                        columns=["Layer","Responsibility","Operating Mode"])
        st.dataframe(bg,use_container_width=True,hide_index=True)
        st.caption("Demo architecture: Salesforce/SAP are represented as integration-ready layers; no live Philips write is claimed.")

    st.markdown("### Filipe — Interaction Validation")
    st.caption("Only customer replies generated by Filipe's proactive Growth outreach appear here. The table follows the selected Owner filter and is ordered by Commercial Load Index.")

    pending_iv = pd.DataFrame(st.session_state.interaction_validation)
    if len(pending_iv):
        pending_iv = pending_iv[pending_iv["Status"].eq("Pending Human Validation")].copy()

    if owner != "All" and len(pending_iv):
        pending_iv = pending_iv[pending_iv["Assigned Validator"].eq(owner)].copy()

    if len(pending_iv):
        pending_iv = pending_iv.sort_values(["Commercial Load Index","Received"],ascending=[True,True]).reset_index(drop=True)
        iv_view = pending_iv[[
            "Validation ID","Customer","Growth Type","Estimated Potential",
            "Assigned Validator","Commercial Load Index","Received","Status"
        ]].copy()
        iv_view["Estimated Potential"] = iv_view["Estimated Potential"].map(brl)

        iv_event = st.dataframe(
            iv_view,
            use_container_width=True,
            hide_index=True,
            height=220,
            on_select="rerun",
            selection_mode="single-row",
            key=f"dashboard_iv_table_{owner}"
        )

        selected_rows = iv_event.selection.rows if iv_event and hasattr(iv_event,"selection") else []
        if selected_rows:
            selected_id = pending_iv.iloc[selected_rows[0]]["Validation ID"]
            rec = next(x for x in st.session_state.interaction_validation if x["Validation ID"] == selected_id)

            with st.container(border=True):
                st.markdown(f"### Interaction Editor — {rec['Customer']}")
                h1,h2,h3=st.columns(3)
                h1.metric("Estimated Potential",brl(rec["Estimated Potential"]))
                h2.metric("Assigned Validator",rec["Assigned Validator"])
                h3.metric("Commercial Load Index",rec["Commercial Load Index"])

                st.markdown("#### Conversation — Filipe ↔ Customer")
                st.markdown(f"**Filipe:** {rec['Filipe Message']}")
                st.markdown(f"**Customer:** {rec['Customer Reply']}")
                st.info(f"**AI Summary:** {rec['AI Summary']}")

                c1,c2=st.columns(2)
                with c1:
                    validation_note=st.text_area(
                        "Human Qualification / Validation Note",
                        "Customer response indicates a valid commercial opportunity.",
                        key=f"dash_iv_note_{selected_id}"
                    )
                    close_reason=st.selectbox(
                        "Close Reason (only if no opportunity is created)",
                        ["No current interest","No budget","No fit / need","Wrong contact","Timing / revisit later","Other"],
                        key=f"dash_iv_close_reason_{selected_id}"
                    )
                with c2:
                    seller_opts=["Ana","Bruno","Carla"]
                    assigned=rec["Assigned Validator"] if rec["Assigned Validator"] in seller_opts else "Ana"
                    proposed_owner=st.selectbox(
                        "Opportunity Owner",
                        seller_opts,
                        index=seller_opts.index(assigned),
                        key=f"dash_iv_owner_{selected_id}"
                    )
                    estimated_value=st.number_input(
                        "Validated Estimated Value (R$)",
                        min_value=0.0,
                        value=float(rec["Estimated Potential"]),
                        step=500.0,
                        key=f"dash_iv_value_{selected_id}"
                    )

                a1,a2=st.columns(2)
                with a1:
                    if st.button("Create Opportunity",type="primary",key=f"dash_iv_create_{selected_id}"):
                        current=st.session_state.opps
                        new_id=int(current["OPP"].max())+1
                        score=78
                        new_row={
                            "OPP":new_id,"Customer":rec["Customer"],"Owner":proposed_owner,"Seller":proposed_owner,
                            "Priority":priority(score),"Score":score,
                            "Revenue":"Alta","Conversion":"Alta","Inventory":"Normal","SLA":"Alta","Credit":"Normal",
                            "Main Item":rec["Growth Type"],"Quantity":1,"Unit Price":float(estimated_value),
                            "Value":float(estimated_value),"Items in Quote":f"{rec['Growth Type']} — 1 un.",
                            "Cross Sell / Up Sell":"—","Cross Sell Qty":0,"Cross Sell Unit Price":0.0,
                            "Optional Value":0.0,"Total Opportunity Value":float(estimated_value),
                            "SF Stage":"Identify","FUP Status":"Not Started","Days Waiting":0,
                            "Source":"Filipe Growth","Needs Review":False,
                            "Action":"Human-qualified Growth opportunity — first commercial follow-up",
                            "Description":validation_note,"Demand Description":rec["AI Summary"],
                            "Channel Detail":"Filipe Growth Interaction",
                            "OPP Open Date":date.today(),"Next FUP":next_fup_date(0),
                            "Opportunity Source":"Growth / Filipe",
                            "Growth Conversation":f"Filipe: {rec['Filipe Message']} | Customer: {rec['Customer Reply']}"
                        }
                        st.session_state.opps=pd.concat([current,pd.DataFrame([new_row])],ignore_index=True)
                        for item in st.session_state.interaction_validation:
                            if item["Validation ID"]==selected_id:
                                item["Status"]="Converted to Opportunity"
                                item["Created OPP"]=new_id
                        create_change_ticket(
                            new_id,proposed_owner,
                            {"SF Stage":("No OPP","Identify")},
                            "Human validated Filipe interaction and created Salesforce opportunity"
                        )
                        st.success(f"OPP {new_id} created in Identify and routed to {proposed_owner}'s Workflow.")
                        st.rerun()
                with a2:
                    if st.button("Close as Not Qualified",key=f"dash_iv_dismiss_{selected_id}"):
                        for item in st.session_state.interaction_validation:
                            if item["Validation ID"]==selected_id:
                                item["Status"]="Closed — Not Qualified"
                                item["Validation Note"]=validation_note
                                item["Close Reason"]=close_reason
                        st.success("Interaction closed as Not Qualified. No Salesforce opportunity was created; the conversation remains stored in Growth history.")
                        st.rerun()
    else:
        st.caption("No interactions pending validation for this seller.")

    st.markdown('<div class="section-title">Priority Explainability</div>',unsafe_allow_html=True)
    q=open_od.sort_values('Score',ascending=False).head(8).copy()
    for c,m in [('Revenue',30),('Conversion',25),('Inventory',20),('SLA',15),('Credit',10)]:
        label_to_points = {'Normal': round(m*0.55), 'Alta': round(m*0.80), 'Altíssima': m}
        q[c] = q[c].apply(
            lambda x: (
                f"{'🟢' if str(x)=='Normal' else '🟡' if str(x)=='Alta' else '🔴'} {str(x)}"
                if str(x) in ['Normal','Alta','Altíssima']
                else f"{int(float(x))}/{m}" if str(x).replace('.','',1).isdigit()
                else str(x)
            )
        )
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

# ---------------------------- Activity & Salesforce Sync ----------------------------
elif page=="Activity & Salesforce Sync":
    st.markdown('<div class="section-title">Activity & Salesforce Sync</div>',unsafe_allow_html=True)
    st.caption("Central audit trail for commercial changes, Salesforce calls and API-ready synchronization.")
    log_df=pd.DataFrame(st.session_state.activity_log); sync_df=pd.DataFrame(st.session_state.sf_sync_queue)
    a1,a2,a3=st.columns(3)
    a1.metric("Activities / Calls",len(log_df)); a2.metric("API-ready Queue",len(sync_df)); a3.metric("Sync Errors",0)
    st.markdown("### Salesforce Activity / Call Log")
    if len(log_df): st.dataframe(log_df,use_container_width=True,hide_index=True,height=360)
    else: st.info("No activity recorded yet. Opportunity changes and validated Growth conversions create traceable Salesforce tickets.")
    st.markdown("### Salesforce Sync Queue")
    if len(sync_df): st.dataframe(sync_df,use_container_width=True,hide_index=True,height=300)
    else: st.caption("No queued updates.")

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
Filipe executes **30–50 proactive actions/day** across the installed-base portfolio. A Growth Signal is *not* a Salesforce OPP. When the customer replies, the interaction is routed by **Commercial Load Index** to a human seller for validation. Only after human approval is an OPP created in **Identify**.

**Governance**  
Pricing exceptions, credit issues, inventory constraints, out-of-policy negotiations and final commercial commitments remain under human approval. Filipe automates governed volume and preserves seller time for higher-value judgment.""")
    with tab2:
        st.markdown("""### Inside Sales Smart Hub — From Reactive Requests to Intelligent Revenue Growth
**1. Smart Workflow | Productivity** — organize inbound demand and commercial creation.  
**2. Smart Priority | Conversion** — explainable score and focus.  
**3. Smart Growth | Incremental Revenue** — Filipe creates demand before the next call.

**Executive principle:** *Automate governed volume. Preserve human sellers for commercial judgment and higher-impact decisions.*

**Operational rhythm:** one Executive Dashboard, one owner filter and six transactional reports: **Workflow | FUP | Growth | Interaction Validation | Orders / Won | Lost**.

**V14 transformation layer:** five coordinated agents — Filipe, CRM Agent, Priority Agent, Operations Agent and Proposal Agent — with Salesforce and SAP API-ready integration and human governance at financial-risk decisions.""")

# ---------------------------- Filipe everywhere ----------------------------
st.markdown('---')
st.markdown('<div class="section-title">💬 Filipe — AI Sales Assistant & Agent</div>',unsafe_allow_html=True)
fc1,fc2=st.columns([1,3]); fctx=fc1.selectbox('Owner context',["All"]+OWNERS,key='fctx'); q=fc2.text_input('Ask Filipe',placeholder='Ex.: O que eu preciso fazer hoje? | Quais são as demandas da Ana? | Quantos Growth actions você tem hoje?')
if st.button('Ask Filipe',key='ask') and q:
    st.markdown(f'<div class="chat-answer"><b>Filipe</b><br>{filipe_answer(q,fctx)}</div>',unsafe_allow_html=True)
