"""Two genuine processes, real atomic Git CAS and durable object history. No network."""
import json,os,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'engine'),str(ROOT/'tools')]
from github_recovery_journal import Journal
from production_contract import canonical

def git(repo,*args,input=None,check=True):
    env={**os.environ,'GIT_AUTHOR_NAME':'Synthetic','GIT_AUTHOR_EMAIL':'synthetic@example.invalid',
         'GIT_COMMITTER_NAME':'Synthetic','GIT_COMMITTER_EMAIL':'synthetic@example.invalid'}
    return subprocess.run(['git','-C',str(repo),*args],input=input,capture_output=True,check=check,env=env)

def read(repo):
    head=git(repo,'rev-parse','refs/heads/journal').stdout.strip().decode()
    body=git(repo,'show',head+':state.json',check=False)
    if body.returncode:return head,None
    blob=git(repo,'rev-parse',head+':state.json').stdout.strip().decode()
    return head,[blob,json.loads(body.stdout)]

def worker(directory,identity):
    repo=Path(directory)
    class Remote:
        def read(self,path):return read(repo)[1]
        def cas(self,path,blob,value):
            head,row=read(repo)
            if blob!=(row[0] if row else None):raise ValueError('Synthetic CAS conflict')
            if identity.startswith('parallel-') and len(value['leases'])==1:
                (repo.parent/identity).touch()
                end=time.monotonic()+5
                while not all((repo.parent/k).exists() for k in ('parallel-A','parallel-B')):
                    if time.monotonic()>end:raise ValueError('Parallel barrier deadline')
                    time.sleep(.01)
            raw=canonical(value).encode()
            oid=git(repo,'hash-object','-w','--stdin',input=raw).stdout.strip().decode()
            tree=git(repo,'mktree',input=('100644 blob '+oid+'\tstate.json\n').encode()).stdout.strip().decode()
            commit=git(repo,'commit-tree',tree,'-p',head,input=b'synthetic CAS\n').stdout.strip().decode()
            git(repo,'update-ref','refs/heads/journal',commit,head)
    journal=Journal(Remote(),'a'*40,'b'*64,200000,lambda:1000)
    try:
        journal.acquire({'identity':identity})
        journal.reserve_write('stream',{'commit_sha':'c'*40},{'synthetic':True})
        return 0
    except ValueError:return 23

def run():
    with tempfile.TemporaryDirectory() as td:
        repo=Path(td)/'journal.git';repo.mkdir();git(repo,'init','--bare')
        tree=git(repo,'mktree',input=b'').stdout.strip().decode()
        seed=git(repo,'commit-tree',tree,input=b'synthetic seed\n').stdout.strip().decode()
        git(repo,'update-ref','refs/heads/journal',seed)
        children=[]
        try:
            for identity in ('parallel-A','parallel-B'):
                children.append(subprocess.Popen([sys.executable,'-B',__file__,'--worker',str(repo),identity],stdout=subprocess.PIPE,stderr=subprocess.PIPE))
            codes=[]
            for child in children:
                out,err=child.communicate(timeout=15);codes.append(child.returncode)
                assert child.returncode in (0,23),(out,err)
            assert sorted(codes)==[0,23],codes
            for identity in ('restart-C','restart-D','exhausted-E'):
                p=subprocess.run([sys.executable,'-B',__file__,'--worker',str(repo),identity],capture_output=True,timeout=15)
                assert p.returncode==23,(p.stdout,p.stderr)
            _,row=read(repo);value=row[1]
            assert len(value['leases'])==3 and value['reserved_gets']==384
            assert list(value['writes'])==['stream']
            print('PASS two real processes: one atomic Git-CAS winner; one conflict; exactly one durable write reservation')
            print('PASS independent restart, three leases exhausted, no budget reset; all processes ended')
        finally:
            for child in children:
                if child.poll() is None:child.kill();child.communicate(timeout=5)

if __name__=='__main__':
    if '--worker' in sys.argv:raise SystemExit(worker(sys.argv[2],sys.argv[3]))
    run()
