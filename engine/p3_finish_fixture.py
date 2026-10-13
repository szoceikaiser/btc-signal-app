import os,json,sqlite3,atexit,types,socket
from pathlib import Path
from datetime import datetime
def install():
    import p3_happy_finish as f
    import p3_probe_simulation as sim
    import test_p3_rules403 as t
    p=f.p;cfg=f.read(os.environ['P3_FINISH_FIXTURE']);root=Path(cfg['root']);out=Path(cfg['out']);mode=cfg['mode'];plan=f.read(root/'plan.json')
    saved=f.read(root/'api-state.json');api=sim.API(plan);api.records=saved['records'];api.head=saved['head'];accepted=saved['accepted'];pending=saved['pending']
    wire={'prompts':[],'http':[],'network':False,'current_gates_unpatched':True}
    atexit.register(lambda:(out/('wire-'+str(os.getpid())+'.json')).write_text(p.canonical(wire),encoding='utf-8'))
    socket.socket.connect=socket.socket.connect_ex=socket.create_connection=p.urllib.request.urlopen=t.deny
    class Clock(datetime):
        current=datetime.fromisoformat('2026-10-14T00:00:00+00:00')
        @classmethod
        def now(cls,tz=None):return cls.current if tz else cls.current.replace(tzinfo=None)
    p.datetime=Clock;p.getpass.getpass=lambda label:(wire['prompts'].append(label.split()[0]) or sim.FIXTURE_TOKEN)
    def save():
        (root/'api-state.json').write_text(p.canonical({'records':api.records,'head':api.head,'accepted':accepted,'pending':pending}),encoding='utf-8')
    def opened(req,**kw):
        nonlocal pending,accepted
        db=sqlite3.connect((root/'session/probe-session.sqlite3').as_uri()+'?mode=ro',uri=True)
        row=json.loads(db.execute('SELECT body FROM events ORDER BY seq DESC LIMIT 1').fetchone()[0]);published=db.execute('SELECT published FROM frontier').fetchone()[0];db.close()
        assert row['event']=='request' and row['method']==req.method and row['hash']==published
        assert req.get_header('Authorization')=='Bearer '+sim.FIXTURE_TOKEN
        wire['http'].append({'method':req.method,'route':row['route'],'counts':row['counts'],'extra':row.get('confirmation_retry',False)})
        tail=req.full_url.split('https://api.github.com'+f.r.routes(plan)[0])[1].split('?')[0]
        if req.method=='PUT':
            if mode=='CAS409':raise t.http_error(req.full_url,409,'fixture conflict')
            old=api.head
            response=api.open(req,**kw);accepted+=1;pending=None
            if mode in ('old-once','moving','old-forever','pool-exhaust') or mode=='worst30' and accepted<=5:
                pending={'old':old,'new':api.head,'refs':0,'max':4 if mode in ('pool-exhaust','worst30') else 2,'kind':mode}
            if mode=='foreign':
                env=json.loads(p.base64.b64decode(api.records[api.head]['body']));env['snapshot']['control']['owner']=p.owner(plan,4);env['body_digest']=p.digest(env['snapshot']);api.put(p.canonical(env).encode(),api.head)
            save()
            if mode=='deadline-put':Clock.current=datetime.fromisoformat(cfg['deadline'].replace('Z','+00:00'))
            if mode=='lost-put':raise TimeoutError('fixture lost mutation response')
            return response
        if not tail:return sim.Response({'id':plan['repository_id'],'full_name':plan['repo'],'private':False,'has_pages':False,'archived':False,'permissions':{'admin':True}})
        if tail=='/pages' or tail.endswith('/protection'):raise t.http_error(req.full_url,404,'Branch not protected' if tail.endswith('/protection') else 'Not Found')
        if tail.startswith('/git/ref/') and pending:
            n=pending['refs'];kind=pending['kind'];sha=pending['old'] if kind=='old-forever' or n<pending['max'] else pending['new']
            if kind=='moving' and n==1:sha=pending['new']
            pending['refs']+=1;save()
            if kind!='old-forever' and pending['refs']>=pending['max']+2:pending=None;save()
            return sim.Response({'ref':'refs/heads/'+plan['branch'],'object':{'type':'commit','sha':sha}})
        response=api.open(req,**kw)
        if tail.startswith('/git/trees/'):
            value=json.loads(response.getvalue());value['sha']=tail.rsplit('/',1)[1];response=sim.Response(value)
        return response
    p.urllib.request.build_opener=lambda *a,**k:types.SimpleNamespace(open=opened)
