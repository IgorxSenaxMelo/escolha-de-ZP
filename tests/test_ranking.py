import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import ranking as rk  # noqa: E402

N = 20
IDS = [f"ZP{i:02d}" for i in range(1, 21)]


def oracle(score):
    return lambda a, b: 0 if score[a] == score[b] else (1 if score[a] > score[b] else 2)


class TestRelacao(unittest.TestCase):
    def test_direta_e_inversa(self):
        h = [{"a": 0, "b": 1, "result": 1}]
        self.assertEqual(rk.relation(0, 1, h, 3), 1)
        self.assertEqual(rk.relation(1, 0, h, 3), 2)

    def test_transitividade(self):
        h = [{"a": 0, "b": 1, "result": 1}, {"a": 1, "b": 2, "result": 1}]
        self.assertEqual(rk.relation(0, 2, h, 3), 1)
        self.assertEqual(rk.relation(2, 0, h, 3), 2)

    def test_empate_e_transitividade_com_empate(self):
        h = [{"a": 0, "b": 1, "result": 0}, {"a": 1, "b": 2, "result": 1}]
        self.assertEqual(rk.relation(0, 1, h, 3), 0)
        self.assertEqual(rk.relation(0, 2, h, 3), 1)

    def test_desconhecida_pede_comparacao(self):
        with self.assertRaises(rk.NeedComparison):
            rk.merge_sort_interactive([0, 1], [], 2)

    def test_max_comparacoes_20(self):
        self.assertEqual(rk.max_comparisons(20), 69)  # limite citado no projeto anterior


class TestAlgoritmo(unittest.TestCase):
    def test_ordem_final_independe_da_ordem_inicial(self):
        rng = random.Random(1)
        score = list(range(N)); rng.shuffle(score)  # ordem verdadeira estrita
        esperado = sorted(range(N), key=lambda i: -score[i])
        for modo in ("cadastro", "aleatoria", "prior"):
            for seed in range(15):
                ini = rk.build_initial_order(
                    IDS, modo, {"alta": ["ZP14", "ZP15"], "baixa": ["ZP06"]}, seed)
                rows, hist = rk.run_with_oracle(ini, N, oracle(score))
                self.assertEqual([r["indice"] for r in rows], esperado, (modo, seed))
                self.assertLessEqual(len(hist), 69)
                self.assertEqual([r["posicao"] for r in rows], list(range(1, N + 1)))

    def test_nunca_repete_par_nem_pergunta_inferivel(self):
        rng = random.Random(7)
        score = list(range(N)); rng.shuffle(score)
        ini = list(range(N)); rng.shuffle(ini)
        _, hist = rk.run_with_oracle(ini, N, oracle(score))
        pares = [frozenset((h["a"], h["b"])) for h in hist]
        self.assertEqual(len(pares), len(set(pares)))
        for k, h in enumerate(hist):
            self.assertIsNone(rk.relation(h["a"], h["b"], hist[:k], N))

    def test_empates_compartilham_posicao(self):
        score = [i // 4 for i in range(N)]  # 5 classes de empate
        rows, _ = rk.run_with_oracle(list(range(N)), N, oracle(score))
        pos = {}
        for r in rows:
            pos.setdefault(r["posicao"], []).append(score[r["indice"]])
        self.assertEqual(len(pos), 5)
        for v in pos.values():
            self.assertEqual(len(set(v)), 1)
        self.assertEqual(sorted(pos), [1, 5, 9, 13, 17])

    def test_prior_correto_reduz_comparacoes(self):
        alta, baixa = ["ZP14", "ZP15", "ZP16", "ZP05", "ZP17"], ["ZP06", "ZP07", "ZP08"]
        base = [2 if z in alta else 0 if z in baixa else 1 for z in IDS]
        score = [s * 100 + (19 - i) for i, s in enumerate(base)]
        prior = {"alta": alta, "baixa": baixa}
        com = [len(rk.run_with_oracle(rk.build_initial_order(IDS, "prior", prior, s), N,
                                      oracle(score))[1]) for s in range(30)]
        sem = [len(rk.run_with_oracle(rk.build_initial_order(IDS, "aleatoria", prior, s), N,
                                      oracle(score))[1]) for s in range(30)]
        self.assertLess(sum(com) / 30, sum(sem) / 30)

    def test_usuario_inconsistente_termina(self):
        rng = random.Random(3)
        for _ in range(20):
            tabela = {}

            def juiz(a, b):
                k = (min(a, b), max(a, b))
                if k not in tabela:
                    tabela[k] = rng.choice([0, 1, 2])
                r = tabela[k]
                return r if a < b else (2 if r == 1 else 1 if r == 2 else 0)

            rows, hist = rk.run_with_oracle(list(range(N)), N, juiz)
            self.assertEqual(sorted(r["indice"] for r in rows), list(range(N)))
            self.assertLessEqual(len(hist), 69)

    def test_ordem_inicial_prior_agrupa(self):
        o = rk.build_initial_order(IDS, "prior", {"alta": ["ZP14", "ZP15"], "baixa": ["ZP06"]}, 5)
        self.assertEqual(sorted(o), list(range(N)))
        self.assertEqual({IDS[i] for i in o[:2]}, {"ZP14", "ZP15"})
        self.assertEqual(IDS[o[-1]], "ZP06")

    def test_flip_estavel_e_simetrico(self):
        self.assertEqual(rk.flip_display("x", 2, 5), rk.flip_display("x", 5, 2))
        self.assertEqual({rk.flip_display(str(s), 1, 2) for s in range(40)}, {True, False})

    def test_validate_history(self):
        rk.validate_history([{"a": 0, "b": 1, "result": 2}], 3)
        for ruim in ([{"a": 0, "b": 0, "result": 1}], [{"a": 0, "b": 9, "result": 1}],
                     [{"a": 0, "b": 1, "result": 3}], [{"a": 0}]):
            with self.assertRaises(ValueError):
                rk.validate_history(ruim, 3)

    def test_ranking_string(self):
        rows = [{"posicao": 1, "indice": 1}, {"posicao": 2, "indice": 0}, {"posicao": 2, "indice": 2}]
        self.assertEqual(rk.ranking_string(rows, ["A", "B", "C"]), "B > A = C")


if __name__ == "__main__":
    unittest.main()
