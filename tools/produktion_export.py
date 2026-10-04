"""Allowlisted public display export from one v2 store, never the raw state."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'engine'))
import durable_delivery as durable
from production_contract import canonical

STATE_FIELDS=('pos_state','direction','last_signal_ts','entry_ref','entry_pct',
              'bestand_pct','last_close','updated_at')
SIGNAL_FIELDS=('ts','type','price','tranche_pct','tag','label','reason','stop_ref')


def _scalar(value):
    return value is None or type(value) in (str,int,float,bool)


def export(store_path,store_id,out):
    out=Path(out)
    if out.exists(): raise FileExistsError(out)
    with durable.VolumeStore(store_path,store_id) as store:
        if store.snapshot['version']!=2: raise ValueError('v2 store required')
        state=store.snapshot['engine']
        public_state={k:state[k] for k in STATE_FIELDS if k in state and _scalar(state[k])}
        raw_signals=state['_delivery']['signals']['signals']
        signals=[]
        for row in raw_signals:
            if not isinstance(row,dict): raise ValueError('Invalid signal row')
            public={k:row[k] for k in SIGNAL_FIELDS if k in row and _scalar(row[k])}
            if type(public.get('ts')) is not int or not isinstance(public.get('type'),str):
                raise ValueError('Incomplete public signal')
            signals.append(public)
        oi=state['_delivery']['oi_history']
        if any(not isinstance(row,list) or len(row)!=2 or type(row[0]) is not int or
               type(row[1]) not in (int,float) for row in oi):
            raise ValueError('Invalid public OI projection')
        values={'state.json':public_state,'signals.json':{'signals':signals},'oi_history.json':oi}
        revision=store.revision
    stage=Path(tempfile.mkdtemp(prefix='.produktion-export-',dir=out.parent))
    try:
        for name,value in values.items():
            (stage/name).write_text(canonical(value)+'\n',encoding='utf-8')
        manifest={'schema':'produktion-public-export-v1','revision':revision,
                  'files':{name:hashlib.sha256((stage/name).read_bytes()).hexdigest() for name in values}}
        (stage/'manifest.json').write_text(canonical(manifest)+'\n',encoding='utf-8')
        stage.rename(out)
    finally:
        if stage.exists(): shutil.rmtree(stage)
    return manifest


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--store',required=True);p.add_argument('--store-id',required=True)
    p.add_argument('--out',required=True);a=p.parse_args()
    print(canonical(export(a.store,a.store_id,a.out)))
