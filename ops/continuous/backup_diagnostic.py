"""Fixed producer diagnostics over the pinned core CLI."""
import contextlib
import hashlib
import json
import os
from pathlib import Path


def execute(core, extension, loader_hash, manifest_hash, source_hash):
    phase = 'loader_binding'
    budget = None
    reason = 'refused'
    try:
        with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
            loader = extension / 'tools/pinned_delivery_entry.py'
            raw = loader.read_bytes()
            if hashlib.sha256(raw).hexdigest() != loader_hash:
                raise ValueError()
            scope = {'__name__': 'reviewed_loader', '__file__': str(loader)}
            exec(compile(raw, str(loader), 'exec'), scope)
            scope['install'](core, extension, manifest_hash)
            phase = 'producer_source_binding'
            source = core / 'tools/p4_hosted_backup.py'
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != source_hash:
                raise ValueError()
            scope = {'__name__': 'reviewed_producer', '__file__': str(source)}
            exec(compile(raw, str(source), 'exec'), scope)
            phase = 'runtime_input'
            original_run = scope['run']
            original_budget = scope['Budget']

            def new_budget(root):
                nonlocal budget
                budget = original_budget(root)
                return budget

            def mark(namespace, name, label):
                original = namespace[name] if isinstance(namespace, dict) else getattr(namespace, name)

                def checked(*args, **kwargs):
                    nonlocal phase
                    phase = label
                    return original(*args, **kwargs)

                if isinstance(namespace, dict):
                    namespace[name] = checked
                else:
                    setattr(namespace, name, checked)

            def run(*args, **kwargs):
                nonlocal phase, reason
                try:
                    result = original_run(*args, **kwargs)
                except Exception as exc:
                    from job_quota import QuotaStopped
                    if isinstance(exc, QuotaStopped):
                        reason = 'provider_quota_or_http_refusal'
                    elif str(exc) in ('Shared HTTP/transfer limit', 'Destination capacity',
                                     'Published target capacity', 'Workspace disk/file limit',
                                     'Response byte limit', 'Git object size budget',
                                     'Total time budget', 'Python memory budget', 'Git memory budget',
                                     'Segment count budget', 'Package/set byte budget',
                                     'Git wire byte limit', 'Git transfer byte/short-packet limit'):
                        reason = 'bounded_resource_limit'
                    elif str(exc) in ('Original occurrence already late or in future',
                                      'Bounded waiting time exceeded; no replacement slot'):
                        reason = 'occurrence_refused'
                    elif str(exc) in ('Source cut moved before upload',
                                      'Source moved during publication; no upload receipt',
                                      'Source moved after final public review',
                                      'Allowed Git source ref moved/capability unavailable'):
                        reason = 'source_cut_or_capability'
                    elif str(exc) in ('Provider HTTP outcome unconfirmed', 'Provider outcome unconfirmed'):
                        reason = 'provider_unconfirmed'
                    raise
                phase = 'complete'
                return result

            scope['run'] = run
            scope['Budget'] = new_budget
            for name, label in (
                ('validate', 'runtime_binding'), ('roles', 'public_protection_and_roles'),
                ('metadata', 'run_binding_and_slot'), ('download', 'previous_package_download'),
                ('fetch_source', 'source_pack'), ('migration', 'migration_download'),
                ('validate_migration_bytes', 'package_migration_check'), ('publish', 'publication'),
            ):
                mark(scope, name, label)
            mark(scope['pair'], 'append', 'package_build')
            mark(scope['pair'], 'restore', 'package_restore')
            mark(scope['public'], 'check', 'public_review')
            status = scope['cli'](['producer'])
    except Exception:
        status = 20
    print(json.dumps({'phase':phase, 'reason':'ok' if status == 0 else reason,
                      'http':getattr(budget, 'http', 0), 'mutations':getattr(budget, 'mutations', 0),
                      'reserved_transfer_bytes':getattr(budget, 'transfer', 0)}, sort_keys=True))
    return status
