"""Comparador de Zonas de Praticagem (ZP) – interface Streamlit."""
import json
import time
import uuid
from io import BytesIO

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import dados
import ranking as rk
import storage

st.set_page_config(page_title="Comparador de Zonas de Praticagem", page_icon="⚓", layout="wide")
ND = dados.ND


# ----------------------------------------------------------------------------- dados
@st.cache_data
def carregar():
    return dados.load_all()


@st.cache_data
def carregar_config():
    with open(dados.ROOT / "config_zp.json", encoding="utf-8") as f:
        return json.load(f)


zonas, ind, ref, fain, fontes = carregar()
CFG = carregar_config()
ids = zonas["ZP"].tolist()
n = len(ids)
nome = dict(zip(zonas.ZP, zonas.Abrangencia))
PERFIS = {z: dados.perfil(z, zonas, ind, ref, fain) for z in ids}


def fnum(x, d=0):
    if x is None or pd.isna(x):
        return ND
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def rotulo_contexto(z):
    out = []
    if z in CFG["preferencia_historica"]["alta"]:
        out.append("Frequentemente preferida por usuários (informação preliminar)")
    if z in CFG["preferencia_historica"]["baixa"]:
        out.append("Percebida como menos desejável por alguns usuários (informação preliminar)")
    for g in CFG["grupos_contextuais"].values():
        if z in g["zps"]:
            out.append("Grupo de interesse associado a características militares")
    return out


# ----------------------------------------------------------------------------- sessão
def novo_estado():
    seed = uuid.uuid4().hex[:8]
    return {
        "history": [], "seed": seed, "session_id": uuid.uuid4().hex[:12], "started_at": None,
        "initial_order": rk.build_initial_order(
            ids, CFG.get("ordem_inicial", "prior"), CFG["preferencia_historica"], seed),
        "saved": {"key": None, "revisoes": 0, "status": None, "erro": None, "backend": None},
    }


if "zp" not in st.session_state:
    st.session_state["zp"] = novo_estado()
S = st.session_state["zp"]


@st.cache_resource
def backends():
    try:
        sec = dict(st.secrets)
    except Exception:
        sec = None
    return storage.get_backends(ids, sec)


def registrar(rows, forcar=False):
    sv = S["saved"]
    chave = rk.ranking_string(rows, ids) + json.dumps(S["history"])
    if sv["key"] == chave and not (forcar and sv["status"] == "falha"):
        return
    rec = storage.build_record(
        ids, rows, S["history"], S["session_id"], sv["revisoes"] + 1, S["started_at"],
        rk.ranking_string(rows, ids), CFG.get("ordem_inicial", "prior"))
    ok, nome_backend, erro = storage.save_record(rec, backends())
    sv.update(key=chave, status="ok" if ok else "falha", erro=erro, backend=nome_backend)
    if ok:
        sv["revisoes"] += 1


def responder(a, b, resultado):
    if S["started_at"] is None:
        S["started_at"] = time.time()
    S["history"].append({"a": a, "b": b, "result": resultado})
    st.rerun()


# ----------------------------------------------------------------------------- tabelas
def linhas_resumo(p):
    f = p["fainas"]
    idh, _ = dados.valor_indicador(p, "IDHM")
    pop, _ = dados.valor_indicador(p, "População")
    idh_n = None
    _, r = dados.valor_indicador(p, "IDHM")
    if r is not None:
        idh_n = float(r["Valor"])
    km = p["dist_aeroporto_km"]
    return [  # (rótulo, texto, valor numérico p/ diferença, casas)
        ("Abrangência", p["abrangencia"], None, 0),
        ("Município de referência dos indicadores", p["municipio_ref"], None, 0),
        ("IDHM (ano de referência e município)", idh, idh_n, 3),
        ("População (Censo 2022)", pop, None, 0),
        ("Aeroporto comercial mais próximo", p["aeroporto"], None, 0),
        ("Distância até o aeroporto (linha reta, estimada)",
         ND if km is None else f"≈ {fnum(km, 0)} km", km, 0),
        ("Voos comerciais regulares", p["voos"], None, 0),
        ("Práticos (lotação informada)", ND if p["lotacao"] is None else str(p["lotacao"]),
         p["lotacao"], 0),
        ("Fainas por ano (média 2017–2025)", ND if not f else fnum(f["media"]), f and f["media"], 0),
        ("Fainas no último ano da série", ND if not f else fnum(f["ultimo"]), f and f["ultimo"], 0),
        ("Variação das fainas no período",
         ND if not f or f["variacao_pct"] is None else f"{f['variacao_pct']:+.1f}%".replace(".", ","),
         f and f["variacao_pct"], 1),
        ("Tendência das fainas", ND if not f else f["tendencia"], None, 0),
        ("Volatilidade das fainas (coef. de variação)",
         ND if not f or f["volatilidade_cv_pct"] is None else f"{fnum(f['volatilidade_cv_pct'], 1)}%",
         f and f["volatilidade_cv_pct"], 1),
    ]


