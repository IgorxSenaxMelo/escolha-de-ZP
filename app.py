# app.py
# Comparador e ranking interativo de Zonas de Praticagem
# Adaptado do algoritmo MATLAB enviado: merge sort, histórico de julgamentos,
# inferência por transitividade, empates e retomada de sessão.

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Comparador de ZP", page_icon="⚓", layout="wide")

SESSION_FILE = Path("sessao_zp.json")

# Mesmas 20 alternativas e IDs do script MATLAB enviado.
alternativas = [
    ("ZP14", "Vitória, Tubarão e Ubu–ES"),
    ("ZP16", "Santos e São Sebastião–SP"),
    ("ZP05", "Fortaleza e Pecém–CE"),
    ("ZP10", "Maceió, Terminal Químico e Sergipe/TMIB–AL/SE"),
    ("ZP15", "Rio, Niterói, Sepetiba e Angra–RJ"),
    ("ZP07", "Natal–RN"),
    ("ZP04", "Itaqui, Alumar e Ponta da Madeira–MA"),
    ("ZP17", "Paranaguá e Antonina–PR"),
    ("ZP09", "Recife e Suape–PE"),
    ("ZP19", "Rio Grande–RS"),
    ("ZP08", "Cabedelo–PB"),
    ("ZP22", "Imbituba–SC"),
    ("ZP18", "São Francisco do Sul–SC"),
    ("ZP21", "Itajaí e Navegantes–SC"),
    ("ZP06", "Areia Branca–RN"),
    ("ZP12", "Salvador e Baía de Todos os Santos–BA"),
    ("ZP20", "Lagoa dos Patos e terminais interiores–RS"),
    ("ZP03", "Belém e Vila do Conde–PA"),
    ("ZP01", "Fazendinha–Itacoatiara, AP/AM"),
    ("ZP02", "Itacoatiara–Tabatinga–AM"),
]
ids = [x[0] for x in alternativas]
nomes = [x[1] for x in alternativas]
n = len(ids)
id_to_idx = {v: i for i, v in enumerate(ids)}

# Lotação transcrita da tabela fornecida.
lotacao_data = {
    "ZP01": 160, "ZP02": 35, "ZP03": 36, "ZP04": 33, "ZP05": 13,
    "ZP06": 3, "ZP07": 4, "ZP08": 4, "ZP09": 14, "ZP10": 5,
    "ZP12": 27, "ZP14": 28, "ZP15": 65, "ZP16": 58, "ZP17": 30,
    "ZP18": 17, "ZP19": 22, "ZP20": 5, "ZP21": 13, "ZP22": 5,
}
zones = pd.DataFrame([
    {"ZP": z, "Zona de Praticagem": nomes[i], "Lotação": lotacao_data.get(z)}
    for i, z in enumerate(ids)
])

# Séries transcritas visualmente do gráfico de fainas.
years = list(range(2017, 2026))
fainas_rows = [
    ("ZP01", "Amapá", [2657,2603,2664,2809,2744,2923,3327,3048,3042]),
    ("ZP02", "Amazonas", [1560,1587,1545,1431,1329,1510,1322,1208,1227]),
    ("ZP03", "Pará", [3434,4713,3521,3702,3801,4470,4684,4388,4499]),
    ("ZP04", "Maranhão", [3792,3962,3919,4003,4067,3976,4014,3971,3967]),
    ("ZP05", "Ceará", [2270,2391,2545,2443,2717,2356,2379,2606,2551]),
    ("ZP06", "Areia Branca", [155,189,165,136,148,146,130,136,127]),
    ("ZP07", "Natal", [250,213,210,177,127,164,152,150,136]),
    ("ZP08", "Paraíba", [232,198,178,177,200,204,197,210,184]),
    ("ZP09", "Pernambuco", [3611,3277,3342,3371,3276,3423,3562,3834,3666]),
    ("ZP10", "Alagoas", [551,633,572,445,559,733,769,796,833]),
    ("ZP10-H", "Sergipe (linha histórica separada)", [135,79,85,81,138,7,0,0,0]),
    ("ZP12", "Salvador", [4220,4272,4524,4558,4429,3986,4271,4359,4032]),
    ("ZP12-H", "Ilhéus (linha histórica separada)", [78,88,32,0,0,0,0,0,0]),
    ("ZP14", "Espírito Santo", [4470,4051,3905,3280,3857,3641,3979,3822,4114]),
    ("ZP15", "Rio de Janeiro", [11594,12069,13022,12077,12560,14152,15998,16816,17344]),
    ("ZP16", "São Paulo", [12829,12316,12844,13156,12611,13474,14042,14089,14489]),
    ("ZP17", "Paraná", [5907,5895,5753,5015,5963,5819,6599,6763,6897]),
    ("ZP18", "São Francisco do Sul", [2320,2220,2318,2117,2264,2242,2451,2681,2716]),
    ("ZP19", "Rio Grande", [4440,4281,4149,3677,3974,3687,4074,4005,4347]),
    ("ZP20", "Lagoa dos Patos", [466,467,564,430,440,275,302,213,125]),
    ("ZP21", "Itajaí", [1885,1978,2102,2106,2147,2009,1677,1571,2139]),
    ("ZP22", "Imbituba", [499,572,464,451,581,641,632,733,647]),
]
fainas = pd.DataFrame([
    {"ZP": z, "Série histórica": nome, **dict(zip(years, vals))}
    for z, nome, vals in fainas_rows
])
long_fainas = fainas.melt(
    id_vars=["ZP", "Série histórica"], value_vars=years,
    var_name="Ano", value_name="Fainas"
)
long_fainas["Ano"] = long_fainas["Ano"].astype(int)

