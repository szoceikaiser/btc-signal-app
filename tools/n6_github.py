"""Exact-branch dispatch explicitly authorized by user; otherwise GET only.
Credentials are used only for github.com API; artifact redirect is followed
without Authorization. Never show credentials or raw exceptions.
"""
import argparse
import io
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile
ROOT=Path(__file__).resolve().parents[1]
BRANCH='codex/nach-6-historische-auswertung'
API='https://api.github.com/repos/szoceikaiser/btc-signal-app'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['dispatch','status','download','ci'])
    args=parser.parse_args()
    git=['git','-c','safe.directory='+ROOT.as_posix()]
    sha=subprocess.check_output(git+['rev-parse','HEAD'],cwd=ROOT).decode().strip()
    cred=subprocess.run(git+['credential','fill'],input='protocol=https\nhost=github.com\n\n',
        capture_output=True,text=True,check=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    fields=dict(line.split('=',1) for line in cred.stdout.splitlines() if '=' in line)
    headers={'Accept':'application/vnd.github+json','User-Agent':'btc-historical-audit'}
    if fields.get('password'):headers['Authorization']='Bearer '+fields['password']
    def request(path,data=None):
        req=urllib.request.Request(API+path,headers=headers,data=json.dumps(data).encode() if data is not None else None)
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read();return json.loads(raw) if raw else None
    branch=request('/branches/'+BRANCH)
    assert branch['commit']['sha']==sha
    out=ROOT/'docs/nach-6';out.mkdir(exist_ok=True)
    if args.mode=='dispatch':
        assert not (out/'dispatch.json').exists(),'Prevent accidental repeat dispatch'
        # Verify exact SHA has reviewed harmless workflow name and contents.
        workflow=(ROOT/'.github/workflows/coinalyze-test.yml').read_text()
        assert workflow.startswith('name: Nach-6 Historische Rohdaten')
        assert 'contents: read' in workflow and 'TELEGRAM' not in workflow
        request('/actions/workflows/coinalyze-test.yml/dispatches',dict(ref=BRANCH))
        (out/'dispatch.json').write_text(json.dumps(dict(commit=sha,branch=BRANCH,workflow='coinalyze-test.yml',
            user_authorization='Du kannst backtest läufe anstossen',result='accepted'),indent=2),encoding='utf-8')
        print('Isolated data-only dispatch accepted',sha);return
    if args.mode=='ci':
        data=request('/actions/runs?head_sha='+sha+'&per_page=100')['workflow_runs']
        selected=[dict(id=r['id'],name=r['name'],status=r['status'],conclusion=r['conclusion'],
            head_sha=r['head_sha'],event=r['event'],url=r['html_url']) for r in data]
        assert all(r['name']=='Tests' and r['event']=='push' for r in selected)
        ref=request('/git/ref/tags/sicherung/vor-audit-korrekturen-2026-09-28')['object']
        target=request('/git/tags/'+ref['sha'])['object']['sha']
        print(json.dumps(dict(branch=BRANCH,commit=sha,runs=selected,
            tests_success=bool(selected) and all(r['conclusion']=='success' for r in selected),
            tag_object=ref['sha'],tag_target=target,main_observed=request('/branches/main')['commit']['sha']),indent=2));return
    dispatch=json.loads((out/'dispatch.json').read_text(encoding='utf-8'))
    data=request('/actions/workflows/coinalyze-test.yml/runs?branch='+BRANCH+'&per_page=10')['workflow_runs']
    runs=[r for r in data if r['head_sha']==dispatch['commit'] and r['event']=='workflow_dispatch']
    info=[{k:r[k] for k in ['id','name','head_sha','status','conclusion','html_url','created_at']} for r in runs]
    (out/'data-runs.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
    print(json.dumps(info,indent=2))
    if args.mode=='download':
        assert len(runs)==1 and runs[0]['conclusion']=='success'
        artifacts=request('/actions/runs/'+str(runs[0]['id'])+'/artifacts')['artifacts']
        artifact=next(a for a in artifacts if a['name']=='nach-6-historical-raw')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*a,**kw):return None
        try:
            urllib.request.build_opener(NoRedirect).open(urllib.request.Request(artifact['archive_download_url'],headers=headers),timeout=30)
        except urllib.error.HTTPError as e:
            assert e.code==302;url=e.headers['Location']
        with urllib.request.urlopen(url,timeout=30) as r:raw=r.read()
        (out/'raw-artifact.zip').write_bytes(raw)
        target=out/'r1-raw';target.mkdir(exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for name in z.namelist():
                assert '/' not in name and '\\' not in name and name.endswith('.json')
                (target/name).write_bytes(z.read(name))
        (out/'artifact-metadata.json').write_text(json.dumps(artifact,indent=2),encoding='utf-8')
        print('Downloaded public market data artifact; no credential exported')


if __name__=='__main__':main()
