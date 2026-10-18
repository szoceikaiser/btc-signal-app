"""P2 O: backup/restore, positive evidence, negative health, public allowlist."""
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from datetime import datetime,timezone
from unittest.mock import patch

import durable_delivery as durable
import main
import telegram_notify as tg
from test_production_runtime import seeded, active, expect
import produktion_backup as backup
import produktion_export as export
import produktion_health as health
import produktion_reconcile as reconcile


def test_consistent_backup_restore_is_blocked_and_hash_checked():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);store,data,paths=seeded(root)
        out=root/'backup'; restored=root/'restored'
        manifest=backup.backup(store,'synthetic-store',paths[-1],out)
        assert manifest['revision']==0
        checked,_=backup.verify_backup(out)
        assert checked==manifest
        result=backup.restore(out,restored)
        assert result['mode']=='blocked' and result['restore_requires_reconciliation']
        with durable.VolumeStore(restored,'synthetic-store') as volume:
            assert volume.snapshot['control']['mode']=='blocked'
            assert volume.snapshot['control']['health']['restore_requires_reconciliation']
        expect(FileExistsError,lambda:backup.restore(out,restored))
        # A backup source cannot be copied while another owner holds the lock.
        with durable.VolumeStore(store,'synthetic-store'):
            expect(sqlite3.OperationalError,lambda:backup.backup(store,'synthetic-store',paths[-1],root/'busy'))
        assert not (root/'busy').exists()
        (out/'snapshot.v2.json').write_bytes((out/'snapshot.v2.json').read_bytes()+b' ')
        expect(ValueError,lambda:backup.restore(out,root/'invalid'))


def test_positive_reconciliation_requires_exact_review_and_revision():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);store,data,_=seeded(root)
        with active(root,store,data),patch.object(tg,'deliver_telegram',side_effect=TimeoutError('synthetic')):
            main.send_testnachricht(data_dir=data)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            rev=volume.revision
            m=next(iter(volume.snapshot['commands'].values()))['_delivery']['messages'][0].copy()
        proof=root/'proof.bin';proof.write_bytes(b'synthetic positive receipt evidence')
        evidence={'status':'confirmed','message_id':m['id'],'target_binding':m['target'],
                  'text_sha256':m['text_sha256'],'attempt':m['attempts'],
                  'attempt_started_ms':m['attempt_started_ms'],
                  'receipt_message_id':73,'observed_at_utc':datetime.fromtimestamp(
                      m['attempt_started_ms']/1000,timezone.utc).isoformat().replace('+00:00','Z'),
                  'reviewer':'synthetic-reviewer','proof_path':str(proof),
                  'proof_sha256':hashlib.sha256(proof.read_bytes()).hexdigest()}
        ev=root/'evidence.json';ev.write_text(json.dumps(evidence),encoding='utf-8')
        plan_path=root/'review.json'
        plan=reconcile.review(store,'synthetic-store',ev,plan_path)
        expect(ValueError,lambda:reconcile.apply_review(store,'synthetic-store',plan_path,ev,'wrong',rev))
        altered={**evidence,'receipt_message_id':74}
        ev.write_text(json.dumps(altered),encoding='utf-8')
        expect(ValueError,lambda:reconcile.apply_review(store,'synthetic-store',plan_path,ev,plan['review_sha256'],rev))
        ev.write_text(json.dumps(evidence),encoding='utf-8')
        result=reconcile.apply_review(store,'synthetic-store',plan_path,ev,plan['review_sha256'],rev)
        assert result['status']=='confirmed'
        expect(ValueError,lambda:reconcile.apply_review(store,'synthetic-store',plan_path,ev,plan['review_sha256'],rev))
        with durable.VolumeStore(store,'synthetic-store') as volume:
            saved=next(iter(volume.snapshot['commands'].values()))['_delivery']['messages'][0]
            assert saved['receipt']==73 and saved['text']==m['text']
            assert volume.snapshot['control']['reconciliations'][-1]['previous_revision']==rev


def test_health_and_public_export_exclude_private_data():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td);store,data,_=seeded(root)
        with durable.VolumeStore(store,'synthetic-store') as volume:
            volume.snapshot['engine']['secret_extra']='private-marker'
            volume.snapshot['control']['health']['last_watch_check_ms']=None
            volume.commit()
        h=health.evaluate(store,'synthetic-store',now_ms=1791100800000)
        assert 'watch_overdue' in h['alarms'] and h['mode']=='blocked'
        out=root/'public'
        export.export(store,'synthetic-store',out)
        joined=''.join(p.read_text(encoding='utf-8') for p in out.iterdir())
        for forbidden in ('_delivery','control','secret_extra','target_binding','bot_identity',
                          'unknown_no_replay','message_id','private-marker'):
            assert forbidden not in joined
        assert json.loads((out/'signals.json').read_text(encoding='utf-8'))['signals']
