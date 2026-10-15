import csv
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import dados  # noqa: E402
import storage  # noqa: E402
import validacao  # noqa: E402


class TestDados(unittest.TestCase):
    def test_validacao_sem_erros(self):
        erros, _ = validacao.verificar()
        self.assertEqual(erros, [])

    def test_haversine_conhecido(self):
        self.assertAlmostEqual(dados.haversine_km(-22.9068, -43.1729, -23.5505, -46.6333), 357, delta=8)

    def test_metricas_fainas(self):
        import pandas as pd
        s = pd.DataFrame({"Ano": [2017, 2018, 2019, 2020], "Fainas": [100, 110, 120, 130]})
        m = dados.fainas_metricas(s, {2020: 1300})
        self.assertEqual(m["media"], 115)
        self.assertAlmostEqual(m["variacao_pct"], 30)
        self.assertEqual(m["tendencia"], "crescimento")
        self.assertEqual((m["ano_max"], m["ano_min"]), (2020, 2017))
        self.assertAlmostEqual(m["participacao_ultimo_ano_pct"], 10)

    def test_zero_nao_gera_divisao(self):
        import pandas as pd
        s = pd.DataFrame({"Ano": [2017, 2018, 2019], "Fainas": [0, 0, 0]})
        m = dados.fainas_metricas(s)
        self.assertIsNone(m["variacao_pct"])
        self.assertIsNone(m["volatilidade_cv_pct"])

    def test_perfil_todas_as_zps(self):
        zonas, ind, ref, fain, _ = dados.load_all()
        for z in zonas.ZP:
            self.assertIsNotNone(dados.perfil(z, zonas, ind, ref, fain)["fainas"])
        p20 = dados.perfil("ZP20", zonas, ind, ref, fain)
        self.assertIsNone(p20["dist_aeroporto_km"])
        self.assertEqual(dados.valor_indicador(p20, "IDHM")[0], dados.ND)
        p14 = dados.perfil("ZP14", zonas, ind, ref, fain)
        txt = dados.valor_indicador(p14, "IDHM")[0]
        self.assertIn("0.845", txt)
        self.assertIn("2010", txt)


class FakeWorksheet:
    def __init__(self):
        self.rows = []

    def row_values(self, i):
        return self.rows[0] if self.rows else []

    def append_row(self, values, value_input_option=None):
        self.rows.append(list(values))


class FakeSpreadsheet:
    def __init__(self):
        self.ws = FakeWorksheet()
        self.created = 0

    def worksheet(self, name):
        raise KeyError(name)

    def add_worksheet(self, name, rows, cols):
        self.created += 1
        return self.ws


class TestStorage(unittest.TestCase):
    ids = [f"ZP{i:02d}" for i in range(1, 6)]

    def _registro(self):
        hist = [{"a": 0, "b": 1, "result": 1}, {"a": 2, "b": 3, "result": 0}]
        rows = [{"posicao": i + 1, "indice": i} for i in range(5)]
        t = datetime(2026, 10, 15, 15, 0, tzinfo=timezone.utc)
        return storage.build_record(self.ids, rows, hist, "abc123", 1, t.timestamp() - 90,
                                    "ZP01 > ZP02", "prior", now=(t, t))

    def test_registro_sem_dados_pessoais(self):
        rec = self._registro()
        self.assertEqual(rec["n_comparacoes"], 2)
        self.assertEqual(rec["n_empates"], 1)
        self.assertEqual(rec["duracao_seg"], 90)
        self.assertEqual(rec["pos_ZP03"], 3)
        self.assertEqual(json.loads(rec["historico_json"])[0], ["ZP01", "ZP02", 1])
        self.assertFalse({"nome", "email", "ip", "user_agent"} & set(rec))

    def test_local_csv(self):
        with tempfile.TemporaryDirectory() as d:
            b = storage.LocalCsvBackend(self.ids, os.path.join(d, "r.csv"))
            ok, _, _ = storage.save_record(self._registro(), [b])
            storage.save_record(self._registro(), [b])
            self.assertTrue(ok)
            with open(os.path.join(d, "r.csv"), encoding="utf-8-sig") as f:
                linhas = list(csv.DictReader(f))
            self.assertEqual(len(linhas), 2)
            self.assertEqual(linhas[0]["sessao_id"], "abc123")

    def test_sheets_cria_aba_cabecalho_e_linha(self):
        sh = FakeSpreadsheet()
        b = storage.SheetsBackend(self.ids, sh)
        b.append(self._registro())
        b.append(self._registro())
        self.assertEqual(sh.created, 1)
        self.assertEqual(sh.ws.rows[0], storage.columns(self.ids))
        self.assertEqual(len(sh.ws.rows), 3)
        self.assertEqual(len(sh.ws.rows[1]), len(storage.columns(self.ids)))

    def test_fallback_quando_sheets_falha(self):
        class Quebrado:
            name = "Google Sheets"

            def append(self, rec):
                raise RuntimeError("sem rede")

        with tempfile.TemporaryDirectory() as d:
            local = storage.LocalCsvBackend(self.ids, os.path.join(d, "r.csv"))
            ok, nome, _ = storage.save_record(self._registro(), [Quebrado(), local])
            self.assertTrue(ok)
            self.assertIn("local", nome)
            ok2, _, erro = storage.save_record(self._registro(), [Quebrado()])
            self.assertFalse(ok2)
            self.assertIn("RuntimeError", erro)

    def test_get_backends_sem_secrets_usa_local(self):
        bs = storage.get_backends(self.ids, None)
        self.assertEqual(len(bs), 1)
        self.assertIsInstance(bs[0], storage.LocalCsvBackend)


if __name__ == "__main__":
    unittest.main()
