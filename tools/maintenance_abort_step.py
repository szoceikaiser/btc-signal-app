"""One bounded maintenance step on an injected confirmed client. No CLI/token.

Caller authenticates quiescence evidence and pins this executor; never retry a
mutation on exception. A fresh invocation only inspects actually saved states.
"""
import json
import secrets
import aborted_maintenance as m
import github_delivery as g

def step(client, review):
    repo='szoceikaiser/btc-delivery-store'
    def read(branch,path):
        value=client.read(repo,branch,path)
        return {**value,'parents':client.parents(repo,value['commit_sha'])}
    stream=read('delivery-stream-live',g.STORE_PATH)
    fence=read('delivery-fence-live','delivery/actions-fence.json')
    decision=m.next_step(stream,fence,review)
    if decision=='takeover':
        g.review_takeover(client,repo,'delivery-stream-live','btc-signal-app-live-store-20261018',
            review['old_owner'],1801,m.takeover_evidence(review))
        return 'stream-confirmed; invoke fresh inspection before fence'
    if decision=='already-confirmed; no-write': return decision
    # Pin again using the existing envelope parser and confirmed-record locator.
    store=g.read_only(client,repo,'delivery-stream-live','btc-signal-app-live-store-20261018')
    if store._record != {k:v for k,v in stream.items() if k!='parents'}:
        raise g.StoreConflict('Stream moved during maintenance')
    candidate=m.close_candidate(json.loads(fence['body']),store._envelope,
        store.confirmed_record(),review,secrets.token_hex(16))
    # Uses the existing bounded CAS + independent parent/readback confirmation.
    client.fence_write({k:v for k,v in fence.items() if k!='parents'},candidate)
    final_stream=read('delivery-stream-live',g.STORE_PATH)
    final_fence=read('delivery-fence-live','delivery/actions-fence.json')
    if m.next_step(final_stream,final_fence,review)!='already-confirmed; no-write':
        raise g.StoreConflict('Final maintenance pair not confirmed')
    return 'aborted-confirmed; no send; triggers remain paused'
