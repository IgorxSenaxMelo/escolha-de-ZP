"""Lógica pura de ordenação por comparações par a par (sem dependência do Streamlit).

Baseada no merge sort interativo do projeto anterior (que reproduz o script MATLAB):
- reaproveita julgamentos já dados (direto e invertido);
- infere por transitividade entre classes de empate;
- só pede uma comparação quando a relação não pode ser inferida.

Resultado de uma comparação: 1 = A melhor, 2 = B melhor, 0 = empate.
"""
import math
import random
from dataclasses import dataclass


@dataclass
class NeedComparison(Exception):
    a: int
    b: int


def _invert(r):
    return 2 if r == 1 else 1 if r == 2 else 0


def relation(a, b, history, n):
    """Relação entre a e b conhecida/inferida: 1, 2, 0 ou None (precisa perguntar)."""
    if a == b:
        return 0
    direct = {}
    for h in history:
        direct[(h["a"], h["b"])] = h["result"]
        direct[(h["b"], h["a"])] = _invert(h["result"])
    if (a, b) in direct:
        return direct[(a, b)]
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for h in history:
        if h["result"] == 0:
            ra, rb = find(h["a"]), find(h["b"])
            if ra != rb:
                parent[rb] = ra
    comp = [find(i) for i in range(n)]
    if comp[a] == comp[b]:
        return 0
    roots = sorted(set(comp))
    ri = {r: i for i, r in enumerate(roots)}
    g = [[False] * len(roots) for _ in roots]
    for h in history:
        x, y, r = h["a"], h["b"], h["result"]
        if r == 0:
            continue
        better, worse = (x, y) if r == 1 else (y, x)
        if comp[better] != comp[worse]:
            g[ri[comp[better]]][ri[comp[worse]]] = True
    for k in range(len(roots)):
        for i in range(len(roots)):
            if g[i][k]:
                for j in range(len(roots)):
                    g[i][j] = g[i][j] or g[k][j]
    ia, ib = ri[comp[a]], ri[comp[b]]
    ab, ba = g[ia][ib], g[ib][ia]
    if ab and not ba:
        return 1
    if ba and not ab:
        return 2
    return None


def merge_sort_interactive(items, history, n):
    if len(items) <= 1:
        return list(items)
    mid = len(items) // 2
    left = merge_sort_interactive(items[:mid], history, n)
    right = merge_sort_interactive(items[mid:], history, n)
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        rel = relation(left[i], right[j], history, n)
        if rel is None:
            raise NeedComparison(left[i], right[j])
        if rel == 1:
            out.append(left[i]); i += 1
        elif rel == 2:
            out.append(right[j]); j += 1
        else:
            out.extend([left[i], right[j]]); i += 1; j += 1
    return out + left[i:] + right[j:]


def max_comparisons(n):
    """Pior caso do merge sort: n*ceil(log2 n) - 2^ceil(log2 n) + 1 (n=20 -> 69)."""
    if n <= 1:
        return 0
    k = math.ceil(math.log2(n))
    return n * k - 2 ** k + 1


def tie_components(history, n):
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for h in history:
        if h["result"] == 0:
            ra, rb = find(h["a"]), find(h["b"])
            if ra != rb:
                parent[rb] = ra
    return [find(i) for i in range(n)]


def compute_ranking(initial_order, history, n):
    """Retorna (linhas, None) se concluído, ou (None, NeedComparison).
    Cada linha: {'posicao', 'indice'}; empatados compartilham a posição."""
    try:
        order = merge_sort_interactive(list(initial_order), history, n)
    except NeedComparison as q:
        return None, q
    comp = tie_components(history, n)
    first_pos, rows = {}, []
    for pos, i in enumerate(order, 1):
        first_pos.setdefault(comp[i], pos)
        rows.append({"posicao": first_pos[comp[i]], "indice": i})
    return rows, None


def build_initial_order(ids, mode, prior, seed):
    """Ordem inicial do merge sort.

    'cadastro' : ordem do cadastro (comportamento do projeto anterior);
    'aleatoria': embaralhada por sessão (análogo ao randperm do MATLAB);
    'prior'    : grupo de preferência histórica alta, depois neutras, depois baixa,
                 embaralhando dentro de cada grupo. Só altera QUAIS pares são
                 perguntados (e quantos); o ranking final vem só das respostas.
    """
    rng = random.Random(seed)
    idx = list(range(len(ids)))
    if mode == "cadastro":
        return idx
    if mode == "aleatoria":
        rng.shuffle(idx)
        return idx
    alta = [i for i in idx if ids[i] in set(prior.get("alta", []))]
    baixa = [i for i in idx if ids[i] in set(prior.get("baixa", []))]
    meio = [i for i in idx if i not in alta and i not in baixa]
    for g in (alta, meio, baixa):
        rng.shuffle(g)
    return alta + meio + baixa


def flip_display(seed, a, b):
    """Decide de forma estável (por sessão e par) se A/B aparecem trocados na tela,
    para diluir viés de posição. Não altera o resultado, só a apresentação."""
    return random.Random(f"{seed}:{min(a, b)}:{max(a, b)}").random() < 0.5


def validate_history(history, n):
    for h in history:
        if not (isinstance(h, dict) and {"a", "b", "result"} <= set(h)):
            raise ValueError("Julgamento mal formado")
        if h["a"] not in range(n) or h["b"] not in range(n) or h["a"] == h["b"]:
            raise ValueError("Julgamento fora dos limites")
        if h["result"] not in (0, 1, 2):
            raise ValueError("Resultado de julgamento inválido")


def run_with_oracle(initial_order, n, judge):
    """Executa o algoritmo respondendo com judge(a,b)->0/1/2. Retorna (linhas, historico)."""
    history = []
    while True:
        rows, q = compute_ranking(initial_order, history, n)
        if rows is not None:
            return rows, history
        history.append({"a": q.a, "b": q.b, "result": judge(q.a, q.b)})


def ranking_string(rows, ids):
    """Ex.: 'ZP15 > ZP16 = ZP14 > ZP05' (empatados unidos por '=')."""
    out, last = [], None
    for r in rows:
        z = ids[r["indice"]]
        if not out:
            out.append(z)
        else:
            out.append((" = " if r["posicao"] == last else " > ") + z)
        last = r["posicao"]
    return "".join(out)
