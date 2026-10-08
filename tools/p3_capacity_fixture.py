"""Real local Git fixtures; synthetic run events/messages, never transport/data."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import durable_delivery as durable
import github_delivery as github
import run_health
import telegram_outbox as box
from production_contract import canonical, digest, CANDLE_MS
from test_production_runtime import seeded
from test_github_delivery import REPO,BRANCH,STORE_ID
from test_p3_operations import run_env,finish
import p3_backup_chain as chain


class GitWriter:
    def __init__(self,repo,seed):
        self.repo=repo;self.envelope=json.loads(seed);self.snapshot=self.envelope['snapshot']
        self.revision=-1;self.pin=None;self.prior_digest=chain.ZERO;self.p=None
        self.body_bytes=0;self.min_bytes=10**12;self.max_bytes=0;self.health_max=0
        self.mark=0;self.budget=chain.Budget()

    def start(self):
        self.cm=chain.process(self.repo,['fast-import','--quiet','--date-format=raw'],self.budget)
        self.p=self.cm.__enter__();self.mark=0

    def stop(self):
        self.p.stdin.write(b'done\n');self.p.stdin.flush();self.cm.__exit__(None,None,None);self.p=None

    def commit(self):
        self.revision+=1
        env={**self.envelope,'snapshot':self.snapshot,'revision':self.revision,
            'write_id':'synthetic-capacity-'+str(self.revision),'parent_digest':self.prior_digest,
            'body_digest':digest(self.snapshot)}
        body=canonical(env).encode();chain.parser(dict(repo=REPO,branch=BRANCH,store_id=STORE_ID,
            stream_id=self.snapshot['control']['stream_id']))._parse({'body':body})
        self.mark+=2; blob=self.mark-1
        message=f'Synthetic capacity revision {self.revision}\n'.encode()
        data=f'blob\nmark :{blob}\ndata {len(body)}\n'.encode()+body+b'\n'
        data+=f'commit refs/heads/{BRANCH}\nmark :{self.mark}\ncommitter Offline P3 <synthetic@example.invalid> {1700000000+self.revision} +0000\ndata {len(message)}\n'.encode()+message
        if self.pin:data+=f'from {":"+str(self.mark-2) if self.mark>2 else self.pin}\n'.encode()
        data+=f'M 100644 :{blob} {github.STORE_PATH}\n\nget-mark :{self.mark}\n'.encode()
        self.p.stdin.write(data);self.p.stdin.flush()
        self.pin=self.p.stdout.readline().decode().strip()
        if not chain.HEX40.fullmatch(self.pin):raise ValueError('Fixture import interrupted')
        self.prior_digest=env['body_digest'];self.body=body
        self.blob=hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
        self.body_bytes+=len(body);self.min_bytes=min(self.min_bytes,len(body));self.max_bytes=max(self.max_bytes,len(body))
        self.health_max=max(self.health_max,len(canonical(self.snapshot['control']['health']).encode()))
        self.budget.check()

    def confirmed_record(self):
        return dict(adapter='github',repo=REPO,branch=BRANCH,path=github.STORE_PATH,store_id=STORE_ID,
            revision=self.revision,commit_sha=self.pin,blob_sha=self.blob,snapshot_digest=self.prior_digest)


def message_load(w,day,base):
    # Six extra writes inside the final owned watch, before its completion.
    state=w.snapshot['commands'].setdefault('capacity-load',dict(result='synthetic-only',
        _delivery=dict(version=1,messages=[],signals={'signals':[]},oi_history=[])))
    d=state['_delivery']
    for n in range(2):
        key=f'{day}-{n}';text='Synthetic capacity message '+key+' '+('offline fixture text '*48)
        box.enqueue(d,'capacity',key,0,dict(text=text,day=day,fixture=True),text)
        d['signals']['signals'].append(dict(event=key,ts=base+day*86400000,synthetic=True))
        d['oi_history'].append(dict(ts=base+day*86400000,value=day*2+n,synthetic=True))
        w.commit();m=d['messages'][-1];m.update(status='sending',attempts=1,target='a'*64);w.commit()
        m.update(status='confirmed',receipt=day*2+n+1);w.commit()


def create(root,days=0,simple_count=12):
    root=Path(root);root.mkdir(exist_ok=False)
    store,_,paths=seeded(root)
    with durable.read_only_volume(store,STORE_ID) as s:seed=github.initial_envelope(s.snapshot,REPO,BRANCH,STORE_ID)
    repo=root/'synthetic-git';repo.mkdir();budget=chain.Budget();chain.git(repo,budget,'init','--bare','-b',BRANCH)
    w=GitWriter(repo,seed);w.start();w.commit();w.snapshot['control']['mode']='active';w.commit();w.stop()
    pins=[];base=w.snapshot['control']['migration']['W']+2*CANDLE_MS
    if not days:
        w.start()
        for _ in range(simple_count-2):
            w.snapshot['control']['health']['synthetic_tick']=w.revision+1;w.commit()
        w.stop();pins.append(dict(pin=w.pin,revision=w.revision))
    for day in range(days):
        w.start()
        # 96 watches + six signals, each claim/start/candidate/attestation/release.
        events=[('watch',base+day*86400000+n*900000+480000) for n in range(96)]
        events += [('signal',base+day*86400000+n*CANDLE_MS+120000) for n in range(6)]
        for kind,slot in sorted(events,key=lambda x:x[1]):
            rid=str(100000+w.revision)
            w.owner=dict(repository=REPO,run_id=rid,run_attempt='1',nonce=digest([day,rid])[:32])
            w.snapshot['control']['owner']=deepcopy(w.owner);w.commit()
            if kind=='signal':w.snapshot['engine']['last_signal_ts']=slot-120000-CANDLE_MS
            with patch.dict(os.environ,run_env(kind,slot,rid)):
                run_health.record_event(w,kind,'start',slot+1000,None)
                if slot==base+day*86400000+95*900000+480000:message_load(w,day,base)
                finish(w,kind,slot)
            w.snapshot['control']['owner']=None;w.commit()
        w.stop();pins.append(dict(day=day+1,pin=w.pin,revision=w.revision))
        print('fixture day',day+1,'states',w.revision+1,'body',len(w.body),flush=True)
    identity=dict(repo=REPO,branch=BRANCH,store_id=STORE_ID,stream_id=w.snapshot['control']['stream_id'])
    chain.git(repo,budget,'update-ref','refs/heads/all-synthetic-history',w.pin)
    result=dict(synthetic=True,source=str(repo),migration=str(paths[-1]),identity=identity,pins=pins,
        states=w.revision+1,days=days,minimum_writes_per_day=510,additional_writes_per_day=6 if days else 0,
        retained_messages=days*2,message_writes_inside_owned_run=True,
        body_bytes=w.body_bytes,min_body_bytes=w.min_bytes,max_body_bytes=w.max_bytes,
        max_health_bytes=w.health_max,completed_index_counts={k:len(v) for k,v in
            w.snapshot['control']['health'].get('completed_runs',{}).items()},metrics=w.budget.metrics())
    chain.write_json(root/'fixture.json',result)
    return result


if __name__=='__main__':
    for key in list(os.environ):
        if key.startswith(('BTC_DELIVERY_','TELEGRAM_','GITHUB_','GH_')):del os.environ[key]
    create(sys.argv[1],int(sys.argv[2]))
