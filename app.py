import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title='Inside Sales Smart Hub V3', page_icon='⚡', layout='wide')

st.markdown('''
<style>
.block-container{padding-top:1rem;padding-bottom:2rem}
.hero{background:linear-gradient(90deg,#0b4f8a,#0d74c7);padding:22px 24px;border-radius:18px;color:white;margin-bottom:18px}
.hero h1{margin:0;font-size:34px}
.hero p{margin:6px 0 0 0;opacity:.92}
.card{background:white;border:1px solid #e7edf3;border-radius:16px;padding:16px 18px;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.small{font-size:12px;color:#667085}
</style>
''', unsafe_allow_html=True)

st.markdown('''
<div class="hero">
<h1>Inside Sales Smart Hub V3</h1>
<p>From Reactive Requests to Intelligent Revenue Growth</p>
</div>
''', unsafe_allow_html=True)

if "quotes" not in st.session_state:
    st.session_state.quotes = pd.DataFrame([
        [1001,"Hospital Alfa","Kit Manutenção","Ana",98000,0.91,1.1,24,"Aprovado","Atacar agora"],
        [1002,"Hospital Beta","Sensor de Fluxo","Bruno",45000,0.78,2.8,8,"Aprovado","Alta prioridade"],
        [1003,"Clínica Gama","Filtro Premium","Carla",18000,0.84,0.7,90,"Aprovado","Atacar agora"],
        [1004,"MedCenter Delta","Módulo Eletrônico","Ana",125000,0.63,4.9,6,"Revisar","Revisar crédito"],
        [1005,"Hospital Épsilon","Bateria Backup","Bruno",76000,0.88,1.5,18,"Aprovado","Atacar agora"],
        [1006,"Instituto Zeta","Contrato Preventivo","Carla",52000,0.69,3.2,999,"Aprovado","Alta prioridade"],
        [1007,"Rede Saúde Sul","Kit Manutenção","Ana",186000,0.94,0.5,12,"Aprovado","Atacar agora"],
        [1008,"Hospital Ômega","Válvula","Bruno",32000,0.52,6.4,40,"Bloqueado","Revisar crédito"],
        [1009,"Clínica Sigma","Sensor de Fluxo","Carla",26000,0.66,2.1,14,"Aprovado","Alta prioridade"],
        [1010,"Centro Médico Prime","Bateria Backup","Ana",68000,0.81,1.2,22,"Aprovado","Atacar agora"],
    ], columns=["ID","Cliente","Produto","Vendedor","Valor","Prob","SLA_h","Estoque","Credito","Acao"])

    st.session_state.accounts = pd.DataFrame([
        ["Hospital Alfa","Ana",980000,1120000,760000,8,420000,140000,41],
        ["Hospital Beta","Bruno",720000,690000,410000,11,300000,40000,96],
        ["Clínica Gama","Carla",410000,470000,355000,4,180000,25000,32],
        ["MedCenter Delta","Ana",610000,560000,390000,6,250000,45000,101],
        ["Hospital Épsilon","Bruno",830000,910000,590000,15,500000,80000,19],
        ["Instituto Zeta","Carla",350000,380000,210000,5,160000,40000,64],
        ["Rede Saúde Sul","Ana",1320000,1450000,860000,23,800000,260000,12],
        ["Hospital Ômega","Bruno",290000,320000,180000,3,120000,2000,144],
        ["Clínica Sigma","Carla",190000,215000,165000,2,90000,35000,47],
        ["Centro Médico Prime","Ana",540000,610000,430000,7,220000,52000,33],
    ], columns=["Cliente","Vendedor","Fat_2024","Fat_2025","Fat_2026_YTD","Base_Instalada","Limite_Credito","Credito_Livre","Dias_Ultima_Compra"])

    st.session_state.installed = pd.DataFrame([
        ["Hospital Alfa","Ventilador A",5,2019,14],
        ["Hospital Alfa","Monitor X",3,2021,9],
        ["Hospital Beta","Ventilador A",7,2018,15],
        ["Clínica Gama","Monitor X",4,2022,11],
        ["MedCenter Delta","Ventilador B",6,2019,16],
        ["Hospital Épsilon","Ventilador A",10,2017,18],
        ["Hospital Épsilon","Ventilador B",5,2020,13],
        ["Instituto Zeta","Monitor X",5,2021,10],
        ["Rede Saúde Sul","Ventilador A",14,2018,17],
        ["Rede Saúde Sul","Ventilador B",9,2020,12],
        ["Hospital Ômega","Ventilador A",3,2017,20],
        ["Clínica Sigma","Monitor X",2,2022,8],
        ["Centro Médico Prime","Ventilador B",7,2019,15],
    ], columns=["Cliente","Equipamento","Qtd","Ano_Instalacao","Meses_Desde_Compra"])

