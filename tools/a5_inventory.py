"""Additive F02/F12 classification of original configurations; no strategy runs."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
from derivative_accounting import require_spot_config, NotEvaluable


def inventory(source):
    paths = [source/'gitter-plan.json'] + sorted((source/'struktur').glob('S*.json'))
    hashes = {}
    candidates = []
    for path in paths:
        raw = path.read_bytes()
        hashes[path.relative_to(source).as_posix()] = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        candidates.extend(data['rows'] if path.name=='gitter-plan.json' else [data])
    rows, seen = [], {}
    for item in candidates:
        params = item['params']
        canonical = json.dumps(params,sort_keys=True,separators=(',',':'))
        if canonical in seen:
            next(r for r in rows if r['id']==seen[canonical])['aliases'].append(item['id'])
            continue
        seen[canonical] = item['id']
        try:
            require_spot_config(params)
            status = 'no_F02_block_under_explicit_spot_model'
            reason = 'Only model Spot; no historical instrument proof or general A7 data clearance.'
        except NotEvaluable:
            status = 'not_evaluable'
            reason = ('F02: causal derivative strategy path, historical instrument/margin terms, '
                      'complete exact funding settlements and matching marks not established. '
                      'Flow funding indicators are not settlement records; no zero substitution.')
        rows.append(dict(id=item['id'],aliases=[],params=params,
            params_sha256=hashlib.sha256(canonical.encode()).hexdigest(),
            f02_status=status,reason=reason,historical_execution_proven=False,
            f12='Legacy level/close is retrospective; not V2 or an actual prior order.'))
    assert len(rows)==86, len(rows)
    assert [r['id'] for r in rows if r['f02_status']=='not_evaluable']==['V035']
    return dict(version=1,stage='A5',base_commit='291588946206333ca58d771f1cc96f261da1a981',
        source_commit='ccf2b01c0578346f325261e72445b7375a9ac706',
        scope='Classification only; no historical calculation, strategy changes or instrument evidence inferred',
        source_sha256=hashes,rows=rows,
        separate_capital_quotas='Unchanged and not recomputed; A7 must retain original capital plan.',
        other_limits='A3 aggregate basket/conversion blocks remain; no V2, E41.6 or manual live holdings proof.')


if __name__=='__main__':
    data=inventory(ROOT.parent/'audit-work/docs/audit-2026-09-27')
    dest=ROOT/'docs/audit-nacharbeit-2026-10/A5-historical-eligibility-v1.json'
    dest.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print('86 original configurations, V035 not evaluable; no historical runs')
