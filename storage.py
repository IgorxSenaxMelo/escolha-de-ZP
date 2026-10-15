"""Registro anônimo do ranking de cada respondente (Google Sheets ou CSV local).

- Sem nome/e-mail/IP: só data/hora, id aleatório de sessão e as respostas.
- Google Sheets: planilha PRIVADA do criador, acessada por conta de serviço
  (credenciais em st.secrets). Quem responde nunca vê a planilha.
- Se o Sheets não estiver configurado ou falhar, grava em respostas_local.csv
  (útil em teste local; em hospedagem efêmera o arquivo pode se perder).
"""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LOCAL_FILE = ROOT / "respostas_local.csv"
APP_VERSION = "2.0"
BASE_COLS = ["data_hora_brasilia", "data_hora_utc", "sessao_id", "revisao", "n_comparacoes",
             "n_empates", "duracao_seg", "ranking", "modo_ordem_inicial", "versao_app"]


def columns(ids):
    return BASE_COLS + [f"pos_{z}" for z in ids] + ["historico_json"]


def _now():
    utc = datetime.now(timezone.utc)
    try:
        from zoneinfo import ZoneInfo
        br = utc.astimezone(ZoneInfo("America/Sao_Paulo"))
    except Exception:  # sem tzdata: UTC-3 fixo (Brasil não usa horário de verão desde 2019)
        from datetime import timedelta
        br = utc.astimezone(timezone(timedelta(hours=-3)))
    return utc, br


def build_record(ids, rows, history, session_id, revisao, started_at_ts, ranking_txt, ordem_modo,
                 now=None):
    utc, br = now or _now()
    pos = {ids[r["indice"]]: r["posicao"] for r in rows}
    dur = None if started_at_ts is None else max(0, int(utc.timestamp() - started_at_ts))
    rec = {
        "data_hora_brasilia": br.strftime("%Y-%m-%d %H:%M:%S"),
        "data_hora_utc": utc.strftime("%Y-%m-%d %H:%M:%S"),
        "sessao_id": session_id, "revisao": revisao,
        "n_comparacoes": len(history), "n_empates": sum(1 for h in history if h["result"] == 0),
        "duracao_seg": dur, "ranking": ranking_txt, "modo_ordem_inicial": ordem_modo,
        "versao_app": APP_VERSION,
        "historico_json": json.dumps(
            [[ids[h["a"]], ids[h["b"]], h["result"]] for h in history], ensure_ascii=False),
    }
    for z in ids:
        rec[f"pos_{z}"] = pos.get(z, "")
    return rec


class LocalCsvBackend:
    name = "arquivo local (respostas_local.csv)"

    def __init__(self, ids, path=None):
        self.cols, self.path = columns(ids), Path(path or LOCAL_FILE)

    def append(self, rec):
        novo = not self.path.exists()
        with open(self.path, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=self.cols, extrasaction="ignore")
            if novo:
                w.writeheader()
            w.writerow(rec)


class SheetsBackend:
    name = "Google Sheets"

    def __init__(self, ids, worksheet, tab_name="respostas"):
        self.cols, self.ws_parent, self.tab = columns(ids), worksheet, tab_name
        self._ws = None

    @classmethod
    def from_secrets(cls, ids, secrets):
        import gspread  # importação tardia: só necessária se o Sheets estiver configurado
        creds = dict(secrets["gcp_service_account"])
        cfg = secrets["sheets"]
        gc = gspread.service_account_from_dict(creds)
        sh = gc.open_by_key(cfg["spreadsheet_id"]) if "spreadsheet_id" in cfg else gc.open_by_url(cfg["url"])
        return cls(ids, sh, cfg.get("aba", "respostas"))

    def _worksheet(self):
        if self._ws is None:
            try:
                ws = self.ws_parent.worksheet(self.tab)
            except Exception:
                ws = self.ws_parent.add_worksheet(self.tab, rows=1000, cols=len(self.cols))
            if not ws.row_values(1):
                ws.append_row(self.cols, value_input_option="RAW")
            self._ws = ws
        return self._ws

    def append(self, rec):
        self._worksheet().append_row([rec.get(c, "") for c in self.cols], value_input_option="RAW")


def get_backends(ids, secrets=None):
    """Retorna lista [principal, fallback]. O principal é o Sheets se houver credenciais."""
    out = []
    try:
        if secrets is not None and "gcp_service_account" in secrets and "sheets" in secrets:
            out.append(SheetsBackend.from_secrets(ids, secrets))
    except Exception:
        pass
    out.append(LocalCsvBackend(ids))
    return out


def save_record(rec, backends):
    """Tenta cada backend em ordem. Retorna (ok, nome_do_backend, erro_ou_None)."""
    erro = None
    for b in backends:
        try:
            b.append(rec)
            return True, b.name, erro
        except Exception as e:  # noqa: BLE001
            erro = f"{b.name}: {type(e).__name__}"
    return False, None, erro
