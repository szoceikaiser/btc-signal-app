"""Explicit test-sitecustomize injection: input/time/transport/faults only."""
import atexit,json,os,socket,sqlite3,subprocess,types
from datetime import datetime,timezone
from pathlib import Path

def install():
    __import__('offline_git_objects').install()
    import p3_github_probe as p
    import p3_public_root as u
    import test_p3_rules403 as t
    cfg=json.loads(Path(os.environ['P3_PUBLIC_FIXTURE']).read_text());root=Path(cfg['root']);out=Path(cfg['output'])
    plan=t.read(root/'plan.json');api=t.RulesAPI(plan);api.head=None
    api.records[plan['seed_commit']]['tree']=u.c.git(root/'execution','rev-parse',u.SEED+'^{tree}').decode().strip()
    result={'http':[],'prompts':[],'pushes':0,'security_checks_unpatched':True}
    def save(name,x):
        with (out/name).open('w',encoding='utf-8') as f:f.write(p.canonical(x));f.flush();os.fsync(f.fileno())
    atexit.register(lambda:save('wire.json',result))
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=t.deny
    class Clock(datetime):
        current=datetime.fromisoformat(cfg['at'].replace('Z','+00:00'))
        @classmethod
        def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)
    p.datetime=Clock
    def expire():Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
    reader=t.sim.FIXTURE_TOKEN;writer='github_pat_'+'WriterFixtureOnly0'*5
    def ask(label):
        role=label.split()[0];result['prompts'].append(role)
        if cfg['mode']=='input-cancel':raise KeyboardInterrupt()
        if cfg.get('expiry')==role.lower():expire()
        return reader if role=='Reader' else writer
    p.getpass.getpass=ask
    def reserved(method):
        db=sqlite3.connect((root/'session/probe-session.sqlite3').as_uri()+'?mode=ro',uri=True)
        row=json.loads(db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0]);published=db.execute('SELECT published FROM frontier').fetchone()[0];db.close()
        assert row['event']=='request' and row['method']==method and published==row['hash']
        with (out/'outbound.jsonl').open('a',encoding='utf-8') as f:f.write(p.canonical({'method':method,'counts':row['counts'],'published':published})+'\n');f.flush();os.fsync(f.fileno())
    def opened(req,**opts):
        reserved(req.method);assert req.get_header('Authorization') in ('Bearer '+reader,'Bearer '+writer)
        role='Writer' if req.get_header('Authorization')=='Bearer '+writer else 'Reader'
        result['http'].append({'method':req.method,'url':req.full_url,'credential_role':role})
        tail=req.full_url.split('/repos/'+u.REPO)[1].split('?')[0];mode=cfg['mode']
        if tail=='':
            if mode=='writer403' and role=='Writer':raise t.http_error(req.full_url,403,'Resource not accessible by personal access token')
            value={'id':u.RID+(mode=='wrong-repo'),'full_name':u.REPO,'private':mode=='private','has_pages':False,'archived':False,'permissions':{'admin':True}}
            response=t.sim.Response(value)
        elif '/rules/branches/' in tail and mode=='403':raise t.http_error(req.full_url,403,'Resource not accessible by personal access token')
        elif '/rules/branches/' in tail and mode=='rules-present':response=t.sim.Response([{'type':'required_status_checks'}])
        elif tail.endswith('/protection') and mode in ('unprotected-variant','protection-unknown','protection403'):
            raise t.http_error(req.full_url,403 if mode=='protection403' else 404,'Branch not protected' if mode=='unprotected-variant' else 'Unknown protection reply')
        elif tail.endswith('/protection') and mode=='protection-present':response=t.sim.Response({'required_status_checks':{}})
        elif tail=='/pages' and mode=='pages-unknown':raise t.http_error(req.full_url,404,'Unknown missing site')
        elif '/rules/branches/' in tail and mode=='rules404':raise t.http_error(req.full_url,404)
        elif tail=='/branches' and mode=='protected':response=t.sim.Response([] if api.head is None else [{'name':u.p.PUBLIC_ROOT and plan['branch'],'protected':True,'commit':{'sha':u.SEED}}])
        else:
            response=api.open(req,**opts)
            if tail.startswith('/git/commits/') and mode=='bad-parent':
                response=t.sim.Response({'sha':u.SEED,'tree':{'sha':api.records[u.SEED]['tree']},'parents':[{'sha':'f'*40}]})
            if tail.startswith('/git/trees/') and mode=='bad-tree':response=t.sim.Response({'truncated':False,'tree':[]})
            if tail.startswith('/contents/') and mode=='bad-body':response=t.sim.Response({'type':'file','encoding':'base64','sha':'f'*40,'content':'e30='})
        if cfg.get('expiry')=='response':expire()
        return response
    p.urllib.request.build_opener=lambda *a,**kw:types.SimpleNamespace(open=opened)
    original_run=subprocess.run
    def run(args,**kw):
        if 'push' not in args:return original_run(args,**kw)
        reserved('GIT_PUSH');assert args[-1]==u.SEED+':refs/heads/p3-synthetic-only' and '--force' not in args
        assert args[-2]=='https://github.com/'+u.REPO+'.git' and kw['env']['P3_EXPLICIT_BOOTSTRAP_TOKEN']==writer
        result['pushes']+=1;api.head=u.SEED
        if cfg['mode']=='lost-push' or cfg.get('expiry')=='push-response':
            if cfg.get('expiry')=='push-response':expire()
            raise subprocess.TimeoutExpired('fixture',15)
        return types.SimpleNamespace(returncode=0)
    subprocess.run=run
    original=p.Ledger.checkpoint
    def checkpoint(self,point,event):
        original(self,point,event)
        if [point,event]==cfg.get('kill'):save('cutpoint.json',{'point':point,'event':event});os._exit(71)
        if point=='before_outbound' and cfg.get('expiry')=='before-'+event:expire()
        if (point,event)==('before_commit','phase_end') and cfg.get('expiry')=='before-confirmed':expire()
    p.Ledger.checkpoint=checkpoint
