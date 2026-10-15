from pathlib import Path
import json, math
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Comparador de Zonas de Praticagem", page_icon="⚓", layout="wide")
ROOT=Path(__file__).resolve().parent
STATE_FILE=ROOT/"sessao_zp.json"

@st.cache_data
def load_data():
    zones=pd.read_csv(ROOT/"dados_zp.csv", dtype={"ZP":str}).fillna("")
    hist=pd.read_csv(ROOT/"fainas_historicas.csv", dtype={"ZP_serie":str})
    sources=pd.read_csv(ROOT/"fontes.csv").fillna("")
    hist["Ano"]=pd.to_numeric(hist["Ano"],errors="coerce").astype("Int64")
    hist["Fainas"]=pd.to_numeric(hist["Fainas"],errors="coerce")
    zones["Lotacao_praticos"]=pd.to_numeric(zones["Lotacao_praticos"],errors="coerce")
    return zones,hist,sources
zones,hist,sources=load_data()
ids=zones["ZP"].tolist(); names=dict(zip(zones.ZP,zones.Abrangencia)); idx={z:i for i,z in enumerate(ids)}; n=len(ids)

def blank_state(): return {"history":[],"ranking":None,"initial_order":list(range(n))}
def load_state():
    if STATE_FILE.exists():
        try:
            s=json.loads(STATE_FILE.read_text(encoding="utf-8"))
            if isinstance(s,dict) and isinstance(s.get("history"),list): return s
        except Exception: pass
    return blank_state()
if "zp_state" not in st.session_state: st.session_state.zp_state=load_state()
state=st.session_state.zp_state

def save_state(): STATE_FILE.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
def history_map():
    d={}
    for h in state["history"]:
        a,b,r=h["a"],h["b"],h["result"]
        d[(a,b)]=r; d[(b,a)]=2 if r==1 else 1 if r==2 else 0
    return d

def tie_components():
    parent=list(range(n))
    def find(x):
        while parent[x]!=x:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        ra,rb=find(a),find(b)
        if ra!=rb: parent[rb]=ra
    for h in state["history"]:
        if h["result"]==0: union(h["a"],h["b"])
    return [find(i) for i in range(n)]

def relation(a,b):
    if a==b:return 0
    hm=history_map()
    if (a,b) in hm:return hm[(a,b)]
    comp=tie_components()
    if comp[a]==comp[b]:return 0
    roots=sorted(set(comp)); ri={r:i for i,r in enumerate(roots)}; g=[[False]*len(roots) for _ in roots]
    for h in state["history"]:
        aa,bb,r=h["a"],h["b"],h["result"]
        better,worse=(aa,bb) if r==1 else ((bb,aa) if r==2 else (None,None))
        if better is not None and comp[better]!=comp[worse]:g[ri[comp[better]]][ri[comp[worse]]]=True
    for k in range(len(roots)):
        for i in range(len(roots)):
            if g[i][k]:
                for j in range(len(roots)):g[i][j]=g[i][j] or g[k][j]
    aa,bb=ri[comp[a]],ri[comp[b]]; ab,ba=g[aa][bb],g[bb][aa]
    if ab and not ba:return 1
    if ba and not ab:return 2
    return None
class NeedComparison(Exception):
    def __init__(self,a,b):self.a,self.b=a,b

def merge_sort(items):
    if len(items)<=1:return list(items)
    mid=len(items)//2; left=merge_sort(items[:mid]); right=merge_sort(items[mid:]); out=[]; i=j=0
    while i<len(left) and j<len(right):
        a,b=left[i],right[j]; r=relation(a,b)
        if r is None:raise NeedComparison(a,b)
        if r==1:out.append(a);i+=1
        elif r==2:out.append(b);j+=1
        else:out.extend([a,b]);i+=1;j+=1
    return out+left[i:]+right[j:]

