"""Reached green F13 cases, then isolated in-memory faults. No network."""
from contextlib import redirect_stdout
import inspect
import io
import json
from unittest.mock import patch
import main
import telegram_notify as tg
import telegram_outbox as box
import test_stage5a as t


def verify():
    cases = [
        ('intent_not_enqueued', box, 'enqueue', "delivery['messages'].append(dict(", "return\n    delivery['messages'].append(dict(", t.test_rejection_retries_same_intent_without_replaying_real_buy),
        ('identity_ignores_sequence', box, 'identity', '[kind, event, sequence, payload]', '[kind, event, payload]', t.test_stable_id_is_independent_of_dict_order_and_text_is_fixed),
        ('dry_run_pending', box, 'enqueue', "status='preview' if preview else 'pending'", "status='pending'", t.test_dry_run_is_terminal_preview_even_when_credentials_appear),
        ('confirmed_resent', box, 'drain', "if m['status'] in {'confirmed', 'preview'}:", "if m['status'] in {'preview'}:", t.test_confirmed_is_never_resent_on_restart),
        ('uncertain_retried', box, 'drain', "if m['status'] in {'uncertain', 'sending'}:", 'if False:', t.test_timeout_after_acceptance_is_uncertain_never_automatically_retried),
        ('sending_not_saved', box, 'drain', 'atomic_json(state_path, state)\n        try:', 'pass\n        try:', t.test_commit_exists_before_any_transport_attempt),
        ('rejection_drops_queue', box, 'drain', "m['status'] = result['status']", "m['status'] = 'confirmed'", t.test_rejection_retries_same_intent_without_replaying_real_buy),
        ('failed_message_overtaken', box, 'drain', "if m['status'] != 'confirmed':", 'if False:', t.test_middle_rejection_preserves_order_and_retries_only_remaining_messages),
        ('receipt_not_saved', box, 'drain', "m['receipt'] = result.get('message_id') if m['status'] == 'confirmed' else None", "m['receipt'] = None", t.test_rejection_retries_same_intent_without_replaying_real_buy),
        ('interrupted_attempt_requeued', box, 'recover', "'uncertain', 'process_interrupted'", "'pending', 'process_interrupted'", t.test_receipt_write_failure_keeps_sending_then_uncertain_on_restart),
        ('target_change_ignored', box, 'drain', "if m['target'] is not None and m['target'] != target_key:", 'if False:', t.test_goal_change_blocks_rejected_message_and_does_not_persist_chat_or_token),
        ('true_without_message_id_accepted', tg, 'deliver_telegram', 'if type(mid) is int and mid > 0:', "if True:\n                mid = 42", t.test_transport_requires_ok_and_message_id),
        ('server_failure_retried', tg, 'deliver_telegram', "400 <= body['error_code'] < 500", "400 <= body['error_code'] < 600", t.test_transport_explicit_rejection_and_server_failure_are_distinguished),
        ('projection_drops_signal_history', box, 'project', "d['signals']", "{'signals': []}", t.test_state_projection_damage_is_repaired_from_canonical_history_and_oi),
        ('unknown_schema_accepted', box, 'load_delivery', "delivery.get('version') != 1", 'False', t.test_invalid_schema_stops_before_transport_or_state_overwrite),
        ('text_integrity_ignored', box, 'load_delivery', "if m['text_sha256'] != hashlib.sha256(m['text'].encode()).hexdigest():", 'if False:', t.test_text_tampering_and_invalid_projection_stop_before_send),
    ]
    result = []
    for name, module, attr, old, new, test in cases:
        with redirect_stdout(io.StringIO()): test()
        source = inspect.getsource(getattr(module, attr))
        assert old in source, (name, 'anchor missing')
        ns = dict(vars(module))
        exec(compile(source.replace(old, new), '<F13 '+name+'>', 'exec'), ns)
        caught = None
        with patch.object(module, attr, ns[attr]):
            try:
                with redirect_stdout(io.StringIO()): test()
            except (AssertionError, ValueError) as error:
                caught = type(error).__name__
        assert caught, name+' survived reached test'
        result.append(dict(name=name, baseline='PASS', reached=test.__name__, caught=caught))
    return dict(total=len(result), caught=len(result), cases=result)


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
