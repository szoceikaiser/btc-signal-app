"""Offline, one-way legacy snapshot converter. Never creates a delivery store."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'engine'))
from position_state import pos_from_state, pos_to_state
from production_contract import CANDLE_MS, canonical, digest, effective_config, validate_v2


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'), parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def write_json(path, value):
    Path(path).write_text(canonical(value)+'\n', encoding='utf-8', newline='\n')


def utc(value):
    if not isinstance(value, str) or not value.endswith('Z'):
        raise ValueError('Expected explicit UTC timestamp')
    return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone(timezone.utc)


def _source(source_dir, manifest):
    required = ('state.json', 'signals.json', 'oi_history.json', 'config-source.json')
    files = manifest.get('files')
    if manifest.get('schema') != 'produktion-source-v1' or manifest.get('mode') not in ('rehearsal', 'live_candidate'):
        raise ValueError('Unknown source manifest')
    for k in ('repository', 'code_sha', 'source_sha', 'git_tree', 'captured_at_utc'):
        if not isinstance(manifest.get(k), str) or not manifest[k]:
            raise ValueError('Missing source identity: '+k)
    utc(manifest['captured_at_utc'])
    if not isinstance(files, dict) or any(n not in files for n in (*required, 'watch.json')):
        raise ValueError('Incomplete source file manifest')
    copied = {}
    for name, meta in files.items():
        if '/' in name or '\\' in name or name.startswith('.'):
            raise ValueError('Unsafe source path')
        path = source_dir/name
        if name == 'watch.json' and meta.get('presence') == 'missing':
            if path.exists():
                raise ValueError('Watch presence conflicts with source')
            continue
        if not path.is_file():
            raise ValueError('Missing source file: '+name)
        data = path.read_bytes()
        if sha(data) != meta.get('sha256') or len(data) != meta.get('size'):
            raise ValueError('Source hash/size mismatch: '+name)
        copied[name] = data
    for name in required:
        if name not in copied:
            raise ValueError('Missing mandatory source: '+name)
    return copied


def convert(source_dir, manifest_path, cutover_path, config_path, out):
    source_dir, out = Path(source_dir), Path(out)
    if out.exists():
        raise FileExistsError(out)
    if out.resolve().is_relative_to(source_dir.resolve()):
        raise ValueError('Migration output must be outside immutable source directory')
    manifest, cutover, target_raw = (read_json(p) for p in (manifest_path, cutover_path, config_path))
    source = _source(source_dir, manifest)
    objs = {name: json.loads(data, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
            for name, data in source.items()}
    state, history, oi, old_cfg = (objs[n] for n in ('state.json', 'signals.json', 'oi_history.json', 'config-source.json'))
    if not isinstance(state, dict) or state.get('demo') or '_delivery' in state or 'state_version' in state:
        raise ValueError('Not a legacy, non-demo engine state')
    if not isinstance(history, dict) or not isinstance(history.get('signals'), list) or history.get('demo'):
        raise ValueError('Invalid signal history')
    if not isinstance(oi, list) or not isinstance(old_cfg, dict) or not isinstance(state.get('config'), dict):
        raise ValueError('Invalid legacy source')
    canonical([state, history, oi, old_cfg, cutover, target_raw])
    b = state.get('last_signal_ts')
    t = cutover.get('freeze_at_ms')
    if type(b) is not int or type(t) is not int or b % CANDLE_MS:
        raise ValueError('Invalid B or freeze time')
    w = (t//CANDLE_MS)*CANDLE_MS
    if b != w-CANDLE_MS:
        raise ValueError('Missing or future closed candle at cutover')
    for sig in history['signals']:
        if not isinstance(sig, dict) or type(sig.get('ts')) is not int or sig['ts'] > b:
            raise ValueError('Signal history newer than B or invalid')
    watch = objs.get('watch.json', {})
    if not isinstance(watch, dict) or (watch.get('gewarnt_ts') is not None and
                                       (type(watch['gewarnt_ts']) is not int or watch['gewarnt_ts'] > w)):
        raise ValueError('Invalid watch boundary')
    if cutover.get('last_persisted_B') != b or cutover.get('source_sha') != manifest['source_sha']:
        raise ValueError('Mixed source revision or last-run gap')
    runs = cutover.get('last_runs')
    if not isinstance(runs, list) or not runs or any(x.get('status') != 'complete' for x in runs):
        raise ValueError('Unclear last legacy run')
    if manifest['mode'] == 'live_candidate' and (not cutover.get('writers_stopped') or
            not cutover.get('snapshot_consistent') or cutover.get('synthetic')):
        raise ValueError('Live candidate lacks actual freeze evidence')
    target = effective_config(target_raw)
    source_effective = {k:v for k,v in old_cfg.items() if not k.startswith('_')}
    embedded = state['config']
    embedded_diff = {k:{'embedded':embedded.get(k),'source':source_effective.get(k)}
                     for k in embedded.keys() | source_effective.keys()
                     if embedded.get(k)!=source_effective.get(k)}
    if embedded_diff and not cutover.get('embedded_config_difference_reviewed'):
        raise ValueError('Embedded and external legacy configuration differ without review')
    config_diff = {k: {'old': source_effective.get(k), 'target': target.get(k)}
                   for k in source_effective.keys() | target.keys()
                   if source_effective.get(k) != target.get(k)}
    unapproved = set(config_diff)-{'muster_cvd'}-set(cutover.get('approved_config_differences', []))
    if unapproved:
        raise ValueError('Unapproved target configuration differences: '+','.join(sorted(unapproved)))
    if source_effective.get('muster_cvd') != 'alt' or target['muster_cvd'] != 'usd':
        raise ValueError('Expected explicit alt to usd CVD transition')
    pos = pos_from_state(state)
    converted = pos_to_state(pos)
    ignored = {'config', 'updated_at', 'last_close', 'widerstand', 'plan', 'zonen_vorschau'}
    unknown_fields = sorted(set(state)-set(converted)-ignored)
    for k in set(state) & set(converted):
        if k == 'zones':
            if any(converted['zones'].get(z) != v for z,v in (state['zones'] or {}).items()):
                raise ValueError('Position zone altered: '+k)
        elif converted[k] != state[k]:
            raise ValueError('Position field altered: '+k)
    additions = sorted(set(converted)-set(state))
    engine = deepcopy(converted)
    for k in ('updated_at', 'last_close', 'widerstand', 'plan', 'zonen_vorschau'):
        if k in state:
            engine[k] = deepcopy(state[k])
    engine['config'] = target
    engine['_delivery'] = {'version':1, 'messages':[], 'signals':deepcopy(history), 'oi_history':deepcopy(oi)}
    unknowns = sorted(set(pos.migration_notes) | set(unknown_fields) |
                      {'legacy_delivery_unknown_no_replay', 'legacy_fills_unknown'} |
                      ({'watch_source_missing'} if 'watch.json' not in source else set()))
    if pos.state.value != 'FLAT' and pos.valid_stop is None:
        unknowns.append('prior_stop_maximum_unknown')
    source_hashes = {name: sha(data) for name,data in source.items()}
    identity = {k:cutover.get(k) for k in ('stream_id','store_id','target_binding','bot_identity','code_sha')}
    if any(not isinstance(v,str) or not v for v in identity.values()):
        raise ValueError('Missing stream/store/target/bot/code identity')
    gates = {k:bool(cutover.get(k)) for k in ('writers_stopped','snapshot_consistent',
        'target_approved','bot_approved','d1_selected','d2_approved','d3_ready','store_accepted','config_approved')}
    gates['fresh'] = bool(cutover.get('fresh'))
    migration = {
        'migration_id':digest({'manifest':manifest,'cutover':cutover,'target':target}),
        'source_hashes':source_hashes, 'B':b, 'W':w, 'history_sha256':digest(history),
        'history_count':len(history['signals']), 'legacy_delivery':'unknown_no_replay',
        'watch_source_presence':'present' if 'watch.json' in source else 'missing',
        'config_difference':config_diff, 'embedded_config_difference':embedded_diff,
        'unknowns':unknowns, 'gates':gates,
        'evidence_refs':cutover.get('evidence_refs', []),
    }
    snapshot = {'version':2,'engine':engine,'watch':deepcopy(watch),'commands':{},
        'control':{**identity,'mode':'blocked','config_sha256':digest(target),
            'migration':migration,'health':{},'reconciliations':[]}}
    validate_v2(snapshot)
    ready = manifest['mode'] == 'live_candidate' and all(gates.values()) and not unknown_fields
    report = {'schema':'produktion-migration-report-v1','conversion_valid':True,
        'activation_ready':ready,'mode':manifest['mode'],'B':b,'W':w,
        'signal_count':len(history['signals']),'oi_count':len(oi),
        'source_hashes':source_hashes,'field_additions':additions,'unknowns':unknowns,
        'config_embedded':embedded,'config_source':source_effective,'config_target':target,
        'embedded_config_difference':embedded_diff,
        'config_difference':config_diff,'gates':gates,
        'suppressed':['historical_signal','historical_e41_e42','initial_plan',
                      'initial_preview','watch_through_W','old_watch_resolution','resend_all']}
    temp = Path(tempfile.mkdtemp(prefix='.produktion-migrate-', dir=out.parent))
    try:
        (temp/'source').mkdir()
        for name,data in source.items():
            (temp/'source'/name).write_bytes(data)
        for name,path in [('source-manifest.json',manifest_path),('cutover.json',cutover_path),
                          ('config-target.json',config_path)]:
            (temp/'source'/name).write_bytes(Path(path).read_bytes())
        (temp/'projection').mkdir()
        for name,value in [('state.json',engine),('signals.json',history),('oi_history.json',oi),
                           ('watch.json',watch),('config.json',target)]:
            write_json(temp/'projection'/name,value)
        write_json(temp/'snapshot.v2.json',snapshot)
        write_json(temp/'migration-manifest.json',migration)
        write_json(temp/'migration-report.json',report)
        (temp/'MIGRATIONSBERICHT.md').write_text(
            f"# Offline-Migration\n\nB: {b}; W: {w}; Signale: {len(history['signals'])}.\n\n"
            f"Konvertierung gültig: ja. Aktivierbar: {'ja' if ready else 'nein'}. "
            "Alte Zustellungen unbekannt, keine Nachsendung.\n", encoding='utf-8')
        paths = sorted(p for p in temp.rglob('*') if p.is_file())
        (temp/'SHA256SUMS').write_text(''.join(f'{sha(p.read_bytes())}  {p.relative_to(temp).as_posix()}\n' for p in paths), encoding='utf-8')
        if read_json(temp/'snapshot.v2.json') != snapshot or read_json(temp/'migration-report.json') != report:
            raise ValueError('Written package verification failed')
        for p in paths:
            if sha(p.read_bytes()) != next(line.split('  ')[0] for line in (temp/'SHA256SUMS').read_text().splitlines()
                                           if line.endswith('  '+p.relative_to(temp).as_posix())):
                raise ValueError('Output hash verification failed')
        temp.rename(out)
    finally:
        if temp.exists():
            shutil.rmtree(temp)
    return report


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    for arg in ('source-dir','manifest','cutover','config','out'):
        p.add_argument('--'+arg,required=True)
    a=p.parse_args()
    print(canonical(convert(a.source_dir,a.manifest,a.cutover,a.config,a.out)))
