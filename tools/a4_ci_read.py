"""Public, unauthenticated GitHub reads only; never credentials or dispatch."""
import base64
import json
import sys
import urllib.request

API='https://api.github.com/repos/szoceikaiser/btc-signal-app'


def get(path):
    req=urllib.request.Request(API+path,headers={'Accept':'application/vnd.github+json','User-Agent':'A4-offline-audit-ci-check'})
    with urllib.request.urlopen(req,timeout=30) as response:
        return json.load(response)


if sys.argv[1]=='workflows':
    sha=get('/branches/main')['commit']['sha']
    files=get('/contents/.github/workflows?ref='+sha)
    result={'observed_main':sha,'workflows':{}}
    for f in files:
        if f['name'].endswith(('.yml','.yaml')):
            item=get('/contents/'+f['path']+'?ref='+sha)
            result['workflows'][f['name']]=base64.b64decode(item['content']).decode()
    print(json.dumps(result,indent=2))
else:
    sha=sys.argv[1]
    runs=get('/actions/runs?head_sha='+sha+'&per_page=100')['workflow_runs']
    result=[{k:r[k] for k in ('id','name','event','head_sha','status','conclusion','html_url')} for r in runs]
    assert all(r['name']=='Tests' and r['event']=='push' and r['head_sha']==sha for r in result), result
    print(json.dumps({'sha':sha,'runs':result,'success':bool(result) and all(r['conclusion']=='success' for r in result)},indent=2))
