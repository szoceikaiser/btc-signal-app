"""Bounded allocation and fail-closed regressions for the Linux repair."""
import io,json,os,subprocess,sys,threading
from pathlib import Path
from unittest.mock import patch
import p3_backup_chain as b
import p4_hosted_backup as h
from test_github_delivery import fails
OUT=None


def test_chunk_reader_exact_eof_short_reads_and_excess_byte():
    class Short(io.BytesIO):
        def read(self,n):
            assert 0<n<=65536,n
            return super().read(min(n,7))
    for size in (0,1,65536,65539):
        raw=b'x'*size
        assert b.read_bounded(Short(raw),size)==raw
        assert b.read_bounded(Short(raw),64*h.MIB)==raw
        fails(ValueError,lambda:b.read_bounded(Short(raw+b'x'),size))
    fails(ValueError,lambda:b.read_bounded(Short(b''),-1))


def test_real_pipe_uses_small_reads_and_reaps_oversize_child():
    root=Path(OUT);b.git(root,b.Budget(),'init','--bare')
    with b.process(root,['hash-object','--stdin'],b.Budget()) as proc:
        proc.stdin.write(b'synthetic');proc.stdin.close()
        assert len(b.read_bounded(proc.stdout,41))==41
    with b.process(root,['hash-object','--stdin'],b.Budget()) as proc:
        proc.stdin.close()
        fails(ValueError,lambda:b.read_bounded(proc.stdout,3))
    assert proc.poll() is not None


def test_wire_short_reads_repeated_workers_and_oversize_fail_closed():
    class Short(io.BytesIO):
        headers={};status=200
        def read(self,n):
            assert n<=65536
            return super().read(min(n,3))
    budget=h.Budget(OUT);client=h.Client('offline',{'synthetic/repo'},set(),budget)
    before={t.ident for t in threading.enumerate()}
    with patch.object(h.Client,'open_request',side_effect=lambda *a,**k:Short(b'{"ok":true}')):
        for _ in range(12):assert client.request('GET','synthetic/repo','/git/ref/heads/main')=={'ok':True}
    assert {t.ident for t in threading.enumerate()}==before
    with patch.object(h.Client,'open_request',return_value=Short(b'xxxxx')):
        fails(ValueError,lambda:h.wire(client,object(),budget,4))


def test_repeated_real_cli_memory_probe_keeps_production_limit():
    root=Path(__file__).resolve().parents[1]
    proc=subprocess.run([sys.executable,'-B',str(root/'tools/linux_memory_probe.py'),
                         '--out',str(Path(OUT)/'probe')],capture_output=True,timeout=180)
    assert proc.returncode==0,(proc.stdout[-4000:],proc.stderr[-4000:])
    result=json.loads((Path(OUT)/'probe/RESULT.json').read_text())
    assert result['cli_calls']==6 and result['confirmed']==6
    assert result['linux_limit_measured']==(sys.platform=='linux')
    if sys.platform=='linux':
        assert all(row['rlimit_as']==[256*h.MIB]*2 for row in result['samples'][1:])


def test_public_lock_preflight_does_not_create_or_change_session():
    import p3_public_root as u
    root=Path(OUT);plan={'journal_directory':str(root)}
    fails(FileNotFoundError,lambda:u.check_existing_kernel_lock(plan))
    assert not list(root.iterdir())
    lock=root/'probe-session.lock';lock.write_bytes(b'0')
    u.check_existing_kernel_lock(plan)
    with lock.open('r+b') as handle:
        if os.name=='nt':
            import msvcrt;msvcrt.locking(handle.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl;fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fails(OSError,lambda:u.check_existing_kernel_lock(plan))
    assert list(root.iterdir())==[lock] and lock.read_bytes()==b'0'