def brl(v):
    return f"R$ {v:,.0f}".replace(",", "X").replace(".", ",").replace("X",".")

def score_row(r, w=None):
    if w is None:
        w = {"Receita":30,"Conversão":25,"Estoque":20,"SLA":15,"Crédito":10}
    s_receita = min(100,max(10,r["Valor"]/180000*100))
    s_conv = r["Prob"]*100
    s_estoque = min(100,max(0,r["Estoque"]/max(1,r["Valor"]/10000)*8))
    s_sla = min(100,max(0,4/max(.1,r["SLA_h"])*100))
    s_credito = 100 if r["Credito"]=="Aprovado" else (40 if r["Credito"]=="Revisar" else 0)
    total = sum(w.values())
    return round((s_receita*w["Receita"]+s_conv*w["Conversão"]+s_estoque*w["Estoque"]+s_sla*w["SLA"]+s_credito*w["Crédito"])/total)

quotes = st.session_state.quotes.copy()
quotes["Score"] = quotes.apply(score_row, axis=1)
quotes["Criticidade"] = np.select([quotes["Score"]>=80,quotes["Score"]>=65],["Crítica","Alta"],default="Normal")
quotes = quotes.sort_values(["Score","Valor"], ascending=[False,False])

page = st.sidebar.radio("Navegação",[
    "Central de Decisão","Dashboard Executivo","Fila Inteligente",
    "Account 360","Growth Engine","Cockpit do Coordenador","Simulador What If"
])

st.sidebar.markdown("---")
st.sidebar.metric("Operação","600 orçamentos/mês","≈30 por dia útil")
st.sidebar.metric("Time","3 colaboradores")
st.sidebar.caption("Dados fictícios para Business Case")

if page == "Central de Decisão":
    st.subheader("O que precisa da minha atenção agora?")
    crit = quotes[quotes["Criticidade"]=="Crítica"]
    atras = quotes[quotes["SLA_h"]>4]
    growth_pot = int(st.session_state.accounts["Base_Instalada"].sum()*8500)
    c1,c2,c3=st.columns(3)
    with c1:
        st.metric("Faça agora",len(crit),brl(crit["Valor"].sum()))
    with c2:
        st.metric("Fora do SLA",len(atras))
    with c3:
        st.metric("Receita proativa estimada",brl(growth_pot))
    st.info(f"Há {len(crit)} oportunidades críticas. Se tratadas nas próximas 4 horas, o time protege {brl(crit['Valor'].sum())} de pipeline prioritário.")
    st.dataframe(quotes[["ID","Cliente","Produto","Vendedor","Valor","Score","SLA_h","Acao"]].head(5),use_container_width=True,hide_index=True)

elif page == "Dashboard Executivo":
    st.subheader("Visão executiva da operação")
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Orçamentos em carteira",len(quotes))
    c2.metric("Pipeline",brl(quotes["Valor"].sum()))
    c3.metric("Conversão estimada",f"{quotes['Prob'].mean()*100:.0f}%")
    c4.metric("SLA médio",f"{quotes['SLA_h'].mean():.1f} h")
    perf=quotes.groupby("Vendedor").agg(Oportunidades=("ID","count"),Pipeline=("Valor","sum"),Score_Medio=("Score","mean"),SLA_Medio=("SLA_h","mean")).reset_index()
    st.dataframe(perf,use_container_width=True,hide_index=True)

elif page == "Fila Inteligente":
    st.subheader("Smart Priority — fila por impacto, não por ordem de chegada")
    st.dataframe(quotes[["ID","Cliente","Produto","Vendedor","Valor","Score","Criticidade","SLA_h","Credito","Acao"]],use_container_width=True,hide_index=True)
    sel=st.selectbox("Abrir oportunidade",quotes["ID"].tolist())
    r=quotes[quotes["ID"]==sel].iloc[0]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Priority Score",f"{r.Score}/100")
    c2.metric("Valor",brl(r.Valor))
    c3.metric("SLA",f"{r.SLA_h:.1f} h")
    c4.metric("Conversão",f"{r.Prob*100:.0f}%")
    st.success(f"Próxima melhor ação: {r.Acao}")

