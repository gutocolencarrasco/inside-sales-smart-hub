import streamlit as st
import pandas as pd
from datetime import datetime
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Inside Sales Smart Hub V9",page_icon="⚡",layout="wide")
st.markdown("""<style>
.block-container{padding-top:1rem;max-width:1550px}.hero{background:linear-gradient(120deg,#071b33,#0d74c7);padding:24px 28px;border-radius:20px;color:white;margin-bottom:16px}
.hero h1{margin:0}.pill{display:inline-block;background:#ffffff22;padding:5px 9px;border-radius:20px;margin:8px 4px 0 0}
[data-testid="stMetric"]{border:1px solid #8aa0b833;padding:10px;border-radius:13px}.box{border-left:5px solid #0d74c7;background:#0d74c711;padding:14px;border-radius:9px}
.agent{border-left:5px solid #6f42c1;background:#6f42c111;padding:14px;border-radius:9px}
</style>""",unsafe_allow_html=True)

META=4_000_000
STAGES=["Identify","Develop","Propose","Order Promised","Lost Closed"]
def brl(v): return f"R$ {v:,.0f}".replace(",","X").replace(".",",").replace("X",".")
def pm(v): return f"{v/META*100:.1f}%".replace(".",",")

# Dados demonstrativos 100% fictícios/anônimos
BASE=[
[91001,"Hospital Horizonte","Ana",186000,"Develop",92,28,24,20,12,8,"Altíssima","Kit Preventivo Alpha — 10 un.","Sensor de Fluxo Pro — 2 un.","Vendedor","FUP hoje"],
[91002,"Rede Vida Nova","Bruno",74000,"Propose",78,22,20,18,10,8,"Alta","Sensor de Fluxo Pro — 3 un.","Contrato Preventivo 12M — 1 un.","Vendedor","FUP D+2"],
[91003,"Instituto Aurora","Carla",29500,"Propose",84,25,22,18,11,8,"Altíssima","Filtro Performance — 10 un.","Kit Preventivo Alpha — 1 un.","Vendedor","FUP vencido"],
[91004,"Hospital Monte Azul","Ana",128000,"Identify",66,24,14,10,10,8,"Alta","Módulo Eletrônico X — 3 un.","Contrato Preventivo 12M — 1 un.","Vendedor","Validar crédito"],
[91005,"Clínica Integra","Bruno",68000,"Develop",76,21,21,16,10,8,"Alta","Bateria Backup Plus — 5 un.","Upgrade Performance — 1 un.","Vendedor","Contato realizado"],
[91006,"Grupo Santa Luz","Carla",215000,"Propose",82,30,19,17,9,7,"Altíssima","Contrato Preventivo 12M — 1 un.","Upgrade Performance — 1 un.","Vendedor","Negociação"],
[91007,"Hospital Nova Esperança","Ana",99000,"Propose",88,26,23,20,12,7,"Altíssima","Kit Preventivo Alpha — 6 un.","Sensor de Fluxo Pro — 2 un.","Vendedor","FUP vencido"],
[91008,"Centro Médico Solaris","Bruno",47000,"Identify",54,17,12,5,11,9,"Normal","Válvula Inspiratória — 3 un.","Kit Preventivo Alpha — 1 un.","Vendedor","Aguardar estoque"],
[91009,"Rede Plena Saúde","Carla",83000,"Develop",79,23,22,18,9,7,"Alta","Sensor de Fluxo Pro — 4 un.","Contrato Preventivo 12M — 1 un.","Vendedor","Contato realizado"],
[91010,"Hospital Parque Central","Ana",152000,"Propose",73,27,17,13,9,7,"Alta","Upgrade Performance — 2 un.","Contrato Preventivo 12M — 1 un.","Vendedor","FUP D+5"],
[91011,"Clínica Vale Verde","Bruno",7800,"Identify",48,8,13,15,7,5,"Normal","Filtro Performance — 3 un.","Kit Preventivo Alpha — 1 un.","Agente Autônomo","Primeiro contato automático"],
[91012,"Centro Diagnóstico Orion","Carla",9400,"Develop",57,10,16,15,9,7,"Normal","Bateria Backup Plus — 1 un.","Filtro Performance — 2 un.","Agente Autônomo","WhatsApp respondido"],
[91013,"Hospital Bela Vista","Ana",4600,"Propose",52,7,15,17,8,5,"Normal","Filtro Performance — 2 un.","Kit Preventivo Alpha — 1 un.","Agente Autônomo","FUP D+2"],
[91014,"Rede Saúde Prime","Bruno",56000,"Order Promised",86,25,22,20,11,8,"Altíssima","Kit Preventivo Alpha — 3 un.","—","Vendedor","OC validada"],
[91015,"Instituto Lumina","Carla",33000,"Lost Closed",61,16,18,12,8,7,"Alta","Sensor de Fluxo Pro — 2 un.","—","Vendedor","Perdida — preço"]]
COL=["OPP","Cliente","Vendedor","Valor","Status SF","Score","Receita","Conversão","Estoque","SLA","Crédito","Prioridade","Itens em Cotação","Cross Sell / Upsell","Responsável","Próxima Ação"]
if "opps" not in st.session_state: st.session_state.opps=pd.DataFrame(BASE,columns=COL)
opps=st.session_state.opps

