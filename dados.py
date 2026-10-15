"""Carga e cálculo dos indicadores (sem Streamlit)."""
import math
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
ND = "Não disponível"

# Indicadores previstos e ainda NÃO coletados (aparecem como indisponíveis na interface)
NAO_COLETADOS = [
    "Renda per capita", "PIB per capita", "Custo de vida", "Segurança pública",
    "Hospitais e serviços de saúde", "Educação", "Mobilidade urbana", "Clima e condições ambientais",
    "Distância e tempo por estrada até o aeroporto", "Conectividade aérea (rotas e frequência)",
    "Distância até a capital/centro de referência", "Número de práticos (dado oficial atualizado)",
    "Tipos de navios e complexidade operacional", "Infraestrutura portuária",
]


def _read(name, **kw):
    return pd.read_csv(ROOT / name, encoding="utf-8-sig", **kw)


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def load_all():
    zonas = _read("dados_zp.csv", dtype=str).fillna("")
    zonas["Lotacao_praticos"] = pd.to_numeric(zonas["Lotacao_praticos"], errors="coerce")
    ind = _read("indicadores.csv", dtype={"ZP": str}).fillna("")
    ref = _read("referencias_geograficas.csv", dtype={"ZP": str}).fillna("")
    fain = _read("fainas_historicas.csv", dtype={"ZP_serie": str})
    fain["Ano"] = pd.to_numeric(fain["Ano"], errors="coerce").astype("Int64")
    fain["Fainas"] = pd.to_numeric(fain["Fainas"], errors="coerce")
    fontes = _read("fontes.csv").fillna("")
    return zonas, ind, ref, fain, fontes


def distancia_aeroporto(ref_row):
    try:
        return round(haversine_km(float(ref_row["Lat"]), float(ref_row["Lon"]),
                                  float(ref_row["Aero_lat"]), float(ref_row["Aero_lon"])), 1)
    except (ValueError, TypeError, KeyError):
        return None


def fainas_metricas(serie, total_por_ano=None):
    """serie: DataFrame com Ano e Fainas de UMA série. Retorna dict de métricas ou None."""
    s = serie.dropna(subset=["Fainas"]).sort_values("Ano")
    if s.empty:
        return None
    anos = s["Ano"].astype(int).to_numpy()
    v = s["Fainas"].astype(float).to_numpy()
    media = float(v.mean())
    var = None if v[0] == 0 else (v[-1] / v[0] - 1) * 100
    slope = float(np.polyfit(anos, v, 1)[0]) if len(v) >= 3 else None
    tend_pct = None if (slope is None or media == 0) else slope / media * 100
    if tend_pct is None:
        tend = ND
    elif tend_pct > 1:
        tend = "crescimento"
    elif tend_pct < -1:
        tend = "redução"
    else:
        tend = "estável"
    cv = None if (media == 0 or len(v) < 2) else float(v.std(ddof=1) / media * 100)
    part = None
    if total_por_ano is not None and anos[-1] in total_por_ano and total_por_ano[anos[-1]] > 0:
        part = v[-1] / total_por_ano[anos[-1]] * 100
    return {
        "ano_ini": int(anos[0]), "ano_fim": int(anos[-1]), "ultimo": int(v[-1]),
        "media": media, "variacao_pct": var, "tendencia": tend, "tendencia_pct_ano": tend_pct,
        "volatilidade_cv_pct": cv,
        "ano_max": int(anos[v.argmax()]), "max": int(v.max()),
        "ano_min": int(anos[v.argmin()]), "min": int(v.min()),
        "participacao_ultimo_ano_pct": part,
    }


def perfil(zp, zonas, ind, ref, fain):
    """Dicionário com tudo que a interface mostra de uma ZP."""
    z = zonas[zonas.ZP == zp].iloc[0]
    r = ref[ref.ZP == zp]
    r = r.iloc[0] if len(r) else None
    totais = fain.groupby("Ano")["Fainas"].sum().to_dict()
    serie = fain[fain.ZP_serie == zp]
    out = {
        "zp": zp, "abrangencia": z["Abrangencia"], "uf": z["UF"],
        "lotacao": None if pd.isna(z["Lotacao_praticos"]) else int(z["Lotacao_praticos"]),
        "fainas": fainas_metricas(serie, totais), "serie": serie.sort_values("Ano"),
        "indicadores": ind[ind.ZP == zp], "municipio_ref": ND, "aeroporto": ND,
        "dist_aeroporto_km": None, "voos": ND, "obs_geo": "",
    }
    if r is not None:
        out["municipio_ref"] = r["Municipio_referencia"] or ND
        out["aeroporto"] = (f"{r['Aeroporto']} ({r['IATA']})" if r["Aeroporto"] else ND)
        out["dist_aeroporto_km"] = distancia_aeroporto(r)
        out["voos"] = r["Voos_comerciais"] or ND
        out["obs_geo"] = r["Observacao"]
    return out


def valor_indicador(p, nome, principal=True):
    """Retorna (texto, linha) do indicador `nome`; texto = ND se ausente."""
    df = p["indicadores"]
    df = df[df.Indicador == nome]
    if principal and len(df[df.Principal == 1]):
        df = df[df.Principal == 1]
    if df.empty:
        return ND, None
    row = df.iloc[0]
    v = row["Valor"]
    if nome == "IDHM":
        txt = f"{float(v):.3f} ({int(row['Ano_ref'])}, {row['Municipio']})"
    elif nome == "População":
        txt = f"{int(float(v)):,}".replace(",", ".") + f" ({int(row['Ano_ref'])}, {row['Municipio']})"
    else:
        txt = str(v)
    return txt, row


def fmt_int(x):
    return ND if x is None else f"{int(x):,}".replace(",", ".")