elif page == "Account 360":
    st.subheader("Account 360 — visão comercial consolidada")
    cliente=st.selectbox("Cliente",st.session_state.accounts["Cliente"].tolist())
    a=st.session_state.accounts[st.session_state.accounts.Cliente==cliente].iloc[0]
    inst=st.session_state.installed[st.session_state.installed.Cliente==cliente]
    oq=quotes[quotes.Cliente==cliente]
    c1,c2,c3,c4=st.columns(4)
    c1.metric("Faturamento 2025",brl(a.Fat_2025))
    c2.metric("2026 YTD",brl(a.Fat_2026_YTD))
    c3.metric("Base instalada",f"{int(a.Base_Instalada)} equipamentos")
    c4.metric("Crédito livre",brl(a.Credito_Livre))
    st.dataframe(inst,use_container_width=True,hide_index=True)
    if len(oq):
        st.dataframe(oq[["ID","Produto","Valor","Score","Acao"]],use_container_width=True,hide_index=True)
    if a.Dias_Ultima_Compra>60:
        st.info(f"Cliente está há {int(a.Dias_Ultima_Compra)} dias sem comprar. Avaliar reativação.")
    if len(inst) and (inst["Meses_Desde_Compra"]>=12).any():
        st.info("Há itens da base instalada com recorrência vencida. Sugerir abordagem proativa.")

elif page == "Growth Engine":
    st.subheader("Smart Growth — gerar receita antes do próximo chamado")
    g=st.session_state.installed.merge(st.session_state.accounts[["Cliente","Vendedor","Credito_Livre","Dias_Ultima_Compra"]],on="Cliente",how="left")
    g["Idade_Parque"]=2026-g["Ano_Instalacao"]
    g["Growth_Score"]=(g["Meses_Desde_Compra"]>=12).astype(int)*35+(g["Idade_Parque"]>=5).astype(int)*30+(g["Credito_Livre"]>30000).astype(int)*20+(g["Dias_Ultima_Compra"]>45).astype(int)*15
    g["Potencial"]=g["Qtd"]*8500
    st.dataframe(g.sort_values("Growth_Score",ascending=False),use_container_width=True,hide_index=True)
    high=g[g["Growth_Score"]>=70]
    st.success(f"{len(high)} oportunidades proativas de alta aderência, com potencial de {brl(high['Potencial'].sum())}.")

elif page == "Cockpit do Coordenador":
    st.subheader("Cockpit do Coordenador — gestão de pessoas e operação")
    perf=quotes.groupby("Vendedor").agg(Oportunidades=("ID","count"),Pipeline=("Valor","sum"),Score_Medio=("Score","mean"),SLA_Medio=("SLA_h","mean"),Conversao=("Prob","mean")).reset_index()
    perf["Conversao"]=perf["Conversao"]*100
    st.dataframe(perf,use_container_width=True,hide_index=True)
    for _,r in perf.iterrows():
        if r.SLA_Medio>4:
            st.warning(f"{r.Vendedor}: revisar carga e redistribuir oportunidades.")
        elif r.Conversao<70:
            st.info(f"{r.Vendedor}: coaching em qualificação e follow-up.")
        else:
            st.success(f"{r.Vendedor}: desempenho equilibrado.")

elif page == "Simulador What If":
    st.subheader("What If? — simule decisões de gestão")
    c1,c2,c3=st.columns(3)
    wr=c1.slider("Peso Receita",10,50,30)
    wc=c2.slider("Peso Conversão",10,50,25)
    we=c3.slider("Peso Estoque",5,40,20)
    c1,c2=st.columns(2)
    wsla=c1.slider("Peso SLA",5,30,15)
    wcred=c2.slider("Peso Crédito",0,30,10)
    sim=st.session_state.quotes.copy()
    sim["Score"]=sim.apply(lambda r:score_row(r,{"Receita":wr,"Conversão":wc,"Estoque":we,"SLA":wsla,"Crédito":wcred}),axis=1)
    st.dataframe(sim.sort_values(["Score","Valor"],ascending=[False,False])[["ID","Cliente","Produto","Valor","Score","SLA_h","Credito"]],use_container_width=True,hide_index=True)
    st.info("A lógica é parametrizável e pode ser calibrada com dados históricos reais.")

st.markdown("---")
st.caption("Inside Sales Smart Hub V3 • MVP demonstrativo • dados 100% fictícios")
