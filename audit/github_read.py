"""Read-only metadata for this repository. Credentials never printed or saved."""
import argparse,json,os,subprocess,urllib.request
from datetime import datetime,timezone
from inventory import ROOT,OUT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--final',action='store_true',help='Save a separate final snapshot')
    parser.add_argument('--no-write',action='store_true',help='Read-only CI confirmation without changing artifacts')
    args=parser.parse_args()
    credential=subprocess.run(['git','-c',f'safe.directory={ROOT.as_posix()}','credential','fill'],input='protocol=https\nhost=github.com\n\n',
        capture_output=True,text=True,check=True,env={**os.environ,'GIT_TERMINAL_PROMPT':'0'})
    fields=dict(line.split('=',1) for line in credential.stdout.splitlines() if '=' in line)
    token=fields.get('password')
    def get(path):
        headers={'Accept':'application/vnd.github+json','User-Agent':'btc-independent-audit',
                 'X-GitHub-Api-Version':'2022-11-28'}
        if token:headers['Authorization']='Bearer '+token
        req=urllib.request.Request('https://api.github.com/repos/szoceikaiser/btc-signal-app'+path,headers=headers)
        with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
    repo=get('')
    result=dict(repository=repo['full_name'],permissions=repo.get('permissions'),
                main=get('/branches/main'),branches=get('/branches?per_page=100'),
                workflows=get('/actions/workflows'),artifacts=get('/actions/artifacts?per_page=100'),
                runs=get('/actions/runs?per_page=100'))
    result['retrieved_at']=datetime.now(timezone.utc).isoformat()
    result['compare_frozen_main']=get('/compare/89885adc9fb6d2eae60f7a64f9452760a4e33cd9...'+result['main']['commit']['sha'])
    if not args.no_write:
        name='github-abschluss.json' if args.final else 'github-metadaten.json'
        (OUT/name).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('permissions',result['permissions'],'artifacts',result['artifacts']['total_count'],
          'runs',len(result['runs']['workflow_runs']),'main',result['main']['commit']['sha'])
    print('Changed from frozen main:',[f['filename'] for f in result['compare_frozen_main'].get('files',[])])
    print('Audit runs:',[(r['id'],r['name'],r['head_sha'],r['status'],r['conclusion'])
          for r in result['runs']['workflow_runs'] if r['head_branch']=='codex/audit-2026-09-27'])

if __name__=='__main__':main()
