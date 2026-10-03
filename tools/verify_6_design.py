"""Read-only consistency of the draft registry and frozen candidate identities."""
import gzip
import hashlib
import json
from pathlib import Path
from verify_6 import BASE, digest

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT/'docs/nacharbeit-2026-09-28'

def verify():
    registry = json.loads((DOC/'6-design-register.json').read_text(encoding='utf-8'))
    assert registry['base'] == BASE and registry['measured'] is False
    assert registry['live_go'] is False and registry['family_size'] == 1
    with gzip.open(DOC/'6-ledger.json.gz', 'rt', encoding='utf-8') as f:
        rows = json.load(f)
    assert registry['rows'] == [dict(name=r['name'], params=r['params'], params_sha256=digest(r['params'])) for r in rows]
    assert registry['document_sha256'] == hashlib.sha256((DOC/'6-BESTAETIGUNGSDESIGN.md').read_text(encoding='utf-8').encode('utf-8')).hexdigest()
    assert set(registry['decisions']) == {'D6-A', 'D6-B', 'D6-C'}
    states = [d['status'] for d in registry['decisions'].values()]
    assert states == ['confirmed', 'withdrawn', 'withdrawn']
    assert registry['version'] == 2
    assert registry['status'] == 'Retrospektives Prüfdesign; keine Jahreswartezeit; Umsetzung offen'
    assert registry['historical_selection_family_size'] is None
    assert registry['inference_scope'] == 'Conditional fixed pair; historical selection adjustment not established'
    assert registry['minimum_wealth_advantage'] is None
    assert registry['absolute_dd_budgets'] is None
    assert registry['window']['r1_cutoff_utc'] == '2026-09-29T12:00:00Z'
    assert registry['window']['r1_measured'] is False
    assert registry['implementation_registration_complete'] is False
    assert registry['scenarios'] == [
        dict(id='S0', next_open_offset=1, fee_pct=.1, slippage_pct=0.),
        dict(id='S1', next_open_offset=1, fee_pct=.1, slippage_pct=.1),
        dict(id='S2', next_open_offset=1, fee_pct=.1, slippage_pct=.5),
        dict(id='S3', next_open_offset=2, fee_pct=.1, slippage_pct=.1),
        dict(id='S4', next_open_offset=2, fee_pct=.1, slippage_pct=.5)]
    return dict(result='PASS', status=registry['status'], frozen_parameter_hashes_verified=True,
        document_sha256=registry['document_sha256'], decisions=registry['decisions'],
        no_confirmation_measurement=True, no_waiting_year=True,
        historical_selection_adjustment_established=False, live_go=False)

if __name__ == '__main__': print(json.dumps(verify(), ensure_ascii=False, indent=2))