growth=pd.DataFrame([
["Hospital Horizonte","Peça","Kit Preventivo Alpha",3,49200,"Manter 3 un. em estoque para reduzir indisponibilidade e evitar perdas com equipamento parado."],
["Rede Vida Nova","Serviço","Contrato Preventivo 12M",1,44600,"Aumentar disponibilidade da base e previsibilidade da manutenção, reduzindo paradas não planejadas."],
["Instituto Aurora","Peça","Sensor de Fluxo Pro",2,40460,"Criar estoque preventivo de 2 un. para reduzir tempo de resposta e risco de equipamento parado."],
["Clínica Integra","Peça","Bateria Backup Plus",2,24992,"Antecipar reposição e reduzir impacto operacional de indisponibilidade."],
["Grupo Santa Luz","Serviço","Contrato Preventivo 12M",1,44600,"Transformar manutenção reativa em cobertura planejada e aumentar previsibilidade operacional."],
["Hospital Nova Esperança","Peça","Kit Preventivo Alpha",2,32800,"Manter estoque local para reduzir espera por nova compra e proteger disponibilidade."],
],columns=["Cliente","Tipo","Item sugerido","Qtd. sugerida","Valor potencial","Ação sugerida"])

team=pd.DataFrame([["Ana",87,565600,5,31.5,94,82,126000,78],["Bruno",79,253800,5,27.8,88,76,82000,61],["Carla",84,370900,5,29.4,91,85,104000,69]],
columns=["Vendedor","Performance","Pipeline","OPPs Ativas","Conversão %","SLA %","Adoção Growth %","Receita Incremental","Índice de Carga Comercial"])

def summary():
    return pd.DataFrame([[s,len(opps[opps["Status SF"]==s]),opps.loc[opps["Status SF"]==s,"Valor"].sum()] for s in STAGES],columns=["Status Salesforce","Qtd. OPPs","Valor"])

def message(r):
    if r["Tipo"]=="Peça":
        return f"Olá, [Nome]. Temos o {r['Item sugerido']} disponível e identificamos que pode fazer sentido manter {int(r['Qtd. sugerida'])} un. em estoque, reduzindo o risco de parada e possíveis perdas enquanto uma nova peça é adquirida e entregue. Posso avaliar essa necessidade com você?"
    return "Olá, [Nome]. Pela sua base instalada, identificamos uma oportunidade de contrato de serviço para aumentar a disponibilidade dos equipamentos, reduzir paradas não planejadas e trazer maior previsibilidade à manutenção. Posso te apresentar rapidamente essa possibilidade?"

nav=["1. Central de Decisão","2. Performance Comercial do Time","3. Smart Workflow","4. Fila Inteligente","5. Growth Engine","6. FUP","7. Account 360","8. Arquitetura","9. Modo Apresentação"]
page=st.sidebar.radio("Modo Navegação",nav)
st.sidebar.markdown("### Pipeline Salesforce")
for _,r in summary().iterrows():
    st.sidebar.markdown(f"**{r['Status Salesforce']}**  \n{int(r['Qtd. OPPs'])} OPPs • {brl(r['Valor'])} • {pm(r['Valor'])}")
st.sidebar.caption("Meta demonstrativa: R$ 4.000.000")

st.markdown("""<div class=hero><h1>Inside Sales Smart Hub V9</h1><p>From Reactive Requests to Intelligent Revenue Growth</p>
<span class=pill>Workflow</span><span class=pill>Priority</span><span class=pill>Growth</span><span class=pill>Autonomous Agent</span><span class=pill>Salesforce</span></div>""",unsafe_allow_html=True)