def tabela_comparacao(za, zb):
    la, lb = linhas_resumo(PERFIS[za]), linhas_resumo(PERFIS[zb])
    rows = []
    for (lab, ta, na, d), (_, tb, nb, _) in zip(la, lb):
        dif = ""
        if na is not None and nb is not None and abs(na - nb) > 1e-9:
            maior = za if na > nb else zb
            dif = f"{maior} maior em {fnum(abs(na - nb), d)}"
        rows.append({"Indicador": lab, za: ta, zb: tb, "Diferença": dif})
    return pd.DataFrame(rows).set_index("Indicador")


def avisos_geo(z):
    obs = PERFIS[z]["obs_geo"]
    return f"**{z}:** {obs}" if obs else ""


def grafico_fainas(zs):
    fig = go.Figure()
    for z in zs:
        s = PERFIS[z]["serie"]
        if len(s):
            fig.add_trace(go.Scatter(x=s["Ano"], y=s["Fainas"], mode="lines+markers", name=z))
    fig.update_layout(title="Fainas por ano (série transcrita, 2017–2025)", xaxis_title="Ano",
                      yaxis_title="Fainas", height=340, margin=dict(l=10, r=10, t=50, b=10))
    return fig


def excel_bytes(frames):
    b = BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as w:
        for nome_aba, df in frames.items():
            df.to_excel(w, index=False, sheet_name=nome_aba[:31])
    return b.getvalue()


# ----------------------------------------------------------------------------- layout
st.title("⚓ Comparador de Zonas de Praticagem")
st.info(
    "Escolha, em cada par, a ZP que você prefere **para você**. O resultado é o *seu ranking de "
    "preferência*, não uma avaliação universal de qualidade. Os dados mostrados (IDHM, aeroporto, "
    "fainas…) servem para apoiar a escolha e **não alteram o ranking automaticamente**. "
    "Ao concluir, seu ranking é registrado **de forma anônima** (sem nome), com data e hora, para "
    "a pesquisa do criador deste sistema.")

with st.sidebar:
    st.header("Sua sessão")
    st.caption(f"Comparações respondidas: {len(S['history'])}")
    if any(isinstance(b, storage.SheetsBackend) for b in backends()):
        st.caption("Registro: Google Sheets ativo")
    else:
        st.caption("Registro: modo local (Google Sheets não configurado)")
    with st.expander("Salvar / retomar em outro dispositivo"):
        st.download_button("Baixar progresso (JSON)", json.dumps(S, ensure_ascii=False).encode("utf-8"),
                           "progresso_zp.json", "application/json")
        up = st.file_uploader("Carregar progresso", type=["json"])
        if up is not None and st.button("Restaurar progresso"):
            try:
                novo = json.load(up)
                rk.validate_history(novo["history"], n)
                if sorted(novo["initial_order"]) != list(range(n)):
                    raise ValueError("Ordem inicial inválida")
                base = novo_estado()
                base.update({k: novo[k] for k in ("history", "seed", "session_id", "started_at",
                                                  "initial_order") if k in novo})
                S.clear(); S.update(base)
                st.rerun()
            except Exception as e:  # noqa: BLE001
                st.error(f"Não foi possível restaurar: {e}")

abas = st.tabs(["Comparar ZPs", "Perfil das ZPs", "Comparação detalhada", "Ranking final",
                "Dados e fontes"])

rows, pendente = rk.compute_ranking(S["initial_order"], S["history"], n)

