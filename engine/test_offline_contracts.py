"""Regression boundaries for the preserved 4db rule contract and local rename."""
from copy import deepcopy
import os,tempfile
from pathlib import Path
from unittest.mock import patch
import public_access as public
import p3_backup_chain as backup
from test_free_public import access_for
from test_github_delivery import fails

def test_observed_never_keeps_unknown_fields_and_separate_bypass_review_required():
    repo='synthetic/rules';branch='stream'
    access,rules,sets=access_for({repo:{'id':123,'visibility':'public','branches':[branch]}})
    rid=rules[(repo,branch)][0]['ruleset_id']
    baseline=deepcopy((access,sets))
    class Client:
        def request(self,method,target,tail):
            assert method=='GET' and target==repo
            return deepcopy(rules[(repo,branch)] if '/rules/branches/' in tail else sets[(repo,rid)])
    client=Client()
    for value in ('never','always','pull_requests_only',None,False,True,0,{},['never']):
        access,sets=deepcopy(baseline);sets[(repo,rid)]['current_user_can_bypass']=value
        if value=='never':public.protection(client,access,repo,branch)
        else:fails(ValueError,lambda:public.protection(client,access,repo,branch))
    for mode in ('unknown-field','missing-proof','pending-proof','visible-bypass'):
        access,sets=deepcopy(baseline);sets[(repo,rid)]['current_user_can_bypass']='never'
        item=access['protections'][repo+'@'+branch]['rulesets'][str(rid)]
        if mode=='unknown-field':sets[(repo,rid)]['unreviewed_field']='never'
        if mode=='missing-proof':item.pop('bypass_review')
        if mode=='pending-proof':item['bypass_review']['status']='pending'
        if mode=='visible-bypass':sets[(repo,rid)]['bypass_actors']=[{'actor_id':1}]
        fails(ValueError,lambda:public.protection(client,access,repo,branch))

class Budget:
    def __init__(self):self.calls=0
    def check(self):self.calls+=1

def test_local_rename_denial_is_bounded_and_propagates():
    budget=Budget()
    with tempfile.TemporaryDirectory() as td:
        source=Path(td)/'source';source.mkdir();target=Path(td)/'target'
        with patch.object(Path,'rename',side_effect=PermissionError('synthetic lock')) as rename,patch.object(backup.time,'sleep') as sleep:
            fails(PermissionError,lambda:backup.publish_new(source,target,budget))
        assert rename.call_count==(10 if os.name=='nt' else 1)
        assert sleep.call_count==(9 if os.name=='nt' else 0)
        assert source.is_dir() and not target.exists()

def test_local_publication_never_overwrites_and_preserves_payload():
    with tempfile.TemporaryDirectory() as td:
        source=Path(td)/'source';source.mkdir();(source/'payload').write_bytes(b'synthetic verified bytes')
        target=Path(td)/'published';budget=Budget();backup.publish_new(source,target,budget)
        assert not source.exists() and (target/'payload').read_bytes()==b'synthetic verified bytes'
        source.mkdir();(source/'payload').write_bytes(b'other')
        fails(FileExistsError,lambda:backup.publish_new(source,target,budget))
        assert (target/'payload').read_bytes()==b'synthetic verified bytes' and source.exists()

def test_local_publication_expired_budget_stops_before_rename():
    class Expired:
        def check(self):raise ValueError('synthetic deadline')
    with patch.object(Path,'rename') as rename:
        fails(ValueError,lambda:backup.publish_new('source','target',Expired()))
        assert rename.call_count==0


def test_synthetic_runtime_pins_current_python_and_wrong_patch_still_stops():
    import json,sys
    from test_actions_delivery import fixture,invoke
    from production_contract import canonical
    with fixture() as (_,data,path,runtime,http):
        assert runtime['python_version']==list(sys.version_info[:3])
        runtime['python_version'][-1]+=1
        path.write_text(canonical(runtime),encoding='utf-8')
        try:invoke(path,data)
        except ValueError as exc:assert str(exc)=='Reviewed Python runtime differs'
        else:raise AssertionError('Wrong reviewed Python patch accepted')
        assert http.seen==[] and http.puts==0
