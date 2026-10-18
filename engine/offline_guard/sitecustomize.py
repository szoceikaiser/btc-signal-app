"""Inherited offline boundary; fixture sitecustomize hooks are chained after it."""
import os,sys
from pathlib import Path
_installed=False

def install():
    global _installed
    if _installed:return
    _installed=True
    def audit(event,args):
        if event in ('socket.connect','socket.getaddrinfo','socket.sendto'):
            raise RuntimeError('Offline acceptance forbids actual network: '+event)
        if event=='subprocess.Popen':
            executable,argv,_,_=args
            words=[str(x) for x in argv] if isinstance(argv,(list,tuple)) else [str(argv)]
            if any(x in words for x in ('push','fetch','pull','ls-remote','clone')) and any('://' in x or '@github.com' in x for x in words):
                raise RuntimeError('Offline acceptance forbids external Git transport')
    sys.addaudithook(audit)
    import subprocess
    original=subprocess.Popen
    guard=str(Path(__file__).resolve().parent)
    class OfflineChild(original):
        def __init__(self,args,*pos,**kwargs):
            words=args if isinstance(args,(tuple,list)) else [args]
            exe=Path(str(words[0])).name.lower()
            if exe.startswith(('python','node')):
                env=dict(os.environ if kwargs.get('env') is None else kwargs['env'])
                for key in ('SYSTEMROOT','WINDIR'):
                    if key in os.environ:env.setdefault(key,os.environ[key])
                if exe.startswith('python'):
                    paths=env.get('PYTHONPATH','').split(os.pathsep)
                    env.update(BTC_OFFLINE_TEST='1',PYTHONPATH=os.pathsep.join([guard]+[x for x in paths if x and x!=guard]))
                else:
                    env['NODE_OPTIONS']='--require="'+(Path(guard)/'node_guard.cjs').as_posix()+'"'
                kwargs['env']=env
            super().__init__(args,*pos,**kwargs)
    subprocess.Popen=OfflineChild

if os.environ.get('BTC_OFFLINE_TEST')=='1':
    install()
    # Preserve explicit test fixture hooks while guarding their Python children.
    for entry in sys.path:
        candidate=Path(entry or '.')/'sitecustomize.py'
        if candidate.is_file() and candidate.resolve()!=Path(__file__).resolve():
            exec(compile(candidate.read_bytes(),str(candidate),'exec'),{'__file__':str(candidate),'__name__':'offline_fixture_sitecustomize'})
            break
