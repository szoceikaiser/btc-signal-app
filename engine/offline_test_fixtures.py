"""Synthetic current public/automatic-reader contracts, no credentials or network."""
import base64,io,json,os,urllib.parse
from production_contract import canonical

def sender_access(runtime):
    from test_free_public import access_for,writer_review
    repo=runtime['private_store_repository'];branches=[runtime['store_branch'],runtime['fence_branch']]
    access,rules,sets=access_for({repo:{'id':51,'visibility':'public','branches':branches},'synthetic/code':{'id':52,'visibility':'public','branches':['synthetic']}})
    writer_review(access,'sender_write',repo,branches)
    return access,rules,sets

def branch_reply(http,req,timeout):
    from test_github_delivery import REPO
    from test_betriebsabschluss import metadata
    u=urllib.parse.urlsplit(req.full_url);parts=u.path.split('/')
    # Worker reopens its synthetic runtime for genuine process-loss tests.
    if not hasattr(http,'access'):
        import sys
        runtime=json.loads(__import__('pathlib').Path(sys.argv[2]).read_text())
        http.access,http.rules,http.rulesets=sender_access(runtime)
    if u.netloc=='github.com':
        assert req.get_header('Authorization')=='Basic '+base64.b64encode(('x-access-token:'+os.environ['GITHUB_TOKEN']).encode()).decode()
        heads={}
        for branch,pin in http.state['heads'].items():
            http.refs+=1
            selected= 'delivery-only' if http.selected_path=='delivery/stream.json' else 'actions-fence'
            if http.old and branch==selected and (http.mode=='old' or http.mode=='delayed' and http.refs<=4):pin=http.old
            heads[branch]=pin
        def pkt(raw):return f'{len(raw)+4:04x}'.encode()+raw
        raw=pkt(b'# service=git-upload-pack\n')+b'0000'
        for j,(branch,pin) in enumerate(heads.items()):raw+=pkt((pin+' refs/heads/'+branch+('\0side-band-64k' if j==0 else '')+'\n').encode())
        http.seen.append(('GET',req.full_url,timeout));return io.BytesIO(raw+b'0000')
    if u.netloc=='raw.githubusercontent.com':
        pin=parts[3];name='/'.join(parts[4:]);raw=http.state['history'][pin][name].encode()
        http.seen.append(('GET',req.full_url,timeout));return io.BytesIO((b' '*2097153 if http.mode=='oversize' else b'')+raw)
    repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
    if not tail:v={'id':http.access['repositories'][repo]['id'],'full_name':repo,'private':False,'visibility':'public'}
    elif tail.startswith('/rules/branches/'):v=http.rules[(repo,tail.rsplit('/',1)[-1])]
    elif tail.startswith('/rulesets/'):v=http.rulesets[(repo,int(tail.rsplit('/',1)[-1]))]
    elif tail.startswith('/actions/runs/'):
        kind=os.environ['BTC_DELIVERY_WORKFLOW'].split('/')[-1][:-4]
        v=metadata(kind,1791100920000,os.environ['GITHUB_RUN_ID'],int(os.environ['GITHUB_RUN_NUMBER']))
        v['event']=os.environ['GITHUB_EVENT_NAME']
    else:return None
    http.seen.append((req.get_method(),req.full_url,timeout));return io.BytesIO(canonical(v).encode())

def hosted_access(runtime,identity):
    from test_free_public import access_for,writer_review
    access,rules,sets=access_for({identity['repo']:{'id':1,'visibility':'public','branches':[identity['branch'],'fence','migration']},'synthetic/backup':{'id':2,'visibility':'public','branches':['packages']},'synthetic/receipts':{'id':3,'visibility':'public','branches':['receipts']},'synthetic/code':{'id':4,'visibility':'public','branches':['synthetic']}})
    writer_review(access,'backup_write','synthetic/backup',['packages']);writer_review(access,'receipt_write','synthetic/receipts',['receipts'])
    return access,rules,sets

def provider_reply(provider,req,timeout):
    u=urllib.parse.urlsplit(req.full_url);parts=u.path.split('/')
    if u.netloc=='raw.githubusercontent.com':
        assert req.get_header('Authorization')=='Bearer '+provider.tokens['metadata_read']
        repo='/'.join(parts[1:3]);pin=parts[3];name='/'.join(parts[4:])
        if repo=='synthetic/code':raw=provider.yaml[name]
        else:
            import p3_backup_chain as b
            local=provider.repo(repo,pin)
            with b.batch(local,b.Budget()) as read:raw=read(pin+':'+name,'blob',b.MAX_PACKAGE)
        provider.seen.append(('GET',repo,'/raw/'+name))
        return io.BytesIO(raw)
    if u.netloc!='api.github.com':return None
    repo='/'.join(parts[2:4]);tail='/'+('/'.join(parts[4:])) if len(parts)>4 else ''
    if not tail and repo=='synthetic/code':v={'id':4,'full_name':repo,'private':False,'visibility':'public'}
    elif tail.startswith('/rules/branches/'):v=provider.rules[(repo,tail.rsplit('/',1)[-1])]
    elif tail.startswith('/rulesets/'):v=provider.rulesets[(repo,int(tail.rsplit('/',1)[-1]))]
    else:return None
    provider.seen.append((req.get_method(),repo,tail));return io.BytesIO(canonical(v).encode())

def monitor_reply(http,req,timeout):
    u=urllib.parse.urlsplit(req.full_url);parts=u.path.split('/')
    if u.netloc=='github.com':
        from test_free_quota import advertisement
        repo=u.path.split('.git/')[0].lstrip('/')
        for r,branch in http.heads:
            if r==repo:
                logical='/repos/'+r+'/git/ref/heads/'+branch
                http.seen.append(logical)
                if http.hook:http.hook(http,logical)
        return advertisement([(branch,pin) for (r,branch),pin in http.heads.items() if r==repo])
    if u.netloc=='raw.githubusercontent.com':
        repo='/'.join(parts[1:3]);pin=parts[3];name='/'.join(parts[4:]);logical='/repos/'+repo+'/contents/'+name
        http.seen.append(logical)
        if http.hook:http.hook(http,logical)
        return io.BytesIO(http.records[(repo,pin,name)])
    return None