# ---- Aba 1
with abas[0]:
    if rows is None:
        maxc = rk.max_comparisons(n)
        st.progress(min(len(S["history"]) / maxc, 1.0),
                    text=f"{len(S['history'])} respondidas · no máximo {maxc}, em geral menos")
        a, b = pendente.a, pendente.b
        esq, dir_ = (b, a) if rk.flip_display(S["seed"], a, b) else (a, b)
        ze, zd = ids[esq], ids[dir_]
        st.subheader("Qual destas ZPs você prefere?")
        c1, c2 = st.columns(2, gap="large")
        for col, z, lado in ((c1, ze, "ZP A"), (c2, zd, "ZP B")):
            with col, st.container(border=True):
                st.caption(lado)
                st.markdown(f"### {z}")
                st.write(nome[z])
                if CFG.get("mostrar_rotulos_na_comparacao"):
                    for r in rotulo_contexto(z):
                        st.caption("ℹ️ " + r)
        st.table(tabela_comparacao(ze, zd))
        for z in (ze, zd):
            msg = avisos_geo(z)
            if msg:
                st.caption("⚠️ " + msg)
        st.caption("Distâncias são estimativas em linha reta (não por estrada). 'Não disponível' = "
                   "dado não coletado, não zero.")
        with st.expander("Ver histórico de fainas das duas ZPs"):
            st.plotly_chart(grafico_fainas([ze, zd]), use_container_width=True)
        k = len(S["history"])
        b1, b2, b3 = st.columns(3)
        if b1.button(f"Prefiro {ze}", type="primary", use_container_width=True, key=f"e{k}"):
            responder(a, b, 1 if esq == a else 2)
        if b2.button(f"Prefiro {zd}", type="primary", use_container_width=True, key=f"d{k}"):
            responder(a, b, 1 if dir_ == a else 2)
        if b3.button("Empate", use_container_width=True, key=f"t{k}"):
            responder(a, b, 0)
    else:
        registrar(rows)
        st.success("Você concluiu! Este é o seu ranking de preferência:")
        sv = S["saved"]
        if sv["status"] == "ok":
            st.caption("✅ Seu ranking foi registrado anonimamente. Obrigado por participar!")
        elif sv["status"] == "falha":
            st.warning("Não foi possível registrar seu ranking agora.")
            if st.button("Tentar registrar novamente"):
                registrar(rows, forcar=True)
                st.rerun()
        df = pd.DataFrame([{"Posição": r["posicao"], "ZP": ids[r["indice"]],
                            "Abrangência": nome[ids[r["indice"]]]} for r in rows])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Baixar meu ranking (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                           "meu_ranking_zp.csv", "text/csv")
    c1, c2 = st.columns(2)
    if c1.button("↩ Desfazer última resposta", disabled=not S["history"], use_container_width=True):
        S["history"].pop()
        st.rerun()
    if c2.button("Recomeçar do zero", use_container_width=True):
        S.clear(); S.update(novo_estado())
        st.rerun()

# ---- Aba 2
with abas[1]:
    z = st.selectbox("Selecione uma ZP", ids, format_func=lambda x: f"{x} — {nome[x]}", key="perfil_zp")
    p = PERFIS[z]
    st.markdown(f"### {z} — {nome[z]}")
    st.table(pd.DataFrame([{"Indicador": lab, "Valor": t} for lab, t, _, _ in linhas_resumo(p)])
             .set_index("Indicador"))
    if p["obs_geo"]:
        st.caption("⚠️ " + p["obs_geo"])
    st.markdown("**Indicadores com fonte, ano e município**")
    if len(p["indicadores"]):
        t = p["indicadores"][["Indicador", "Valor", "Unidade", "Municipio", "Ano_ref", "Qualidade",
                              "URL"]].copy()
        st.dataframe(t, hide_index=True, use_container_width=True,
                     column_config={"URL": st.column_config.LinkColumn("Fonte (URL)")})
    else:
        st.caption("Nenhum indicador socioeconômico confirmado para esta ZP.")
    with st.expander("Indicadores ainda não coletados (indisponíveis)"):
        st.write("; ".join(dados.NAO_COLETADOS))
    st.markdown("**Contexto subjetivo (não é dado objetivo nem entra no ranking)**")
    rot = rotulo_contexto(z)
    st.write("\n".join(f"- {r}" for r in rot) if rot else "- Sem informação contextual registrada.")
    st.markdown("**Restrições operacionais comprovadas:** nenhuma registrada na base atual.")
    if len(p["serie"]):
        st.plotly_chart(grafico_fainas([z]), use_container_width=True)
        f = p["fainas"]
        m = st.columns(4)
        m[0].metric("Média anual", fnum(f["media"]))
        m[1].metric("Variação no período", ND if f["variacao_pct"] is None else f"{f['variacao_pct']:+.1f}%")
        m[2].metric("Maior volume", f"{fnum(f['max'])} ({f['ano_max']})")
        m[3].metric("Menor volume", f"{fnum(f['min'])} ({f['ano_min']})")
        part = f["participacao_ultimo_ano_pct"]
        st.caption(f"Participação no total de fainas em {f['ano_fim']}: "
                   f"{ND if part is None else fnum(part, 1) + '%'} · tendência: {f['tendencia']}. "
                   "Fainas ≠ navios ≠ faturamento ≠ número de práticos.")
    extra = fain[fain.ZP_serie.str.startswith(z + "-")]
    if len(extra):
        st.caption("Existe série histórica separada associada a esta ZP: "
                   + ", ".join(sorted(set(extra.Nome_serie))))

