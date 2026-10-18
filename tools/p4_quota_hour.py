"""One synthetic contiguous hour from actual offline CLI request transcripts.

Volume replay, not a provider/timing guarantee or long-running market campaign.
Monitor samples conservatively repeat the complete healthy path, independently
reading all evidence each time. No observation-local cache crosses jobs.
"""
import argparse
from collections import Counter
import json
from pathlib import Path


def model(root):
    root=Path(root)
    load=lambda n:json.loads((root/(n+'.json')).read_text())
    entries=load('ENTRIES-PAGES');pair=load('PAIR-COUNTS');monitor=load('MONITOR-CLI')
    if monitor['exit']!=0 or monitor['result']['http_status']!=200: raise ValueError('Full healthy CLI proof required')
    events=[]
    for item in entries['events']:
        events.append({'minute':item['minute'],'kind':item['kind'],'rows':item['entry']})
        events.append({'minute':item['minute']+.1,'kind':'pages','rows':item['pages']})
    if Counter(i['kind'] for i in entries['events'])!={'signal':2,'watch':4,'lage':1}: raise ValueError('Hour obligations differ')
    # Pair transcript preserves its real producer/verifier ordering and separate
    # token roles. No new 1000-request allowance for the second job.
    boundary=next(i for i,r in enumerate(pair['requests']) if r.get('phase')=='verifier')
    events.extend([{'minute':0,'kind':'producer','rows':pair['requests'][:boundary]},
                   {'minute':1,'kind':'verifier','rows':pair['requests'][boundary:]}])
    for minute in range(5,61,5): events.append({'minute':minute,'kind':'monitor','rows':monitor['requests']})
    events.sort(key=lambda e:e['minute'])
    counts=Counter();by_kind={};trace=[];used=0
    for event in events:
        local=Counter(r['pool'] for r in event['rows']);counts.update(local)
        by_kind.setdefault(event['kind'],Counter()).update(local)
        for row in event['rows']:
            if row['pool']=='automatic-core': used+=1
            trace.append({'minute':event['minute'],'job':event['kind'],**row,
                'shared_automatic_used':used,'shared_automatic_remaining':1000-used})
            if used>1000: raise ValueError('Shared automatic quota exhausted')
    jobs=len(events)
    # Explicit platform allowances, not offline measurements of Action internals.
    # Fixed checkout ref + required Git means no REST archive fallback is intended.
    # Keep 2 core/job for checkout/metadata, plus 8 core/Pages job for configure,
    # artifact lookup, deployment and bounded polling (20s / 10s / 1 error).
    checkout_reserve=jobs*2;pages_reserve=7*8
    total=used+checkout_reserve+pages_reserve
    if total>900: raise ValueError('Less than 10 percent automatic quota reserve')
    burst=Counter()
    for row in trace:
        if row['pool'] in ('automatic-core','writer-core'): burst[int(row['minute'])]+=1
    return {'schema':'btc-quota-hour-v1','offline_only':True,'provider_proof':False,
        'model':'60 minute request-volume replay of actual complete CLI paths; no cross-job cache',
        'jobs':jobs,'obligations':{'watch':4,'signal':2,'lage':1,'pages':7,'monitor':12,'producer':1,'verifier':1},
        'counts':dict(counts),'by_kind':{k:dict(v) for k,v in by_kind.items()},
        'bootstrap_non_rest_git_http_allowance':{'per_job':9,'all_jobs':jobs*9,
            'status':'Allowance for bounded shallow Git checkout and Action internal fetch retries; not a measured transport proof'},
        'maximum_synthetic_minute_rest_operations':max(burst.values()),
        'automatic_shared_repository_hour':{'limit':1000,'measured_cli_core':used,
            'checkout_and_code_metadata_allowance':checkout_reserve,'pages_service_allowance':pages_reserve,
            'planned_total':total,'reserve':1000-total,'reset_policy':'No local time-based allowance renewal; provider headers decide'},
        'writer_core':{'operations':counts['writer-core'],'scope':'separate sender/backup/receipt roles; real credential pool/limits pending'},
        'conservative_all_rest_and_allowances':total+counts['writer-core'],
        'non_rest_attribution':'Git upload-pack and pinned raw quota attribution/support pending real provider proof',
        'secondary_limits':'No availability guarantee. Any 403/429/Retry-After stops without retry or deadline shift.',
        'platform_allowance_status':'Conservative installation allowances; actual pinned Action calls/polling still require provider confirmation',
        'trace':trace}


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',required=True);p.add_argument('--out',required=True);a=p.parse_args()
    with Path(a.out).open('x',encoding='utf-8') as f: json.dump(model(a.evidence),f,indent=2)