def blank_state():
    return {"history": [], "next_pair": None, "ranking": None}

def load_saved_state():
    if SESSION_FILE.exists():
        try:
            data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("history"), list):
                return data
        except Exception:
            pass
    return blank_state()

if "zp_state" not in st.session_state:
    st.session_state.zp_state = load_saved_state()
state = st.session_state.zp_state

def save_state():
    SESSION_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
    )

def history_map():
    # Mantém o último julgamento direto para cada par não ordenado.
    result = {}
    for h in state["history"]:
        a, b, r = h["a"], h["b"], h["result"]
        result[(a, b)] = r
        result[(b, a)] = (2 if r == 1 else 1 if r == 2 else 0)
    return result

class NeedComparison(Exception):
    def __init__(self, a, b):
        self.a, self.b = a, b

def tie_components():
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra
    for h in state["history"]:
        if h["result"] == 0:
            union(h["a"], h["b"])
    return [find(i) for i in range(n)]

def relation(a, b):
    """Retorna 1 se A>B, 2 se B>A, 0 empate, None se desconhecido."""
    if a == b:
        return 0
    hm = history_map()
    if (a, b) in hm:
        return hm[(a, b)]
    comp = tie_components()
    if comp[a] == comp[b]:
        return 0

    # Grafo de preferência entre classes de empate, conforme o MATLAB.
    roots = sorted(set(comp))
    root_idx = {r: i for i, r in enumerate(roots)}
    graph = [[False] * len(roots) for _ in roots]
    for h in state["history"]:
        a0, b0, r = h["a"], h["b"], h["result"]
        if r == 1:
            better, worse = a0, b0
        elif r == 2:
            better, worse = b0, a0
        else:
            continue
        if comp[better] != comp[worse]:
            graph[root_idx[comp[better]]][root_idx[comp[worse]]] = True
    # Fechamento transitivo de Warshall.
    for k in range(len(roots)):
        for i in range(len(roots)):
            if graph[i][k]:
                for j in range(len(roots)):
                    graph[i][j] = graph[i][j] or graph[k][j]
    ga, gb = root_idx[comp[a]], root_idx[comp[b]]
    ab, ba = graph[ga][gb], graph[gb][ga]
    if ab and not ba:
        return 1
    if ba and not ab:
        return 2
    return None

def merge_sort_interactive(items):
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort_interactive(items[:mid])
    right = merge_sort_interactive(items[mid:])
    result, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        a, b = left[i], right[j]
        r = relation(a, b)
        if r is None:
            raise NeedComparison(a, b)
        if r == 1:
            result.append(a)
            i += 1
        elif r == 2:
            result.append(b)
            j += 1
        else:
            # Mantém os empatados adjacentes, como no algoritmo MATLAB.
            result.extend([a, b])
            i += 1
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

def compute_ranking():
    try:
        order = merge_sort_interactive(list(range(n)))
        comps = tie_components()
        rank_for_root = {}
        rows = []
        for pos, idx in enumerate(order, start=1):
            root = comps[idx]
            if root not in rank_for_root:
                rank_for_root[root] = pos
            rows.append({
                "Posição": rank_for_root[root],
                "ID": ids[idx],
                "Zona de Praticagem": nomes[idx],
                "Lotação": lotacao_data.get(ids[idx]),
            })
        return pd.DataFrame(rows), None
    except NeedComparison as needed:
        return None, needed

st.title("⚓ Comparador de Zonas de Praticagem")
st.caption(
    "O usuário compara uma ZP por vez, em pares. O sistema reaproveita julgamentos "
    "anteriores, infere relações transitivas e registra empates, conforme o script MATLAB."
)

tab_compare, tab_data, tab_history = st.tabs(
    ["Comparação par a par", "Dados operacionais", "Histórico e ranking"]
)

