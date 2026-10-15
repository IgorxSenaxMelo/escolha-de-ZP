"""Teste de fumaça do app.py com um 'streamlit' simulado (o Streamlit real não está instalado
neste ambiente). Verifica que o fluxo principal executa sem exceções; NÃO substitui um teste
no navegador real (`streamlit run app.py`)."""
import contextlib
import importlib
import os
import sys
import types
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


class SS(dict):
    __getattr__ = dict.get

    def __setattr__(self, k, v):
        self[k] = v


def make_st(click=None):
    st = MagicMock(name="streamlit")
    st.session_state = SS()
    st.secrets = {}
    st.cache_data = lambda f=None, **k: (f if f else (lambda g: g))
    st.cache_resource = lambda f=None, **k: (f if f else (lambda g: g))
    st.tabs = lambda labels: [contextlib.nullcontext(MagicMock()) for _ in labels]
    def _cols(spec, **k):
        cs = [MagicMock() for _ in range(spec if isinstance(spec, int) else len(spec))]
        for c in cs:
            c.button = lambda label, **kw: bool(click and click(label))
            c.selectbox = lambda label, opts, index=0, **kw: opts[index]
        return cs
    st.columns = _cols
    st.container = lambda **k: contextlib.nullcontext()
    st.expander = lambda *a, **k: contextlib.nullcontext()
    st.sidebar = contextlib.nullcontext()
    st.selectbox = lambda label, opts, index=0, **k: opts[index]
    st.rerun = MagicMock(side_effect=RuntimeError("RERUN"))
    st.button = lambda label, **k: bool(click and click(label))
    st.file_uploader = lambda *a, **k: None
    return st


def run(click=None, state=None):
    st = make_st(click)
    if state:
        st.session_state["zp"] = state
    sys.modules["streamlit"] = st
    sys.modules.setdefault("plotly", MagicMock())
    sys.modules.setdefault("plotly.graph_objects", MagicMock())
    for m in ("app",):
        sys.modules.pop(m, None)
    try:
        importlib.import_module("app")
    except RuntimeError as e:
        if "RERUN" not in str(e):
            raise
    return st


if __name__ == "__main__":
    import ranking as rk
    import storage, tempfile

    storage.LOCAL_FILE = type(storage.LOCAL_FILE)(tempfile.mkdtemp()) / "r.csv"
    # 1) tela inicial
    st = run()
    S = st.session_state["zp"]
    assert S["history"] == [] and sorted(S["initial_order"]) == list(range(20))
    # 2) responder via clique no 1º botão "Prefiro ..."
    st = run(click=lambda l: l.startswith("Prefiro"))
    assert len(st.session_state["zp"]["history"]) == 1, st.session_state["zp"]["history"]
    # 3) responder tudo automaticamente até concluir, depois renderiza ranking e salva
    ids = [f"ZP{i:02d}" for i in (1,2,3,4,5,6,7,8,9,10,12,14,15,16,17,18,19,20,21,22)]
    score = {i: (i * 7) % 20 for i in range(20)}
    state = None
    for _ in range(80):
        st = run(click=lambda l: l.startswith("Prefiro"), state=state)
        state = st.session_state["zp"]
        rows, q = rk.compute_ranking(state["initial_order"], state["history"], 20)
        if rows is not None:
            break
    assert rows is not None, "não concluiu"
    st = run(state=state)  # render final: registra
    sv = st.session_state["zp"]["saved"]
    assert sv["status"] == "ok" and sv["revisoes"] == 1, sv
    st = run(state=st.session_state["zp"])  # re-render não duplica
    assert st.session_state["zp"]["saved"]["revisoes"] == 1
    import csv
    linhas = list(csv.DictReader(open(storage.LOCAL_FILE, encoding="utf-8-sig")))
    n_final = int(linhas[0]["n_comparacoes"])
    assert len(linhas) == 1 and n_final <= 69
    # 4) desfazer / recomeçar
    antes = len(st.session_state["zp"]["history"])
    st = run(click=lambda l: l.startswith("↩"), state=st.session_state["zp"])
    assert len(st.session_state["zp"]["history"]) == antes - 1
    st = run(click=lambda l: l.startswith("Recomeçar"), state=st.session_state["zp"])
    assert st.session_state["zp"]["history"] == []
    print("SMOKE OK:", n_final, "comparações até concluir; 1 linha registrada")
