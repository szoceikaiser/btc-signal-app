"""Offline child injection for the actual -B script entry; never a production hook.

Loaded only by a test-created sitecustomize through an explicit fixture PYTHONPATH.
No code, guard, class, route, frontier or authorization check is bypassed here.
"""
import atexit
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import types


def install():
    import p3_github_probe as p
    import p3_rules403 as r
    import test_p3_rules403 as t
    config=json.loads(Path(os.environ['P3_SCRIPT_FIXTURE']).read_text())
    root=Path(config['root']);out=Path(config['output']);out.mkdir(exist_ok=True)
    plan=t.read(root/'plan.json');api=t.RulesAPI(plan,config.get('mode','positive'))
    result={'argv':sys.argv[:],'pid':os.getpid(),'prompts':[],'http':[],'pushes':0,'known_denial':[],
            'input_transport_only_injection':True,'code_guard_frontier_checks_unpatched':True}
    def save(name,value):
        with (out/name).open('w',encoding='utf-8',newline='\n') as f:
            f.write(p.canonical(value)+'\n');f.flush();os.fsync(f.fileno())
    atexit.register(lambda:save('wire.json',result))
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=t.deny
    class Clock(datetime):
        current=datetime.fromisoformat(config['start_utc'].replace('Z','+00:00')) if config.get('start_utc') else None
        @classmethod
        def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)
    if Clock.current:p.datetime=Clock
    def expire():Clock.current=datetime.fromisoformat(config['deadline'].replace('Z','+00:00'))
    def ask(label):
        result['prompts'].append(label)
        if config.get('expire_on')=='reader':expire()
        return t.sim.FIXTURE_TOKEN
    p.getpass.getpass=ask
    def reservation(method):
        db=sqlite3.connect((root/'probe-session.sqlite3').as_uri()+'?mode=ro',uri=True)
        last=t.previous.read_latest(db);published=db.execute('SELECT published FROM frontier').fetchone()[0];db.close()
        assert published==last['hash'] and last['event']=='request' and last['method']==method
        with (out/'outbound.jsonl').open('a',encoding='utf-8') as f:
            f.write(p.canonical({'method':method,'published':published,'counts':last['counts']})+'\n');f.flush();os.fsync(f.fileno())
    def opened(req,**kw):
        reservation(req.method);result['http'].append({'method':req.method,'url':req.full_url})
        value=api.open(req,**kw)
        if config.get('expire_on')=='response':expire()
        return value
    p.urllib.request.build_opener=lambda *a,**kw:types.SimpleNamespace(open=opened)
    original_run=subprocess.run
    def run(args,**kw):
        if 'push' not in args:return original_run(args,**kw)
        assert config.get('allow_fixture_push') is True
        assert args[-1]==plan['seed_commit']+':refs/heads/'+plan['branch']
        assert kw['env']['P3_EXPLICIT_BOOTSTRAP_TOKEN']==t.sim.FIXTURE_TOKEN
        reservation('GIT_PUSH');result['pushes']+=1;api.head=plan['seed_commit']
        if config.get('expire_on')=='push-response':expire();raise subprocess.TimeoutExpired('fixture',15)
        return types.SimpleNamespace(returncode=0)
    subprocess.run=run
    original_checkpoint=p.Ledger.checkpoint
    def checkpoint(self,point,event):
        original_checkpoint(self,point,event)
        if [point,event]==config.get('kill'):
            save('cutpoint.json',{'point':point,'event':event,'pid':os.getpid()});os._exit(71)
        if point=='before_outbound' and config.get('expire_on')=='before-'+event:expire()
    p.Ledger.checkpoint=checkpoint
    # Observe the unchanged predicate; never change its input/result or exception.
    original_require=p.require
    def require(ok,reason):
        if not ok and reason=='Bound rules review required':
            result['known_denial'].append(reason)
            result['main_class_is_canonical']=getattr(sys.modules['__main__'],'RulesGuard',None) is r.RulesGuard
        return original_require(ok,reason)
    p.require=require
