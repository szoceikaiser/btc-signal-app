"""Test-only immutable Git object reader, scoped to one acceptance process.

Reads real local Git objects via one cat-file process. It never caches HEAD,
status, worktree files, fixture repositories, or a mutable ref. No validator is
replaced; historical hashes still compare against the actual object bytes.
"""
import atexit,re,subprocess,threading
from pathlib import Path
_INSTALLED=False

def install():
    global _INSTALLED
    if _INSTALLED:return
    _INSTALLED=True
    import p3_reader401_continue as c
    import p3_github_probe as p
    original=c.git;root=p.ROOT.resolve();cache={};lock=threading.Lock();child=None
    def close():
        nonlocal child
        if child is not None:
            child.stdin.close()
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()
            child.stdout.close();child.stderr.close();child=None
    atexit.register(close)
    def git(directory,*args):
        nonlocal child
        if Path(directory).resolve()!=root:return original(directory,*args)
        blob=(len(args)==2 and args[0]=='show' and re.fullmatch(r'[0-9a-f]{40}:[^\r\n]+',args[1]))
        immutable=(blob or len(args)==2 and args[0]=='rev-parse' and re.fullmatch(r'[0-9a-f]{40}\^\{tree\}',args[1]) or len(args)==4 and args[:2] in (('diff','--name-only'),('merge-base','--is-ancestor')) and all(re.fullmatch('[0-9a-f]{40}',x) for x in args[2:]))
        if not immutable:return original(directory,*args)
        with lock:
            if args in cache:return cache[args]
            if blob:
                if child is None:
                    child=subprocess.Popen(['git','-c','safe.directory='+root.as_posix(),'-C',str(root),'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=p.git_environment())
                child.stdin.write((args[1]+'\n').encode());child.stdin.flush();head=child.stdout.readline(256).split()
                if len(head)!=3 or head[1]!=b'blob':raise subprocess.CalledProcessError(128,['git','show',args[1]])
                size=int(head[2])
                if not 0<=size<=2*1024*1024:raise ValueError('Offline code object byte bound')
                raw=child.stdout.read(size)
                if len(raw)!=size or child.stdout.read(1)!=b'\n':raise ValueError('Short offline code object')
            else:raw=original(directory,*args)
            cache[args]=raw;return raw
    c.git=git