if page.startswith("1."):
    st.subheader("Central de Decisão")
    x=opps[~opps["Status SF"].isin(["Order Promised","Lost Closed"])]
    a,b,c,d=st.columns(4); a.metric("Pipeline",brl(x.Valor.sum()),f"{len(x)} OPPs"); b.metric("Cross Sell / Upsell",brl(growth["Valor potencial"].sum()),f"{len(growth)} sinais"); c.metric("Eficiência Comercial","91%","SLA + FUP"); d.metric("Meta",brl(META),pm(x.Valor.sum())+" pipeline")
    st.markdown("#### Funil Salesforce × Meta")
    s=summary(); s["% Meta"]=s.Valor.map(pm); s["Valor"]=s.Valor.map(brl); st.dataframe(s,use_container_width=True,hide_index=True)
    st.markdown("#### Prioridades Comerciais")
    v=x.sort_values("Score",ascending=False)[["Prioridade","Cliente","Score","Valor","Status SF","Responsável","Próxima Ação"]].copy(); v.Valor=v.Valor.map(brl); st.dataframe(v,use_container_width=True,hide_index=True)

elif page.startswith("2."):
    st.subheader("Performance Comercial do Time")
    t=team.copy(); t.Pipeline=t.Pipeline.map(brl); t["Receita Incremental"]=t["Receita Incremental"].map(brl); st.dataframe(t,use_container_width=True,hide_index=True)
    a=opps[opps.Responsável=="Agente Autônomo"]; c1,c2,c3=st.columns(3); c1.metric("Pipeline Agente",brl(a.Valor.sum()),f"{len(a)} OPPs"); c2.metric("Capacidade liberada","18 h/mês","demo"); c3.metric("Handoff","Menor carga","Índice de Carga Comercial")
    st.info("Performance Comercial e Índice de Carga Comercial são métricas distintas. Handoff do agente vai ao vendedor com menor carga.")

elif page.startswith("3."):
    st.subheader("Smart Workflow")
    st.markdown("Chamado / e-mail / WhatsApp → cliente identificado → **OPP Salesforce criada automaticamente em Identify** → enriquecimento → score → prioridade → responsável.")
    v=opps[["OPP","Prioridade","Cliente","Score","Status SF","Itens em Cotação","Valor","Cross Sell / Upsell","Responsável","Próxima Ação"]].copy(); v.Valor=v.Valor.map(brl); st.dataframe(v,use_container_width=True,hide_index=True)
    o=st.selectbox("Abrir oportunidade",opps.OPP,format_func=lambda z:f"OPP {z} — {opps.loc[opps.OPP==z,'Cliente'].iloc[0]}"); r=opps[opps.OPP==o].iloc[0]
    c1,c2,c3,c4=st.columns(4); c1.metric("Score",r.Score,r.Prioridade); c2.metric("Valor",brl(r.Valor)); c3.metric("Salesforce",r["Status SF"]); c4.metric("Responsável",r.Responsável)
    st.markdown(f"<div class=box><b>Recomendação da IA</b><br>{r['Próxima Ação']}<br>Itens: {r['Itens em Cotação']}<br>Growth: {r['Cross Sell / Upsell']}</div>",unsafe_allow_html=True)
    ns=st.selectbox("Atualizar status Salesforce",STAGES,index=STAGES.index(r["Status SF"]))
    if st.button("Salvar atualização"): st.session_state.opps.loc[st.session_state.opps.OPP==o,"Status SF"]=ns; st.rerun()
    st.caption("PDF comercial da V9: cliente não vê List Price nem desconto; oportunidade adicional permanece separada como OPCIONAL. Gerar PDF não muda estágio; Propose somente após envio.")

elif page.startswith("4."):
    st.subheader("Fila Inteligente — Smart Priority")
    q=opps[["Cliente","OPP","Prioridade","Score","Receita","Conversão","Estoque","SLA","Crédito"]].sort_values("Score",ascending=False).copy()
    for c,m in [("Receita",30),("Conversão",25),("Estoque",20),("SLA",15),("Crédito",10)]: q[c]=q[c].astype(str)+f"/{m}"
    q=q.rename(columns={"Score":"Score Total"}); st.dataframe(q,use_container_width=True,hide_index=True)
    st.info("Referência — Receita 30 | Conversão 25 | Estoque 20 | SLA 15 | Crédito 10. Altíssima ≥80 | Alta 60–79 | Normal <60.")
    st.markdown("**Fluxo reativo:** Normal + até R$10 mil → Agente Autônomo. Normal > R$10 mil → vendedor. Alta/Altíssima → vendedor.")

