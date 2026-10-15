"""Verificações de consistência dos dados. Execute: python validacao.py"""
import sys
import dados


def verificar():
    zonas, ind, ref, fain, fontes = dados.load_all()
    erros, avisos = [], []
    ids = list(zonas.ZP)
    if len(ids) != 20 or len(set(ids)) != 20:
        erros.append(f"Esperadas 20 ZPs distintas, encontradas {len(set(ids))}")
    for z in ids:
        s = fain[fain.ZP_serie == z]
        if sorted(s.Ano.dropna().astype(int)) != list(range(2017, 2026)):
            erros.append(f"{z}: série de fainas não cobre 2017–2025 exatamente uma vez por ano")
        if (s.Fainas < 0).any():
            erros.append(f"{z}: fainas negativas")
    extras = set(fain.ZP_serie) - set(ids)
    if extras:
        avisos.append(f"Séries históricas separadas, fora do cadastro de 20 ZPs: {sorted(extras)}")
    if set(ref.ZP) != set(ids):
        erros.append("referencias_geograficas.csv não tem as mesmas ZPs do cadastro")
    ids_fonte = set(fontes.Fonte_id)
    for _, r in ind.iterrows():
        if r.Fonte_id not in ids_fonte:
            erros.append(f"Indicador {r.ZP}/{r.Indicador}: Fonte_id {r.Fonte_id} ausente em fontes.csv")
        if r.Indicador == "IDHM" and not (0 <= float(r.Valor) <= 1):
            erros.append(f"{r.ZP}: IDHM fora de 0–1")
        if not r.Ano_ref or not r.URL:
            erros.append(f"{r.ZP}/{r.Indicador}: sem ano ou URL de origem")
    for z in ids:
        if ind[(ind.ZP == z) & (ind.Indicador == "IDHM")].empty:
            avisos.append(f"{z}: IDHM não disponível")
    zeros = int((fain.Fainas == 0).sum())
    avisos.append(f"{zeros} valores zero na série de fainas (não confirmados como zero observado)")
    return erros, avisos


if __name__ == "__main__":
    e, a = verificar()
    for x in a:
        print("AVISO:", x)
    for x in e:
        print("ERRO:", x)
    print("OK" if not e else f"{len(e)} erro(s)")
    sys.exit(1 if e else 0)
