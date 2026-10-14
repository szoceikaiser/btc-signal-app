"""Offline maintainer tool: write disabled Free review templates, never activate."""
import json
from copy import deepcopy
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OPS=ROOT/'ops/produktion'
STORE='szoceikaiser/btc-delivery-store'
BACKUP='szoceikaiser/btc-delivery-backup'
RECEIPT='szoceikaiser/btc-delivery-backup-verification'
CODE='szoceikaiser/btc-signal-app'


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')


def main():
    repos={STORE:['delivery-stream-v2','delivery-fence-v2','reviewed-migration'],
           BACKUP:['verified-pair-packages'],RECEIPT:['verified-receipts'],CODE:['main']}
    access={'schema':'btc-public-access-v1','enabled':False,
        'repositories':{r:{'id':None,'visibility':'public','branches':branches} for r,branches in repos.items()},
        'protections':{},'credential_reviews':{}}
    for repo,branches in repos.items():
        for branch in branches:
            if branch in ('main','reviewed-migration'): continue
            access['protections'][repo+'@'+branch]={'repository':repo,'repository_id':None,
                'branch':branch,'active_rules_sha256':None,'rulesets':{}}
    for role,repo,branches in (('sender_write',STORE,repos[STORE][:2]),
            ('backup_write',BACKUP,repos[BACKUP]),('receipt_write',RECEIPT,repos[RECEIPT])):
        access['credential_reviews'][role]={'schema':'btc-writer-review-v1','status':'pending',
            'role':role,'repository_id':None,'credential_type':None,'credential_reference':None,'repositories':[repo],
            'branches':branches,'permissions':{'contents':'write','metadata':'read'},
            'other_repository_write':None,'reviewer':None,'reviewed_at':None,'evidence_sha256':None,'sha256':None}
    write(OPS/'public-access.disabled.json',access)
    write(OPS/'public-bypass-review.disabled.json',{'schema':'btc-bypass-review-v1','status':'pending',
        'repository':None,'repository_id':None,'branch':None,'ruleset_id':None,'public_sha256':None,
        'bypass_actors':None,'reviewer':None,'reviewed_at':None,'evidence_sha256':None,'sha256':None})
    write(OPS/'public-ruleset.disabled.json',{'name':'REVIEW exact branch only','target':'branch',
        'enforcement':'disabled','bypass_actors':[],
        'conditions':{'ref_name':{'include':['refs/heads/REVIEW_EXACT_BRANCH'],'exclude':[]}},
        'rules':[{'type':t} for t in ('deletion','non_fast_forward','required_linear_history')]})
    for name in ('github-actions-runtime','pages-runtime','monitor-runtime','hosted-backup-runtime'):
        p=OPS/(name+'.disabled.json');r=json.loads(p.read_text())
        r['public_access']=deepcopy(access)
        d=r.get('deployment',r)
        d['public_access_sha256']=None
        d['private_store_repository']=STORE  # retained wire key, explicitly public in public_access
        d['store_branch']='delivery-stream-v2';d['fence_branch']='delivery-fence-v2'
        if 'token_scope' in r: r['token_scope']='anonymous data GET; separate reviewed writer only; GITHUB_TOKEN for codejob metadata'
        if name=='github-actions-runtime':
            r['private_backup_repository']=BACKUP
        if name=='hosted-backup-runtime':
            r['migration']['target']={'repository':STORE,'id':None,'branch':'reviewed-migration'}
        if name=='monitor-runtime':
            r['backup_target'].update(repository=BACKUP,branch='verified-pair-packages')
            r['independent_verifier'].update(repository=RECEIPT,receipt_branch='verified-receipts')
        write(p,r)
    for kind in ('signal','watch','lage','backup','backup-verify','pages','monitor'):
        p=OPS/(kind+'-workflow.disabled.yml');lines=p.read_text().splitlines()
        removed=('BTC_HOSTED_SOURCE_READ_TOKEN:','BTC_HOSTED_BACKUP_READ_TOKEN:','BTC_HOSTED_RECEIPT_READ_TOKEN:',
                 'BTC_PAGES_STORE_READ_TOKEN:','BTC_MONITOR_STORE_READ_TOKEN:','BTC_MONITOR_BACKUP_READ_TOKEN:')
        lines=[line for line in lines if not any(key in line for key in removed)]
        start=next(i for i,line in enumerate(lines) if 'uses: actions/checkout@' in line or 'name: Bounded anonymous public code checkout' in line)
        end=next(i for i in range(start+1,len(lines)) if lines[i].startswith('      - '))
        codevar=('BTC_HOSTED_CODE_SHA' if kind in ('backup','backup-verify') else
                 'BTC_MONITOR_CODE_SHA' if kind=='monitor' else 'BTC_PRODUCTION_CODE_SHA')
        bootstrap=(ROOT/'tools/public_code_checkout.py').read_text().splitlines()
        lines[start:end]=['      - name: Bounded anonymous public code checkout',
            '        env:',
            '          BTC_PUBLIC_CODE_SHA: ${{ vars.'+codevar+' }}',
            '          BTC_PUBLIC_CODE_REPOSITORY_ID: ${{ vars.BTC_PUBLIC_CODE_REPOSITORY_ID }}',
            '        run: |',"          python3 - <<'PY'",*['          '+line if line else '' for line in bootstrap],'          PY']
        for i,line in enumerate(lines):
            if any(key in line for key in ('BTC_ACTIONS_METADATA_READ_TOKEN:','BTC_HOSTED_METADATA_READ_TOKEN:',
                       'BTC_PAGES_METADATA_READ_TOKEN:','BTC_MONITOR_ACTIONS_READ_TOKEN:')):
                lines[i]=line[:len(line)-len(line.lstrip())]+'GITHUB_TOKEN: ${{ github.token }}'
        prefix='# Free/public: explicit IDs and actual rules/credential reviews still required.'
        lines=[line for line in lines if line!=prefix]
        p.write_text(prefix+'\n'+'\n'.join(lines)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__': main()
