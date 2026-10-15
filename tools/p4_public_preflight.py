"""Explicit bounded public jobtoken admission check. No setup/mutations.

Run against a completed, externally reviewed access document only. This command
does not discover or bless hidden bypasses or actual credential write reach.
"""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import public_access as public
from production_contract import canonical,digest


def cli(argv=None):
    p=argparse.ArgumentParser();p.add_argument('--review',required=True);p.add_argument('--out',required=True)
    p.add_argument('--public-read',action='store_true');a=p.parse_args(argv)
    try:
        from job_quota import read_only_environment
        read_only_environment()
        with Path(a.review).open('rb') as f: raw=f.read(128*1024+1)
        if len(raw)>128*1024 or not a.public_read: raise ValueError('Explicit bounded public read required')
        access=json.loads(raw)
        bindings=[(repo,branch) for repo,t in access['repositories'].items() for branch in t['branches']]
        protected=[(v['repository'],v['branch']) for v in access['protections'].values()]
        if len(bindings)>8 or len(protected)!=4: raise ValueError('Exact small reviewed operating set required')
        # Exclusivity checked before any request; failed checks retain only a refusal.
        out=Path(a.out);out.mkdir(exist_ok=False)
        try:
            gets=public.preflight(access,bindings,protected)
            value={'schema':'btc-public-preflight-v1','access_sha256':digest(access),
                'public_identity_and_rules_match':True,'get':gets,'mutations':0,
                'hidden_bypass_current_state_proven':False,'credential_write_reach_proven':False}
            (out/'RESULT.json').write_text(canonical(value)+'\n',encoding='utf-8')
        except Exception:
            (out/'REFUSED.txt').write_text('Public identity/rules review not confirmed. No mutation.\n',encoding='utf-8')
            raise
        print('Public identity/rules match the separate review; hidden settings and writer scope remain separate evidence.')
        return 0
    except Exception:
        print('Bounded public preflight refused.',file=sys.stderr);return 20


if __name__=='__main__': sys.exit(cli())
