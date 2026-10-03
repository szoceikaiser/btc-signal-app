"""Bounded historical V035 short accounting probe; not a strategy backtest.

Uses the first chronological V035 SHORT_1 and its next full short exit from
the preserved retrospective signal tape. The tape has no execution feedback.
Fills are hypothetical next-open PF_XBTUSD orders; mark/funding are public
Kraken history. Never interpret this as a full V035 return or real fills.
"""
import gzip
import hashlib
import json
import sys
from datetime import datetime, timezone
from decimal import Decimal as D, ROUND_DOWN
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
from backtest import run_backtest
from derivative_accounting import PERP, replay
from strategy_core import Candle, FlowPoint

DOC = ROOT / "docs" / "audit-nacharbeit-2026-10"
SRC = DOC / "A7-V035-sources"
STEP = 14_400_000
HOUR = 3_600_000
FEE = D("0.001")  # Existing S0 model fee, not an asserted Kraken fee tier.


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def array(name):
    path = SRC / name
    return json.loads(gzip.decompress(path.read_bytes()))


def ms(text):
    return int(datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp() * 1000)


def main():
    manifest = read(SRC / "manifest.json")
    prices = {}
    for name, spec in manifest["series"].items():
        path = SRC / spec["file"]
        assert digest(path) == spec["sha256"]
        rows = array(spec["file"])
        assert len(rows) == spec["count"]
        prices[name] = {int(c["time"]): c for c in rows}
    start, end = manifest["active_start_ms"], manifest["r1_cutoff_ms"]
    for name, step, first in (("trade-4h", STEP, start),
                              ("mark-1h", HOUR, start-HOUR),
                              ("spot-1h", HOUR, start-HOUR)):
        assert list(prices[name]) == list(range(first, end+1, step))
    funding_path = ROOT / "docs/nach-6/r1-raw/funding.json"
    funding_raw = json.loads(funding_path.read_text(encoding="utf-8"), parse_float=D)
    rates = {ms(row["timestamp"]): row for row in funding_raw["rates"]}
    missing = [ts for ts in range(start, end+1, HOUR) if ts not in rates]
    assert missing == [1770206400000, 1771005600000, 1778306400000], missing

    flow_path = DOC / "A7-flow-modeled-v2.json.gz"
    data = json.loads(gzip.decompress(flow_path.read_bytes()))
    design_path = DOC / "A7-analysemanifest-v1.json"
    row = next(r for r in read(design_path)["rows"] if r["id"] == "V035")
    cfg = dict(row["params"], muster_cvd="usd")
    signals = run_backtest([Candle(**c) for c in data["candles"]],
                           [FlowPoint(**f) for f in data["flow"]], cfg,
                           start_ms=start)
    first = next(s for s in signals if s["type"] == "SHORT_1")
    stop_types = {"SHORT_COVER_REST", "SHORT_STOPLOSS"}
    close = next(s for s in signals if s["ts"] > first["ts"] and s["type"] in stop_types)
    entry_at, exit_at = first["ts"]+STEP, close["ts"]+STEP
    assert entry_at < exit_at and exit_at < missing[0]
    entry = D(prices["trade-4h"][entry_at]["open"])
    exit_price = D(prices["trade-4h"][exit_at]["open"])
    capital = D("10000")
    initial_fraction = D(first["tranche_pct"]) / 100
    qty = ((capital*initial_fraction)/(entry*(1+FEE))).quantize(
        D("0.0001"), rounding=ROUND_DOWN)
    assert qty > 0
    marks = {t: D(prices["mark-1h"][t-HOUR]["close"])
             for t in range(entry_at, exit_at+1, HOUR)}
    settlements = []
    absolute_sum = D(0)
    for t in range(entry_at+HOUR, exit_at+1, HOUR):
        # Kraken sets the rate at the beginning of the next funding period;
        # that period accrues continuously and settles at its END (t).
        # Our fills occur at exact hour boundaries, so each full held hour
        # receives the rate published at its start.
        rate = rates.get(t-HOUR)
        if rate is None:
            raise ValueError(f"Missing funding for held interval ending {t}")
        absolute = rate["fundingRate"]
        absolute_sum += absolute
        # A5 book multiplies mark*rate. This effective rate encodes the
        # exchange's published absolute USD/BTC payment, not a new estimate.
        settlements.append({"ts": t, "rate": absolute/marks[t],
                            "source": "Kraken PF_XBTUSD published absolute USD/BTC rate set at interval start"})
    fills = [{"id": "v035:first-short:open", "ts": entry_at, "action": "open",
              "lot": "first-short", "side": "short", "qty": qty, "price": entry},
             {"id": "v035:first-short:close", "ts": exit_at, "action": "close",
              "lot": "first-short", "side": "short", "qty": qty, "price": exit_price}]
    result = replay(fills, marks, instrument=PERP, start_ms=entry_at,
                    end_ms=exit_at, capital=capital, fee=FEE,
                    calendar={"interval_ms": HOUR, "offset_ms": 0},
                    funding=settlements)
    independent = (capital + qty*(entry-exit_price)
                   - qty*(entry+exit_price)*FEE + qty*absolute_sum)
    difference = result["end"]["equity"] - independent
    assert abs(difference) < D("0.000000001"), difference
    assert not result["end"]["lots"] and result["end"]["margin"] == 0
    assert len([e for e in result["ledger"] if e["kind"] == "funding"]) == len(settlements)
    output = {
        "schema": "a7-v035-first-short-accounting-probe-v1",
        "scope": "First retrospective V035 SHORT_1 to next full exit; hypothetical next-open PF_XBTUSD fills. No closed-loop V035 strategy or full-window return.",
        "original_params_sha256": row["params_sha256_canonical"],
        "source_manifest_sha256": digest(SRC / "manifest.json"),
        "funding_raw_sha256": digest(funding_path),
        "flow_sha256": digest(flow_path),
        "signal_tape": "legacy_retrospective_no_execution_feedback",
        "first_signal": {"ts": first["ts"], "type": first["type"],
                         "tranche_pct": first["tranche_pct"]},
        "full_exit_signal": {"ts": close["ts"], "type": close["type"]},
        "open_at_ms": entry_at, "close_at_ms": exit_at,
        "open_trade_price": str(entry), "close_trade_price": str(exit_price),
        "quantity_btc": str(qty), "fee_fraction": str(FEE),
        "funding_payments": len(settlements),
        "funding_rate_alignment": "rate timestamp is interval start; settlement timestamp is next full UTC hour",
        "funding_usd": str(result["funding"]),
        "fees_usd": str(result["fees"]),
        "end_equity_usd": str(result["end"]["equity"]),
        "independent_end_equity_usd": str(independent),
        "independent_difference_usd": str(difference),
        "max_gross_to_equity": str(max(e["after"]["gross"]/e["after"]["equity"]
                                        for e in result["ledger"])),
        "missing_full_window_funding_ms": missing,
        "full_v035_historical_return_valid": False,
        "historical_api_as_of_proven": False,
        "real_fills_proven": False,
    }
    dest = SRC / "first-short-probe-v1.json"
    raw = (json.dumps(output, indent=2, ensure_ascii=False) + "\n").encode()
    if dest.exists():
        assert dest.read_bytes() == raw
    else:
        dest.write_bytes(raw)
    print("V035 first short accounting PASS", entry_at, exit_at,
          "funding", len(settlements), "equity", result["end"]["equity"])


if __name__ == "__main__":
    main()
