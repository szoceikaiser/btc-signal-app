"""Synthetic repeated real CLI calls; Linux AS measurements, no remote access."""
import argparse,json,platform,sys,threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
import test_hosted_backup as tests
import p3_backup_chain as b


def sample(label):
    row={'label':label,'threads':len(threading.enumerate())}
    if sys.platform=='linux':
        import resource
        row['rlimit_as']=list(resource.getrlimit(resource.RLIMIT_AS))
        fields=('VmPeak','VmSize','VmRSS','VmData','VmStk','Threads')
        row['proc_status']={k:v.strip() for line in Path('/proc/self/status').read_text().splitlines()
                            for k,_,v in [line.partition(':')] if k in fields}
        row['mappings']=sum(1 for _ in Path('/proc/self/maps').open())
    return row


def main(out):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    result={'python':sys.version,'platform':platform.platform(),'linux_limit_measured':sys.platform=='linux',
            'cli_calls':0,'confirmed':0,'samples':[sample('before')]}
    for index in range(3):
        provider=tests.Provider(out/str(index))
        for role in ('producer','verifier'):
            receipt,_=provider.invoke(role)
            result['cli_calls']+=1;result['confirmed']+=bool(receipt['upload_readback_verified'])
            row=sample(str(index)+'-'+role);result['samples'].append(row)
            if sys.platform=='linux':assert row['rlimit_as']==[b.MAX_PYTHON_RSS]*2,row
            assert row['threads']==result['samples'][0]['threads'],row
            print('MEMORY_SAMPLE '+json.dumps(row),flush=True)
    (out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result),flush=True)
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',required=True)
    sys.exit(main(parser.parse_args().out))