def compute_ranking():
    try: order=merge_sort(state.get("initial_order",list(range(n))))
    except NeedComparison as q:return None,q
    comp=tie_components(); group_rank={}; rows=[]
    for pos,i in enumerate(order,1):
        root=comp[i]
        if root not in group_rank:group_rank[root]=pos
        rows.append({"Posição":group_rank[root],"ID":ids[i],"Zona de Praticagem":names[ids[i]],"Lotação informada":zones.iloc[i]["Lotacao_praticos"] if zones.iloc[i]["Lotacao_praticos"]!="" else None})
    return pd.DataFrame(rows),None

def get_series(z): return hist[hist.ZP_serie.eq(z)].sort_values("Ano")
def profile(z):
    row=zones[zones.ZP.eq(z)].iloc[0]
    st.markdown(f"### {z} — {row['Abrangencia']}")
    c1,c2,c3=st.columns(3)
    c1.metric("Lotação informada", str(int(row["Lotacao_praticos"])) if pd.notna(row["Lotacao_praticos"]) else "Não disponível")
    s=get_series(z)
    if len(s): c2.metric("Fainas em 2025", f"{int(s.Fainas.iloc[-1]):,}".replace(",","."))
    else:c2.metric("Fainas em 2025","Não disponível")
    idhm=row["IDHM"]
    c3.metric("IDHM", str(idhm) if idhm else "Não disponível")
    st.caption("Os indicadores ausentes não foram estimados. O IDHM deve sempre ser acompanhado do ano de referência e do município a que se refere.")
    fields=[("IDHM","Ano_IDHM"),("Renda_per_capita","Ano_referencia"),("PIB_per_capita","Ano_referencia"),("Populacao","Ano_referencia"),("Custo_vida","Ano_referencia"),("Seguranca_publica","Ano_referencia"),("Saude","Ano_referencia"),("Educacao","Ano_referencia"),("Mobilidade","Ano_referencia"),("Aeroporto_comercial","Ano_referencia"),("Distancia_linha_reta_km","Ano_referencia"),("Distancia_rodoviaria_km","Ano_referencia"),("Tempo_rodoviario_min","Ano_referencia"),("Conectividade_aerea","Ano_referencia"),("Caracteristicas_operacionais","Ano_referencia")]
    data=[]
    for field,yearfield in fields:
        value=row[field]
        data.append({"Indicador":field.replace("_"," "),"Valor":value if value!="" else "Não disponível","Ano de referência":row[yearfield] if row[yearfield]!="" else "Não informado"})
    st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
    if len(s):
        fig=px.line(s,x="Ano",y="Fainas",markers=True,title="Histórico transcrito de fainas (2017–2025)")
        st.plotly_chart(fig,use_container_width=True)
        vals=s.Fainas.dropna()
        if len(vals):
            a,b=int(vals.iloc[0]),int(vals.iloc[-1]); pct=((b/a)-1)*100 if a else None
            mx=s.loc[s.Fainas.idxmax()]; mn=s.loc[s.Fainas.idxmin()]
            c=st.columns(4); c[0].metric("Média anual",f"{vals.mean():,.1f}".replace(",","X").replace(".",",").replace("X",".")); c[1].metric("Variação 2017–2025",f"{pct:+.1f}%" if pct is not None else "N/A"); c[2].metric("Maior volume",f"{int(mx.Fainas)} ({int(mx.Ano)})"); c[3].metric("Menor volume",f"{int(mn.Fainas)} ({int(mn.Ano)})")
        st.caption("Séries históricas são apresentadas como transcritas do gráfico fornecido. Não foram validadas independentemente com base oficial; zero não foi confirmado como ausência real de fainas.")

def _excel_bytes(df):
    from io import BytesIO
    b=BytesIO()
    with pd.ExcelWriter(b,engine="openpyxl") as writer:df.to_excel(writer,index=False,sheet_name="Dados")
    return b.getvalue()

