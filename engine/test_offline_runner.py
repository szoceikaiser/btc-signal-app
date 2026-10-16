"""Acceptance harness regressions: isolation and inherited network denial."""
import os,subprocess,sys
from pathlib import Path
_STATE='fresh'

def test_a_changes_are_confined_to_this_function():
    global _STATE
    assert _STATE=='fresh'
    _STATE='changed';os.environ['BTC_TEST_LEAK']='changed'
    Path('isolated-output.txt').write_text('synthetic only',encoding='utf-8')

def test_b_next_function_has_fresh_module_environment_and_output():
    assert _STATE=='fresh' and 'BTC_TEST_LEAK' not in os.environ
    assert not Path('isolated-output.txt').exists()

def test_descendant_python_and_node_cannot_open_sockets_even_with_clean_environment():
    child=subprocess.run([sys.executable,'-c',"import socket;socket.socket().connect(('127.0.0.1',9))"],env={},capture_output=True)
    assert child.returncode!=0 and b'Offline acceptance forbids actual network' in child.stderr,(child.returncode,child.stdout,child.stderr)
    node=os.environ['BTC_TEST_NODE'];assert Path(node).is_absolute() and Path(node).is_file()
    child=subprocess.run([node,'-e',"require('net').connect(9,'127.0.0.1')"],env={},capture_output=True)
    assert child.returncode!=0 and b'Offline acceptance forbids actual network' in child.stderr,(child.returncode,child.stdout,child.stderr)

def test_runner_environment_contains_only_synthetic_automatic_reader():
    import run_tests
    from unittest.mock import patch
    with patch.dict(os.environ,{'GITHUB_TOKEN':'DO-NOT-INHERIT','SOME_SECRET':'DO-NOT-INHERIT','BTC_DELIVERY_GITHUB_TOKEN':'DO-NOT-INHERIT','P3_PUBLIC_FIXTURE_INPUTS':'closed-session'}):
        env=run_tests.environment()
    assert env['GITHUB_TOKEN']=='offline-automatic-jobtoken'
    assert all('DO-NOT-INHERIT' not in str(v) for v in env.values())
    assert not any(k in env for k in ('SOME_SECRET','BTC_DELIVERY_GITHUB_TOKEN','P3_PUBLIC_FIXTURE_INPUTS'))
