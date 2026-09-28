"""Every locally available historical report/configuration revision, by Git object."""
import hashlib,json,re
from pathlib import Path
from inventory import ROOT,OUT,git

def main():
    records=[];seen=set()
    for line in git('log','--all','--format=%H|%aI|%s','--','BACKTEST.md').splitlines():
        sha,when,subject=line.split('|',2)
        blob=git('rev-parse',sha+':BACKTEST.md').strip()
        if blob in seen: continue
        seen.add(blob)
        source=git('show',sha+':BACKTEST.md')
        section='';tables=[]
        for num,text in enumerate(source.splitlines(),1):
            if text.startswith('#'):section=text
            if text.startswith('|'):
                tables.append(dict(line=num,section=section,cells=[c.strip() for c in text.strip('|').split('|')]))
        records.append(dict(commit=sha,date=when,subject=subject,blob=blob,
            sha256=hashlib.sha256(source.encode()).hexdigest(),header=source.splitlines()[:8],tables=tables))
    configs=[]
    for line in git('log','--all','--format=%H|%aI|%s','--','site/data/config.json').splitlines():
        sha,when,subject=line.split('|',2)
        configs.append(dict(commit=sha,date=when,subject=subject,
                            config=json.loads(git('show',sha+':site/data/config.json'))))
    paths=git('log','--all','--name-only','--format=','--','*.json').splitlines()
    result=dict(reports=records,configurations=configs,all_historical_json_paths=sorted(set(paths)-{''}),
                reproduction_limit='Report text and configuration are not original input data. Full reconstruction requires original OHLC and flow series, recorded retrieval/availability times and original code.')
    (OUT/'historie.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Unique historical BACKTEST reports',len(records),'configuration revisions',len(configs))
    print('JSON input candidates:',*[x for x in result['all_historical_json_paths'] if any(k in x for k in ('eingaben','archiv','probe','history'))],sep='\n')

if __name__=='__main__':main()
