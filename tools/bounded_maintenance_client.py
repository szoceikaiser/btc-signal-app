"""Persistent two-PUT capability. No credential discovery or executable CLI."""
import base64
import json
from pathlib import Path
import re
import sqlite3
import time
import urllib.parse
from contextlib import contextmanager
import aborted_maintenance as m
import github_delivery as g
from production_contract import canonical, digest

REPO='szoceikaiser/btc-delivery-store'
STREAM='delivery-stream-live'; FENCE='delivery-fence-live'

class Client(g.GitHubContentsClient):
    confirmation_attempts=3
    def __init__(self,token,journal,review,opener,clock=None):
        super().__init__(token,timeout=3)
        self.clock=clock or time.time; self.path=Path(journal); self.review=review
        m.review_evidence(review)
        self.open_request=opener; self._capability=None
        with self.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS operation (review TEXT PRIMARY KEY, deadline REAL, gets INTEGER, bytes INTEGER)')
            db.execute('CREATE TABLE IF NOT EXISTS writes (branch TEXT PRIMARY KEY, body TEXT, status TEXT)')
            rows=db.execute('SELECT review FROM operation').fetchall()
            if rows and rows!=[(digest(review),)]: raise g.StoreConflict('Foreign maintenance journal')
            db.execute('INSERT OR IGNORE INTO operation VALUES (?, ?,0,0)',(digest(review),self.clock()+900))
    @contextmanager
    def db(self):
        db=sqlite3.connect(self.path,timeout=0)
        try:
            db.execute('PRAGMA synchronous=FULL')
            with db: yield db
        finally: db.close()
    def _request(self,method,route,payload=None):
        prefix=self._route(REPO,'');tail=route.removeprefix(prefix)
        if not route.startswith(prefix+'/'): raise g.StoreConflict('Maintenance route refused')
        branch=None
        if method=='GET':
            good=(tail in ('/git/ref/heads/'+STREAM,'/git/ref/heads/'+FENCE)
                or re.fullmatch(r'/git/commits/[0-9a-f]{40}',tail)
                or re.fullmatch(r'/contents/delivery/(stream|actions-fence)\.json\?ref=[0-9a-f]{40}',tail))
            if not good: raise g.StoreConflict('Maintenance read scope refused')
        elif method=='PUT' and self._capability:
            branch=self._capability
            expected='/contents/'+(g.STORE_PATH if branch==STREAM else 'delivery/actions-fence.json')
            if tail!=expected or payload.get('branch')!=branch or not payload.get('sha'):
                raise g.StoreConflict('Maintenance write scope refused')
        else: raise g.StoreConflict('Maintenance method refused')
        raw=canonical(payload).encode() if payload else b''
        if len(raw)>1100*1024: raise g.StoreUnavailable('Maintenance request limit')
        with self.db() as db:
            db.execute('BEGIN IMMEDIATE')
            deadline,gets,used=db.execute('SELECT deadline,gets,bytes FROM operation').fetchone()
            if self.clock()>=deadline or gets>=192 or used+len(raw)+2*1024*1024>384*1024*1024:
                raise g.StoreUnavailable('Maintenance operation budget')
            if branch:
                try: db.execute('INSERT INTO writes VALUES (?, ?, ?)',(branch,digest(payload),'reserved'))
                except sqlite3.IntegrityError: raise g.StoreConflict('Write already reserved; independently read first') from None
            db.execute('UPDATE operation SET gets=?,bytes=?',(gets+(method=='GET'),used+len(raw)+2*1024*1024))
        # Reservation survives lost response/process death. Never retry a PUT.
        return super()._request(method,route,payload)
    def locator(self,record):
        env=json.loads(record['body'])
        return dict(adapter='github',repo=REPO,branch=STREAM,path=g.STORE_PATH,
            store_id=env['store_id'],revision=env['revision'],commit_sha=record['commit_sha'],
            blob_sha=record['blob_sha'],snapshot_digest=env['body_digest'])
    def update(self,repo,branch,blob,body,write_id,path=g.STORE_PATH):
        if (repo,branch,path)!=(REPO,STREAM,g.STORE_PATH): raise g.StoreConflict('Stream capability refused')
        old=self.read(REPO,STREAM);fence=self.read(REPO,FENCE,'delivery/actions-fence.json')
        m.preflight(old,fence,self.review)
        if blob!=old['blob_sha']: raise g.StoreConflict('Stream moved')
        env=json.loads(body)
        fake={**old,'body':body,'blob_sha':g.hashlib.sha1(b'blob '+str(len(body)).encode()+b'\0'+body).hexdigest(),'commit_sha':'a'*40}
        m.close_candidate(json.loads(fence['body']),env,self.locator(fake),self.review,'validation-only')
        self._capability=STREAM
        try: return super().update(repo,branch,blob,body,write_id,path)
        finally: self._capability=None
    def fence_write(self,old,value):
        stream=self.read(REPO,STREAM);current=self.read(REPO,FENCE,'delivery/actions-fence.json')
        if current!=old: raise g.StoreConflict('Fence moved')
        m.validate_pair(value,json.loads(stream['body']),self.locator(stream))
        raw=canonical(value).encode()
        payload=dict(message='aborted maintenance '+value['write_id'],branch=FENCE,sha=old['blob_sha'],content=base64.b64encode(raw).decode())
        self._capability=FENCE
        try:
            try: self._request('PUT',self._route(REPO,'/contents/delivery/actions-fence.json'),payload)
            except g.StoreUnavailable: pass
        finally: self._capability=None
        for _ in range(3):
            observed=self.read(REPO,FENCE,'delivery/actions-fence.json')
            if observed['body']==raw and self.parents(REPO,observed['commit_sha'])==[old['commit_sha']]:
                final=self.read(REPO,FENCE,'delivery/actions-fence.json')
                if final==observed: return observed
        raise g.StoreConflict('Fence outcome unknown; independently inspect; no retry')