with tab_compare:
    st.subheader("Escolha a ZP preferida em cada par")
    st.write(
        "Em cada etapa, serão apresentadas duas zonas. Escolha a que considera "
        "globalmente melhor ou marque empate. A próxima comparação será definida "
        "pelo merge sort, aproveitando relações já conhecidas."
    )
    ranking, pending = compute_ranking()
    if pending is None:
        state["ranking"] = ranking.to_dict(orient="records")
        save_state()
        st.success("Ranking concluído com base nos julgamentos registrados.")
        st.dataframe(ranking, use_container_width=True, hide_index=True)
        st.download_button(
            "Baixar ranking em CSV",
            ranking.to_csv(index=False).encode("utf-8-sig"),
            file_name="Ranking_ZP.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        a, b = pending.a, pending.b
        st.progress(min(len(state["history"]) / 40, 1.0))
        st.caption(
            f"Julgamentos diretos registrados: {len(state['history'])}. "
            "O máximo teórico de comparações do merge sort para 20 alternativas é  h ≈ n⌈log₂n⌉ − 2⌈log₂n⌉ + 1 = 67."
        )
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown("#### ZP A")
            st.markdown(f"### {ids[a]}")
            st.write(nomes[a])
            st.metric("Lotação informada", f"{lotacao_data.get(ids[a], 'N/D')} práticos")
        with right:
            st.markdown("#### ZP B")
            st.markdown(f"### {ids[b]}")
            st.write(nomes[b])
            st.metric("Lotação informada", f"{lotacao_data.get(ids[b], 'N/D')} práticos")

        st.markdown("**Qual das duas ZPs é globalmente melhor para você?**")
        c1, c2, c3 = st.columns(3)
        if c1.button(f"Escolher {ids[a]}", type="primary", use_container_width=True):
            state["history"].append({"a": a, "b": b, "result": 1})
            state["ranking"] = None
            save_state()
            st.rerun()
        if c2.button(f"Escolher {ids[b]}", use_container_width=True):
            state["history"].append({"a": a, "b": b, "result": 2})
            state["ranking"] = None
            save_state()
            st.rerun()
        if c3.button("Empate", use_container_width=True):
            state["history"].append({"a": a, "b": b, "result": 0})
            state["ranking"] = None
            save_state()
            st.rerun()

        with st.expander("O que significa 'globalmente melhor'?"):
            st.write(
                "Considere o conjunto de fatores que mais importa para sua decisão, "
                "como lotação, volume de fainas, qualidade de vida, custo de vida e "
                "acessibilidade. Os indicadores informativos aparecem no site, mas "
                "a escolha do par é feita pelo usuário."
            )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Desfazer último julgamento", use_container_width=True,
                     disabled=(len(state["history"]) == 0)):
            state["history"].pop()
            state["ranking"] = None
            save_state()
            st.rerun()
    with col_b:
        if st.button("Reiniciar ranking", use_container_width=True):
            state.clear()
            state.update(blank_state())
            save_state()
            st.rerun()

with tab_data:
    st.subheader("Lotação e histórico de fainas")
    year = st.selectbox("Ano", years, index=len(years)-1, key="year_data")
    fyear = long_fainas[long_fainas["Ano"] == year]
    merged = zones.merge(
        fyear.groupby("ZP", as_index=False)["Fainas"].sum(), on="ZP", how="left"
    )
    merged["Fainas por prático (indicativo)"] = (
        merged["Fainas"] / merged["Lotação"]
    ).round(1)
    st.dataframe(merged, use_container_width=True, hide_index=True)
    st.caption(
        "A razão fainas/prático é apenas indicativa. A imagem apresenta linhas "
        "históricas separadas para Sergipe e Ilhéus; as séries foram preservadas "
        "separadamente e não somadas automaticamente às ZPs atuais."
    )
    selected = st.multiselect(
        "Séries históricas para visualizar",
        options=fainas["Série histórica"].tolist(),
        default=["Rio de Janeiro", "São Paulo"],
    )
    if selected:
        chart_data = long_fainas[long_fainas["Série histórica"].isin(selected)]
        fig = px.line(
            chart_data, x="Ano", y="Fainas", color="Série histórica",
            markers=True, title="Fainas por série histórica (2017–2025)"
        )
        st.plotly_chart(fig, use_container_width=True)

with tab_history:
    st.subheader("Julgamentos registrados")
    if state["history"]:
        hist_rows = []
        for i, h in enumerate(state["history"], 1):
            result = "Empate" if h["result"] == 0 else (
                f"{ids[h['a']]} melhor" if h["result"] == 1 else f"{ids[h['b']]} melhor"
            )
            hist_rows.append({
                "Nº": i,
                "ZP A": ids[h["a"]],
                "Alternativa A": nomes[h["a"]],
                "ZP B": ids[h["b"]],
                "Alternativa B": nomes[h["b"]],
                "Resultado": result,
            })
        hist_df = pd.DataFrame(hist_rows)
        st.dataframe(hist_df, use_container_width=True, hide_index=True)
        st.download_button(
            "Baixar julgamentos em CSV",
            hist_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="Julgamentos_ZP.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.info("Nenhum julgamento foi registrado ainda.")
    if state.get("ranking"):
        st.subheader("Último ranking calculado")
        st.dataframe(pd.DataFrame(state["ranking"]), use_container_width=True, hide_index=True)

st.divider()
st.subheader("Indicadores complementares — próxima etapa")
st.info(
    "IDHM, custo de vida, aeroportos, distâncias e tempos de deslocamento ainda "
    "precisam ser preenchidos com dados verificados e fontes/anos registrados. "
    "A estrutura foi mantida separada para não apresentar números inventados."
)
