"""Empty GitHub destinations are identified by authenticated commit bytes only.

No HTTP failure, missing commit or nonempty-tree validation may be accepted as
an empty inventory. Publication integration uses real local Git databases in
test_hosted_backup with a provider fake that refuses empty-tree API requests.
"""
from pathlib import Path
from unittest.mock import patch
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'engine')]
import p4_hosted_backup as h
from test_github_delivery import fails

ARTIFACT_ROOT=None
EMPTY='4b825dc642cb6eb9a060e54bf8d69288fbee4904'
PIN='a'*40
TARGET={'repository':'synthetic/backup','branch':'packages','id':2}


def client(name):
    root=Path(ARTIFACT_ROOT)/name;root.mkdir(parents=True)
    return h.Client('synthetic-writer',{'synthetic/backup'},{'synthetic/backup'},h.Budget(root))


def test_empty_tree_requires_matching_authenticated_commit_and_no_tree_request():
    assert h.oid('tree',b'')==EMPTY
    c=client('exact-empty');calls=[]
    def request(method,repo,tail,*args,**kwargs):
        calls.append((method,repo,tail))
        assert (method,repo,tail)==('GET',TARGET['repository'],'/git/commits/'+PIN)
        return {'sha':PIN,'tree':{'sha':EMPTY},'parents':[]}
    with patch.object(c,'request',side_effect=request):assert c.tree(TARGET,PIN)==(EMPTY,{})
    assert len(calls)==1 and not c.blob_paths and not c.blob_cache


def test_empty_tree_cannot_bypass_missing_commit_wrong_commit_or_scope():
    c=client('bad-commit')
    for value in ({'sha':'b'*40,'tree':{'sha':EMPTY}}, {'sha':PIN,'tree':{'sha':'invalid'}}):
        with patch.object(c,'request',return_value=value):fails(ValueError,lambda:c.tree(TARGET,PIN))
    with patch.object(c,'request',side_effect=h.Inaccessible('Missing pinned commit')):
        fails(h.Inaccessible,lambda:c.tree(TARGET,PIN))
    # Real request scope checks must run before any well-known-tree admission.
    with patch.object(c,'open_request',side_effect=AssertionError('Network forbidden')) as opened:
        fails(ValueError,lambda:c.tree({**TARGET,'repository':'foreign/repo'},PIN))
        fails(ValueError,lambda:c.tree(TARGET,'invalid'))
        assert not opened.called


def test_nonempty_tree_read_errors_never_become_empty_inventory():
    c=client('inaccessible-nonempty');tree='b'*40
    for error in (h.Inaccessible('404 nonempty'),RuntimeError('403 nonempty'),TimeoutError('unconfirmed')):
        calls=[]
        def request(method,repo,tail,*args,**kwargs):
            calls.append(tail)
            if tail=='/git/commits/'+PIN:return {'sha':PIN,'tree':{'sha':tree}}
            assert tail=='/git/trees/'+tree+'?recursive=1';raise error
        with patch.object(c,'request',side_effect=request):fails(type(error),lambda:c.tree(TARGET,PIN))
        assert len(calls)==2


def test_nonempty_tree_still_checks_truncation_paths_modes_and_complete_hash():
    c=client('invalid-nonempty');blob=h.oid('blob',b'actual file')
    tree=h.tree_oid({'kept.txt':{'sha':blob,'bytes':11}})
    good={'path':'kept.txt','mode':'100644','type':'blob','sha':blob,'size':11}
    bodies=[{'sha':tree,'truncated':True,'tree':[good]},
            {'sha':tree,'truncated':False,'tree':[]},
            {'sha':tree,'truncated':False,'tree':[{**good,'mode':'120000'}]},
            {'sha':tree,'truncated':False,'tree':[{**good,'path':'../escape'}]},
            {'sha':'c'*40,'truncated':False,'tree':[good]}]
    for body in bodies:
        with patch.object(c,'request',side_effect=[{'sha':PIN,'tree':{'sha':tree}},body]):
            fails(ValueError,lambda:c.tree(TARGET,PIN))
