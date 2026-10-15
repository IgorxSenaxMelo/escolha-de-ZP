# app.py
# Comparador de Zonas de Praticagem (ZP) — protótipo Streamlit
# Execute com: streamlit run app.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Comparador de ZP", page_icon="⚓", layout="wide")

st.title("⚓ Comparador de Zonas de Praticagem")
st.caption("Comparação operacional, socioeconômica e de acessibilidade entre ZPs.")

# Lotação transcrita da imagem fornecida pelo usuário.
# ZP 11 e ZP 13 não aparecem na tabela atual apresentada.
lotacao = [
    ("ZP01", "Fazendinha (AP) – Itacoatiara (AM)", 160),
    ("ZP02", "Itacoatiara – Tabatinga (AM)", 35),
    ("ZP03", "Belém e Vila do Conde (PA)", 36),
    ("ZP04", "Itaqui, Alumar e Ponta da Madeira (MA)", 33),
    ("ZP05", "Fortaleza e Pecém (CE)", 13),
    ("ZP06", "Areia Branca (RN)", 3),
    ("ZP07", "Natal (RN)", 4),
    ("ZP08", "Cabedelo (PB)", 4),
    ("ZP09", "Recife e Suape (PE)", 14),
    ("ZP10", "Maceió e terminais de AL/SE", 5),
    ("ZP12", "Salvador e Baía de Todos os Santos (BA)", 27),
    ("ZP14", "Vitória, Tubarão, Praia Mole e Ubu (ES)", 28),
    ("ZP15", "Rio de Janeiro, Niterói, Sepetiba e Angra (RJ)", 65),
    ("ZP16", "Santos, Baixada Santista e São Sebastião (SP)", 58),
    ("ZP17", "Paranaguá e Antonina (PR)", 30),
    ("ZP18", "São Francisco do Sul e Itapoá (SC)", 17),
    ("ZP19", "Rio Grande (RS)", 22),
    ("ZP20", "Lagoa dos Patos e terminais interiores (RS)", 5),
    ("ZP21", "Itajaí e Navegantes (SC)", 13),
    ("ZP22", "Imbituba (SC)", 5),
]
zones = pd.DataFrame(lotacao, columns=["ZP", "Abrangência", "Lotação"])

