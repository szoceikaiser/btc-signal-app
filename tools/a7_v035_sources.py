"""One-shot public PF_XBTUSD history snapshot for the V035 follow-up.

No credentials, trading endpoint, background collection or mutable source inputs.
This is source acquisition only, never a derivative return calculation.
"""
import gzip
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "docs" / "audit-nacharbeit-2026-10" / "A7-V035-sources"
START_MS = 1768766400000  # R0/R1 active start, 2026-01-18 20:00 UTC
END_MS = 1790683200000    # R1 exclusive cutoff, 2026-09-29 12:00 UTC
BASE = "https://futures.kraken.com/api/charts/v1"
SERIES = (("trade", "4h", 14_400_000, START_MS),
          ("mark", "1h", 3_600_000, START_MS - 3_600_000),
          ("spot", "1h", 3_600_000, START_MS - 3_600_000))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch_series(kind, resolution, step, start):
    candles, pages, cursor = [], [], start
    while cursor <= END_MS:
        url = (f"{BASE}/{kind}/PF_XBTUSD/{resolution}?" +
               urlencode({"from": cursor // 1000, "to": END_MS // 1000}))
        request = Request(url, headers={"Accept": "application/json",
                                        "User-Agent": "btc-audit-v035-public-history/1"})
        with urlopen(request, timeout=120) as response:
            assert response.status == 200
            raw = response.read()
        payload = json.loads(raw)
        page = payload["candles"]
        if not page:
            raise ValueError(f"Empty page {url}")
        times = [int(c["time"]) for c in page]
        if times != sorted(set(times)) or times[0] < cursor or times[-1] > END_MS:
            raise ValueError(f"Invalid page timestamp {url}")
        pages.append({"url": url, "sha256": hashlib.sha256(raw).hexdigest(),
                      "count": len(page), "first": times[0], "last": times[-1]})
        candles.extend(page)
        cursor = times[-1] + step
        if not payload["more_candles"]:
            break
    times = [int(c["time"]) for c in candles]
    expected = list(range(start, END_MS + 1, step))
    if times != expected:
        missing = sorted(set(expected) - set(times))
        raise ValueError(f"Incomplete {kind} {resolution}: {len(times)}/{len(expected)}, "
                         f"first gaps {missing[:5]}")
    for c in candles:
        o, h, l, cl = (float(c[k]) for k in ("open", "high", "low", "close"))
        if not 0 < l <= min(o, cl) <= max(o, cl) <= h:
            raise ValueError(f"Invalid OHLC at {c['time']}")
    return candles, pages


def main():
    if DEST.exists():
        raise FileExistsError(f"Snapshot already exists; never overwrite: {DEST}")
    DEST.mkdir(parents=True)
    manifest = {"schema": "a7-v035-public-source-snapshot-v1",
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "source": "Kraken public charts API", "symbol": "PF_XBTUSD",
                "active_start_ms": START_MS, "r1_cutoff_ms": END_MS,
                "historical_api_as_of_proven": False,
                "historical_trading_fills_proven": False, "series": {}}
    for kind, resolution, step, start in SERIES:
        candles, pages = fetch_series(kind, resolution, step, start)
        path = DEST / f"{kind}-{resolution}.json.gz"
        raw = (json.dumps(candles, separators=(",", ":"), ensure_ascii=False) + "\n").encode()
        path.write_bytes(gzip.compress(raw, mtime=0))
        manifest["series"][f"{kind}-{resolution}"] = {
            "file": path.name, "sha256": sha(path), "count": len(candles),
            "first_ms": int(candles[0]["time"]), "last_ms": int(candles[-1]["time"]),
            "step_ms": step, "pages": pages}
        print(kind, resolution, len(candles), len(pages), path.name, flush=True)
    (DEST / "manifest.json").write_bytes(
        (json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode())


if __name__ == "__main__":
    main()
