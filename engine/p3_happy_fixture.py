"""Only input/clock/HTTP fixtures for the actual reader process."""
import os,json,atexit,socket,sqlite3,types
from pathlib import Path
from datetime import datetime
def install():
    import p3_happy_readback as h
    import test_p3_rules403 as t
    import p3_probe_simulation as sim
    p=h.p;cfg=h.read(os.environ['P3_HAPPY_FIXTURE']);root=Path(cfg['root']);out=Path(cfg['output']);mode=cfg['mode'];plan=h.read(root/'plan.json')
    model=h.read(root/'body-model.json');records=model['records'];wire={'prompts':[],'http':[],'network':False,'current_gates_unpatched':True}
    atexit.register(lambda:(out/'wire.json').write_text(p.canonical(wire),encoding='utf-8'))
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=t.deny
    class Clock(datetime):
        current=datetime.fromisoformat('2026-10-14T00:00:00+00:00')
        @classmethod
        def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)
    p.datetime=Clock
    def ask(label):
        wire['prompts'].append(label.split()[0]);assert wire['prompts']==['Reader']
        if mode=='input-cancel':raise KeyboardInterrupt()
        if mode=='input-expiry':Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
        return sim.FIXTURE_TOKEN
    p.getpass.getpass=ask
    head=h.OLD if mode in ('old','moving') else 'f'*40
    refs=0
    def opened(req,**kw):
        nonlocal refs
        db=sqlite3.connect((root/'session/probe-session.sqlite3').as_uri()+'?mode=ro',uri=True)
        row=json.loads(db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0]);published=db.execute('SELECT published FROM frontier').fetchone()[0];db.close()
        assert row['event']=='request' and row['method']==req.method=='GET' and row['hash']==published and row['counts']['PUT']==11 and row['counts']['GIT_PUSH']==1
        assert req.get_header('Authorization')=='Bearer '+sim.FIXTURE_TOKEN
        wire['http'].append({'method':req.method,'route':row['route'],'counts':row['counts']})
        route=row['route'];base=h.r.routes(plan)[0];tail=route[len(base):]
        if mode=='403':raise t.http_error(req.full_url,403,'Resource not accessible by personal access token')
        if mode=='429':raise t.http_error(req.full_url,429,'Too many requests')
        if mode=='lost-get':raise TimeoutError('fixture lost read response')
        if mode=='late-response':Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
        if not tail:return sim.Response({'id':plan['repository_id'],'full_name':plan['repo'],'private':mode=='private','has_pages':False,'archived':False,'permissions':{'admin':True}})
        if tail=='/actions/permissions':return sim.Response({'enabled':False})
        if tail=='/pages' or tail.endswith('/protection'):raise t.http_error(req.full_url,404,'opaque fixture' if mode=='unknown404' else 'Branch not protected' if tail.endswith('/protection') else 'Not Found')
        if tail.startswith(('/rules/','/rulesets')):return sim.Response([])
        if tail.startswith('/branches?'):return sim.Response([{'name':plan['branch'],'protected':False,'commit':{'sha':head}}])
        if tail.startswith('/git/ref/'):
            refs+=1;value='f'*40 if mode=='moving' and refs==2 else head
            return sim.Response({'ref':'refs/heads/'+plan['branch'],'object':{'type':'commit','sha':value}})
        if tail.startswith('/contents/'):
            sha=tail.split('ref=')[1];record=records[sha];body=p.base64.b64decode(record['body'])
            if mode=='foreign' and sha=='f'*40:
                env=json.loads(body);env['snapshot']['control']['owner']=p.owner(plan,3);env['body_digest']=p.digest(env['snapshot']);body=p.canonical(env).encode()
            blob=p.hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
            return sim.Response({'type':'file','path':plan['path'],'encoding':'base64','content':p.base64.b64encode(body).decode(),'size':len(body),'sha':blob})
        if tail.startswith('/git/commits/'):
            sha=tail.rsplit('/',1)[1];parents=model['parents'][sha]
            if mode=='bad-parent':parents=['e'*40]
            return sim.Response({'sha':sha,'parents':[{'sha':x} for x in parents],'tree':{'sha':'d'*40}})
        if tail.startswith('/git/trees/'):
            body=p.base64.b64decode(records[head]['body'])
            if mode=='foreign':env=json.loads(body);env['snapshot']['control']['owner']=p.owner(plan,3);env['body_digest']=p.digest(env['snapshot']);body=p.canonical(env).encode()
            blob=p.hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest()
            return sim.Response({'sha':'d'*40,'truncated':False,'tree':[{'path':'delivery','type':'tree','mode':'040000','sha':'c'*40},{'path':plan['path'],'type':'blob','mode':'100644','sha':'e'*40 if mode=='bad-tree' else blob}]})
        raise AssertionError('Unapproved fixture route')
    p.urllib.request.build_opener=lambda *a,**k:types.SimpleNamespace(open=opened)