elif page.startswith("5."):
    st.subheader("Growth Engine")
    st.markdown("O Growth **levanta demanda antes de gerar proposta**: item + quantidade + potencial interno + argumento de valor.")
    g=growth.copy(); g["Valor potencial"]=g["Valor potencial"].map(brl); st.dataframe(g,use_container_width=True,hide_index=True)
    i=st.selectbox("Selecionar sinal",range(len(growth)),format_func=lambda z:f"{growth.iloc[z].Cliente} — {growth.iloc[z]['Item sugerido']} — {int(growth.iloc[z]['Qtd. sugerida'])} un."); r=growth.iloc[i]
    st.text_area("Texto inicial — e-mail / WhatsApp",message(r),height=140)
    st.markdown("<div class=agent><b>Agente Autônomo no Growth</b><br>Pode realizar abordagem proativa em sinais de até R$50.000. A primeira mensagem não mostra preço; vende disponibilidade, redução de risco e valor operacional.</div>",unsafe_allow_html=True)
    st.markdown("**Sem interação:** sinal de Growth. **Cliente interagiu/demonstrou interesse:** cria OPP em Identify e entra no fluxo normal.")

elif page.startswith("6."):
    st.subheader("FUP")
    st.markdown("Após proposta enviada: **D+2 → D+5 → D+10 → a cada 5 dias até fechamento**.")
    f=opps[opps["Status SF"].isin(["Develop","Propose"])].copy(); f["Dias aguardando resposta"]=[2,5,11,7,3,16,4,9][:len(f)]; f["Próximo FUP"]=f["Dias aguardando resposta"].apply(lambda d:"Vencido" if d>10 else ("Hoje" if d in [2,5,10] else "Programado")); f["Comentários"]=""
    c1,c2,c3=st.columns(3); c1.metric("FUP hoje",(f["Próximo FUP"]=="Hoje").sum()); c2.metric("Vencidos",(f["Próximo FUP"]=="Vencido").sum()); c3.metric("Valor aguardando",brl(f.Valor.sum()))
    v=f[["OPP","Cliente","Valor","Dias aguardando resposta","Vendedor","Status SF","Próximo FUP","Comentários"]].copy(); v.Valor=v.Valor.map(brl); st.data_editor(v,use_container_width=True,hide_index=True)
    st.caption("Order Promised e Lost Closed saem da fila ativa.")

elif page.startswith("7."):
    st.subheader("Account 360"); cli=st.selectbox("Cliente",sorted(opps.Cliente.unique())); x=opps[opps.Cliente==cli]
    a,b,c=st.columns(3); a.metric("Pipeline",brl(x.Valor.sum())); b.metric("OPPs",len(x)); c.metric("Maior Score",x.Score.max()); st.dataframe(x,use_container_width=True,hide_index=True)
    if len(growth[growth.Cliente==cli]): st.markdown("#### Growth"); st.dataframe(growth[growth.Cliente==cli],use_container_width=True,hide_index=True)

elif page.startswith("8."):
    st.subheader("Arquitetura")
    st.markdown("""**Entrada** chamado/e-mail/WhatsApp → **OPP Salesforce Identify** → enriquecimento → **Priority Score** → roteamento → execução humana/agente → **Develop** (contato efetivo) → **Propose** (proposta enviada) → aceite/OC → validações automáticas → **confirmação humana obrigatória** → **Order Promised** → Backoffice.  
**Growth:** identifica demanda não solicitada → item + quantidade + argumento de valor → abordagem até R$50 mil → interação do cliente cria OPP em Identify.  
**Governança:** exceção comercial, crédito, estoque ou pricing fora de política → handoff ao vendedor com menor Índice de Carga Comercial.""")

else:
    st.subheader("Modo Apresentação")
    st.markdown("""### Inside Sales Smart Hub — From Reactive Requests to Intelligent Revenue Growth
**1. Smart Workflow | Produtividade** — captura, Salesforce, SLA/FUP e automação controlada.  
**2. Smart Priority | Conversão** — Receita + Conversão + Estoque + SLA + Crédito.  
**3. Smart Growth | Receita Incremental** — identifica demanda antes do chamado, recomenda item/quantidade e aborda com venda de valor.  

**Princípio:** automatizamos o volume e preservamos o vendedor para julgamento comercial e maior impacto.  
**30 dias:** D1–5 baseline/SLA • D6–10 fila/scoring • D11–20 FUP/dashboard • D21–30 Growth + piloto do agente.""")