# Fainas transcritas visualmente da imagem enviada (2017–2025).
# Atenção: os dados históricos são apresentados pelas localidades/linhas da imagem,
# e não devem ser somados automaticamente quando a abrangência da ZP mudou.
years = list(range(2017, 2026))
fainas_rows = [
    ("ZP01", "Amapá / Fazendinha", [2657,2603,2664,2809,2744,2923,3327,3048,3042]),
    ("ZP02", "Amazonas / Itacoatiara–Tabatinga", [1560,1587,1545,1431,1329,1510,1322,1208,1227]),
    ("ZP03", "Pará / Belém e Vila do Conde", [3434,4713,3521,3702,3801,4470,4684,4388,4499]),
    ("ZP04", "Maranhão", [3792,3962,3919,4003,4067,3976,4014,3971,3967]),
    ("ZP05", "Ceará", [2270,2391,2545,2443,2717,2356,2379,2606,2551]),
    ("ZP06", "Areia Branca", [155,189,165,136,148,146,130,136,127]),
    ("ZP07", "Natal", [250,213,210,177,127,164,152,150,136]),
    ("ZP08", "Paraíba / Cabedelo", [232,198,178,177,200,204,197,210,184]),
    ("ZP09", "Pernambuco / Recife e Suape", [3611,3277,3342,3371,3276,3423,3562,3834,3666]),
    ("ZP10", "Alagoas", [551,633,572,445,559,733,769,796,833]),
    ("ZP10-H", "Sergipe (série histórica separada)", [135,79,85,81,138,7,0,0,0]),
    ("ZP12", "Salvador", [4220,4272,4524,4558,4429,3986,4271,4359,4032]),
    ("ZP12-H", "Ilhéus (série histórica separada)", [78,88,32,0,0,0,0,0,0]),
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
fainas = pd.DataFrame(
    [{"ZP": zp, "Série histórica": nome, **dict(zip(years, vals))}
     for zp, nome, vals in fainas_rows]
)
long_fainas = fainas.melt(
    id_vars=["ZP", "Série histórica"], value_vars=years,
    var_name="Ano", value_name="Fainas"
)
long_fainas["Ano"] = long_fainas["Ano"].astype(int)

# Campos socioeconômicos deliberadamente sem valores fictícios.
# Preencha este arquivo CSV com dados verificados e ano/fonte.
try:
    cidades = pd.read_csv("indicadores_cidades.csv")
except FileNotFoundError:
    cidades = pd.DataFrame(columns=[
        "ZP", "Cidade", "IDHM", "Ano_IDHM",
        "Custo_mensal_estimado_R$", "Ano_custo",
        "Aeroporto", "Distancia_aeroporto_km",
        "Tempo_aeroporto_min", "Fonte", "Observacoes"
    ])

st.sidebar.header("Filtros")
zp_options = zones["ZP"].tolist()
zp_a = st.sidebar.selectbox(
    "Zona A", zp_options, index=zp_options.index("ZP15")
)
zp_b_default = zp_options.index("ZP16") if "ZP16" in zp_options else 0
zp_b = st.sidebar.selectbox("Zona B", zp_options, index=zp_b_default)
ano = st.sidebar.selectbox("Ano das fainas", years, index=len(years)-1)
mostrar_historico = st.sidebar.checkbox("Mostrar histórico completo", value=True)

if zp_a == zp_b:
    st.warning("Selecione duas ZPs diferentes para comparar.")
else:
    a = zones.loc[zones.ZP == zp_a].iloc[0]
    b = zones.loc[zones.ZP == zp_b].iloc[0]
    fa = long_fainas[(long_fainas.ZP == zp_a) & (long_fainas.Ano == ano)]["Fainas"].sum()
    fb = long_fainas[(long_fainas.ZP == zp_b) & (long_fainas.Ano == ano)]["Fainas"].sum()

    st.subheader("Resumo comparativo")
    c1, c2, c3 = st.columns(3)
    c1.metric(f"Lotação — {zp_a}", f"{int(a.Lotação)} práticos")
    c2.metric(f"Lotação — {zp_b}", f"{int(b.Lotação)} práticos")
    diff = int(a.Lotação) - int(b.Lotação)
    c3.metric("Diferença de lotação (A − B)", f"{diff:+d}")

    c4, c5, c6 = st.columns(3)
    c4.metric(f"Fainas {ano} — {zp_a}", f"{int(fa):,}".replace(",", "."))
    c5.metric(f"Fainas {ano} — {zp_b}", f"{int(fb):,}".replace(",", "."))
    c6.metric("Fainas por prático (indicativo)", 
              f"{fa/a.Lotação:.1f} vs. {fb/b.Lotação:.1f}")

    comp = pd.DataFrame({
        "Indicador": ["Lotação", f"Fainas em {ano}", "Fainas/prático (indicativo)"],
        zp_a: [int(a.Lotação), int(fa), round(fa/a.Lotação, 1)],
        zp_b: [int(b.Lotação), int(fb), round(fb/b.Lotação, 1)],
    })
    st.dataframe(comp, use_container_width=True, hide_index=True)

    st.caption(
        "Fainas/prático é uma razão indicativa: não considera duração, complexidade, "
        "escala, férias, afastamentos ou mudanças na abrangência histórica."
    )

    st.subheader("Histórico de fainas")
    hist = long_fainas[long_fainas.ZP.isin([zp_a, zp_b])]
    if not mostrar_historico:
        hist = hist[hist.Ano == ano]
    fig = px.line(
        hist, x="Ano", y="Fainas", color="Série histórica", markers=True,
        title=f"Fainas por série histórica: {zp_a} × {zp_b}"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Qualidade de vida e acessibilidade")
    st.info(
        "IDHM, custo de vida e aeroporto ainda dependem de uma base validada. "
        "O protótipo não inventa valores: preencha indicadores_cidades.csv para "
        "exibir os dados confirmados."
    )
    if not cidades.empty:
        dados = cidades[cidades["ZP"].isin([zp_a, zp_b])]
        if not dados.empty:
            st.dataframe(dados, use_container_width=True, hide_index=True)
        else:
            st.caption("Ainda não há indicadores cadastrados para as ZPs selecionadas.")

st.divider()
st.subheader("Base de lotação")
st.dataframe(zones, use_container_width=True, hide_index=True)

with st.expander("Como adicionar IDHM, custo de vida e aeroportos"):
    st.markdown(
        """
        Edite `indicadores_cidades.csv`, usando uma linha por cidade relevante.
        Colunas esperadas:

        `ZP, Cidade, IDHM, Ano_IDHM, Custo_mensal_estimado_R$, Ano_custo, Aeroporto, Distancia_aeroporto_km, Tempo_aeroporto_min, Fonte, Observacoes`

        **Recomendações:** registrar o ano e a fonte de cada indicador; comparar cidades
        com a mesma cesta de despesas; medir distância/tempo por rota terrestre real;
        e não misturar indicadores municipais de anos diferentes sem sinalização.
        """
    )

st.caption(
    "Protótipo baseado nas imagens e no arquivo MATLAB fornecidos. "
    "Confirme os números transcritos com as planilhas/fontes originais antes de uso decisório."
)