st.title("⚓ Comparador de Zonas de Praticagem")
st.caption("Comparação adaptativa por merge sort interativo, com reaproveitamento de julgamentos, transitividade e empates conforme a estrutura do script MATLAB.")
st.info("O ranking reflete as preferências declaradas pelo usuário, não uma avaliação universal da qualidade das ZPs. Os indicadores exibidos são informativos e não alteram automaticamente a ordenação.")
tabs=st.tabs(["Comparar ZPs","Perfil das ZPs","Comparação detalhada","Ranking e histórico","Dados e fontes"])
with tabs[0]:
    st.subheader("Escolha a ZP preferida em cada comparação")
    ranking,pending=compute_ranking()
    if pending is None:
        state["ranking"]=ranking.to_dict(orient="records");save_state()
        st.success("Ranking concluído com os julgamentos registrados.")
        st.dataframe(ranking,use_container_width=True,hide_index=True)
        st.download_button("Baixar ranking (CSV)",ranking.to_csv(index=False).encode("utf-8-sig"),"ranking_zp.csv","text/csv")
    else:
        a,b=pending.a,pending.b
        # progresso: compara o número de julgamentos com o limite teórico, não afirma percentual exato do algoritmo
        st.progress(min(len(state["history"])/69,1.0),text=f"Julgamentos respondidos: {len(state['history'])} (limite teórico informado pelo MATLAB: 69 comparações)")
        ca,cb=st.columns(2,gap="large")
        for col,z,label in [(ca,ids[a],"ZP A"),(cb,ids[b],"ZP B")]:
            with col:
                with st.container(border=True):
                    st.caption(label); st.markdown(f"## {z}"); st.write(names[z])
                    row=zones[zones.ZP.eq(z)].iloc[0]
                    st.metric("Lotação informada",str(int(row.Lotacao_praticos)) if pd.notna(row.Lotacao_praticos) else "Não disponível")
                    ss=get_series(z)
                    if len(ss):st.metric("Fainas em 2025",f"{int(ss.Fainas.iloc[-1]):,}".replace(",","."))
                    if row["Grupo_contextual"]:st.caption(row["Grupo_contextual"])
                    st.caption("Dados de IDHM, aeroporto e qualidade de vida ainda não confirmados na base local.")
        st.markdown("**Qual das duas ZPs é globalmente melhor para você?**")
        c1,c2,c3=st.columns(3)
        if c1.button(f"Prefiro {ids[a]}",type="primary",use_container_width=True):state["history"].append({"a":a,"b":b,"result":1});state["ranking"]=None;save_state();st.rerun()
        if c2.button(f"Prefiro {ids[b]}",use_container_width=True):state["history"].append({"a":a,"b":b,"result":2});state["ranking"]=None;save_state();st.rerun()
        if c3.button("Empate",use_container_width=True):state["history"].append({"a":a,"b":b,"result":0});state["ranking"]=None;save_state();st.rerun()
    ca,cb=st.columns(2)
    if ca.button("Desfazer último julgamento",disabled=not state["history"],use_container_width=True):state["history"].pop();state["ranking"]=None;save_state();st.rerun()
    if cb.button("Reiniciar ranking",use_container_width=True):state.clear();state.update(blank_state());save_state();st.rerun()
    with st.expander("Salvar ou retomar em outro dispositivo"):
        st.download_button("Exportar sessão JSON",json.dumps(state,ensure_ascii=False,indent=2).encode("utf-8"),"sessao_zp.json","application/json")
        uploaded=st.file_uploader("Importar sessão JSON",type=["json"])
        if uploaded and st.button("Restaurar sessão importada"):
            try:
                s=json.load(uploaded)
                if not isinstance(s.get("history"),list):raise ValueError("Formato de sessão inválido")
                for h in s["history"]:
                    if h["a"] not in range(n) or h["b"] not in range(n) or h["result"] not in [0,1,2]:raise ValueError("Julgamento fora dos limites")
                state.clear();state.update(s);save_state();st.success("Sessão restaurada.");st.rerun()
            except Exception as e:st.error(f"Não foi possível importar a sessão: {e}")
with tabs[1]:
    z=st.selectbox("Selecione uma ZP",ids,key="profile_zp");profile(z)