# ---- Aba 3
with abas[2]:
    c1, c2 = st.columns(2)
    za = c1.selectbox("ZP A", ids, index=0, format_func=lambda x: f"{x} — {nome[x]}", key="det_a")
    zb = c2.selectbox("ZP B", ids, index=1, format_func=lambda x: f"{x} — {nome[x]}", key="det_b")
    if za == zb:
        st.warning("Selecione duas ZPs diferentes.")
    else:
        st.table(tabela_comparacao(za, zb))
        st.plotly_chart(grafico_fainas([za, zb]), use_container_width=True)

# ---- Aba 4
with abas[3]:
    st.caption("Ranking de preferência individual, obtido só das suas respostas. Empates dividem a "
               "mesma posição; não há outro critério de desempate. Grau de confiança não é "
               "calculado (não há método estatístico válido para uma única pessoa).")
    if rows is not None:
        st.dataframe(pd.DataFrame([{"Posição": r["posicao"], "ZP": ids[r["indice"]],
                                    "Abrangência": nome[ids[r["indice"]]]} for r in rows]),
                     hide_index=True, use_container_width=True)
    else:
        st.info("Responda todas as comparações na primeira aba para ver o ranking.")
    if S["history"]:
        h = pd.DataFrame([{"Nº": i, "ZP A": ids[x["a"]], "ZP B": ids[x["b"]],
                           "Resultado": "Empate" if x["result"] == 0 else
                           f"{ids[x['a'] if x['result'] == 1 else x['b']]} preferida"}
                          for i, x in enumerate(S["history"], 1)])
        st.dataframe(h, hide_index=True, use_container_width=True)
        st.download_button("Baixar comparações (Excel)", excel_bytes({"comparacoes": h}),
                           "comparacoes_zp.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ---- Aba 5
with abas[4]:
    st.write("Campos 'Não disponível' = não coletado/confirmado (não é zero). A tabela de fainas é "
             "uma transcrição fornecida pelo criador e **não foi revalidada** contra fonte oficial.")
    st.subheader("Indicadores (valor, unidade, município, ano, fonte)")
    st.dataframe(ind, hide_index=True, use_container_width=True,
                 column_config={"URL": st.column_config.LinkColumn("URL")})
    st.subheader("Fontes")
    st.dataframe(fontes, hide_index=True, use_container_width=True,
                 column_config={"URL": st.column_config.LinkColumn("URL")})
    st.subheader("Ainda não coletados")
    st.write("; ".join(dados.NAO_COLETADOS))
    st.subheader("Série histórica de fainas")
    st.dataframe(fain, hide_index=True, use_container_width=True)
    st.download_button("Baixar tudo (Excel)", excel_bytes(
        {"zonas": zonas, "indicadores": ind, "referencias_geo": ref, "fainas": fain, "fontes": fontes}),
        "dados_zp.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.download_button("Baixar indicadores (CSV)", ind.to_csv(index=False).encode("utf-8-sig"),
                       "indicadores.csv", "text/csv")
