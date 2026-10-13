"""Fixture-only child transport/input/clock; current operations checks intact."""
import os,json,atexit,socket,sqlite3,types
from datetime import datetime,timezone
from pathlib import Path

def install():
    import p3_github_probe as p
    import p3_probe_simulation as sim
    import test_p3_rules403 as t
    import p3_public_operations as o
    cfg=json.loads(Path(os.environ['P3_OPERATIONS_FIXTURE']).read_text());root=Path(cfg['root']);out=Path(cfg['output']);out.mkdir(exist_ok=True)
    plan=o.read(root/'plan.json');state=root/'api-state.json';api=sim.API(plan,persisted=None)
    if state.exists():
        saved=o.read(state);api.head=saved['head'];api.records=saved['records']
    else:api.head=plan['seed_commit'];api.records[api.head]['tree']=o.u.c.git(root/'execution','rev-parse',o.u.SEED+'^{tree}').decode().strip()
    api.persisted=state
    wire={'pid':os.getpid(),'prompts':[],'http':[],'real_network':False,'current_checks_unpatched':True}
    def save():
        (out/('wire-'+str(os.getpid())+'.json')).write_text(p.canonical(wire),encoding='utf-8')
    atexit.register(save)
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=t.deny
    class Clock(datetime):
        current=datetime.fromisoformat(cfg.get('at','2026-10-14T00:00:00Z').replace('Z','+00:00'))
        @classmethod
        def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)
    p.datetime=Clock
    def ask(label):
        wire['prompts'].append(label.split()[0])
        if cfg.get('mode')=='input-cancel':raise KeyboardInterrupt()
        if cfg.get('mode')=='input-expiry':Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
        return sim.FIXTURE_TOKEN
    p.getpass.getpass=ask
    def opened(req,**kw):
        db=sqlite3.connect((root/'session/probe-session.sqlite3').as_uri()+'?mode=ro',uri=True)
        row=json.loads(db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0]);published=db.execute('SELECT published FROM frontier').fetchone()[0];db.close()
        assert row['event']=='request' and row['method']==req.method and published==row['hash']
        assert req.get_header('Authorization')=='Bearer '+sim.FIXTURE_TOKEN
        wire['http'].append({'method':req.method,'url':req.full_url,'phase':row['phase'],'counts':row['counts']})
        base=p.gh.GitHubContentsClient._route(plan['repo'],'');tail=req.full_url.split('https://api.github.com'+base)[1].split('?')[0]
        if tail=='':return sim.Response({'id':plan['repository_id'],'full_name':plan['repo'],'private':cfg.get('mode')=='private','has_pages':False,'archived':False,'permissions':{'admin':True}})
        if tail=='/pages' or tail.endswith('/protection'):raise t.http_error(req.full_url,404,'Branch not protected' if tail.endswith('/protection') else 'Not Found')
        if '/rules/branches/' in tail and cfg.get('mode')=='rules-present':return sim.Response([{'type':'required_status_checks'}])
        response=api.open(req,**kw)
        if cfg.get('mode')=='late-put' and req.method=='PUT':Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
        return response
    p.urllib.request.build_opener=lambda *a,**k:types.SimpleNamespace(open=opened)