with tabs[2]:
    ca,cb=st.columns(2); za=ca.selectbox("ZP A",ids,index=0,key="detail_a"); zb=cb.selectbox("ZP B",ids,index=1,key="detail_b")
    if za==zb:st.warning("Selecione duas ZPs diferentes para comparar.")
    else:
        A=zones[zones.ZP.eq(za)].iloc[0];B=zones[zones.ZP.eq(zb)].iloc[0]
        fields=[("Abrangência","Abrangencia"),("Lotação","Lotacao_praticos"),("IDHM","IDHM"),("Ano do IDHM","Ano_IDHM"),("Renda per capita","Renda_per_capita"),("PIB per capita","PIB_per_capita"),("População","Populacao"),("Aeroporto comercial","Aeroporto_comercial"),("Distância em linha reta (km)","Distancia_linha_reta_km"),("Distância rodoviária (km)","Distancia_rodoviaria_km"),("Tempo rodoviário (min)","Tempo_rodoviario_min"),("Características operacionais","Caracteristicas_operacionais")]
        data=[]
        for label,key in fields:data.append({"Indicador":label,za:A[key] if str(A[key]) else "Não disponível",zb:B[key] if str(B[key]) else "Não disponível"})
        st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
        fa,fb=st.columns(2)
        for col,z in [(fa,za),(fb,zb)]:
            ss=get_series(z)
            if len(ss):
                with col:st.plotly_chart(px.line(ss,x="Ano",y="Fainas",markers=True,title=f"{z} — {names[z]}"),use_container_width=True)
with tabs[3]:
    ranking,pending=compute_ranking()
    if state["history"]:
        rows=[]
        for i,h in enumerate(state["history"],1):rows.append({"Nº":i,"ZP A":ids[h["a"]],"Alternativa A":names[ids[h["a"]]],"ZP B":ids[h["b"]],"Alternativa B":names[ids[h["b"]]],"Resultado":"Empate" if h["result"]==0 else (f"{ids[h['a']]} melhor" if h["result"]==1 else f"{ids[h['b']]} melhor")})
        hdf=pd.DataFrame(rows);st.dataframe(hdf,use_container_width=True,hide_index=True)
        st.download_button("Baixar julgamentos (CSV)",hdf.to_csv(index=False).encode("utf-8-sig"),"julgamentos_zp.csv","text/csv")
        st.download_button("Baixar julgamentos (Excel)",_excel_bytes(hdf),"julgamentos_zp.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:st.info("Nenhum julgamento registrado.")
    if ranking is not None:
        st.subheader("Ranking final");st.dataframe(ranking,use_container_width=True,hide_index=True)
        st.download_button("Baixar ranking (Excel)",_excel_bytes(ranking),"ranking_zp.xlsx","application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:st.caption("Ranking ainda incompleto: falta ao menos uma comparação necessária pelo merge sort.")
with tabs[4]:
    st.subheader("Base de dados utilizada")
    st.write("As preferências de grupo são contextuais e preliminares; não são pesos nem posições fixas. Campos vazios significam dado não coletado/confirmado, não zero.")
    st.dataframe(zones,use_container_width=True,hide_index=True)
    st.download_button("Baixar cadastro de ZPs (CSV)",zones.to_csv(index=False).encode("utf-8-sig"),"dados_zp.csv","text/csv")
    st.subheader("Série histórica de fainas")
    st.dataframe(hist,use_container_width=True,hide_index=True)
    st.download_button("Baixar histórico (CSV)",hist.to_csv(index=False).encode("utf-8-sig"),"fainas_historicas.csv","text/csv")
    st.subheader("Fontes oficiais recomendadas e estado da coleta")
    st.dataframe(sources,use_container_width=True,hide_index=True)
    st.download_button("Baixar registro de fontes (CSV)",sources.to_csv(index=False).encode("utf-8-sig"),"fontes.csv","text/csv")
    st.warning("Não foram preenchidos valores de IDHM, renda, PIB, segurança, saúde, aeroportos ou distâncias sem validação por município e ano. Esses indicadores continuam pendentes; não seriam confiáveis se inventados.")

