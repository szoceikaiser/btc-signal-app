"""Finish interrupted E44.3 runner; refresh six obsolete templates in an isolated copy."""
import ast,hashlib,json,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/audit-2026-09-27'

def main():
    source=(ROOT/'engine/sabotage_e443.py').read_text(encoding='utf-8')
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='SABOTAGEN' for x in n.targets))
    cases=[('original E44.3',*x) for x in ast.literal_eval(node.value)]
    tail='''    for m41, m42, sigs in pakete:
        if m41:
            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)
        for m in m42:
            send_text(format_ruecktest(m), dry_run=dry_run)
        if sigs:
            send_signals(sigs, dry_run=dry_run)'''
    cases += [('refreshed template',*x) for x in [
        ('E443 Altbestand ohne Bestand gilt als leer','main.py','float(d.get("bestand_pct", min(100, pos.entry_pct or 0)) or 0)','float(d.get("bestand_pct", 0) or 0)'),
        ('E41 Kauf trotz Warten','strategy_core.py','        if _e41_sperre:\n            return False','        if False:\n            return False'),
        ('E41 Wartemeldung fehlt','main.py','        if m41:\n            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)','        if False:\n            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)'),
        ('E41 Wartemeldung nach Signal','main.py',tail,tail.replace('        if m41:\n            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)\n','')+'\n        if m41:\n            send_text(format_stop_rueckeroberung(m41), dry_run=dry_run)'),
        ('E433 muster_cvd in EVAL_KEYS fehlt','backtest.py','"ampel_filter", "muster_cvd", "muster_oi",','"ampel_filter", "muster_oi",'),
        ('E434 muster_oi in EVAL_DEFAULTS fehlt','main.py','    "muster_oi": "usd",\n',''),
        ('E434 muster_oi in EVAL_KEYS fehlt','backtest.py','"ampel_filter", "muster_cvd", "muster_oi",','"ampel_filter", "muster_cvd",'),
    ]]
    result_path=OUT/'sabotage-ergaenzung.json'
    results=json.loads(result_path.read_text(encoding='utf-8')) if result_path.exists() else []
    with tempfile.TemporaryDirectory(prefix='btc-audit-final-mutations-') as temp:
        dest=Path(temp)
        for sub in ('engine','site','docs','wissens-layer'):
            shutil.copytree(ROOT/sub,dest/sub,ignore=shutil.ignore_patterns('__pycache__','audit-2026-09-27'))
        for file in ROOT.glob('*.md'):shutil.copy2(file,dest/file.name)
        for group,name,file,old,new in cases:
            if any(x['group']==group and x['name']==name for x in results):continue
            p=dest/'engine'/file
            original=p.read_text(encoding='utf-8')
            if old not in original:
                row=dict(group=group,name=name,file=file,old=old,new=new,missing=True,caught=False,import_error=False)
                results.append(row)
                result_path.write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps(row,ensure_ascii=False),flush=True)
                continue
            try:
                p.write_text(original.replace(old,new,1),encoding='utf-8')
                shutil.rmtree(dest/'engine/__pycache__',ignore_errors=True)
                r=subprocess.run([sys.executable,'run_tests.py'],cwd=dest/'engine',capture_output=True,text=True,
                    env={**os.environ,'PYTHONUTF8':'1','PYTHONDONTWRITEBYTECODE':'1'},timeout=600)
                text=r.stdout+r.stderr
                failures=[s for s in text.splitlines() if s.startswith('FAIL')]
                summary=[s for s in text.splitlines() if 'passed' in s]
                row=dict(group=group,name=name,file=file,old=old,new=new,exit_code=r.returncode,
                    summary=summary[-1] if summary else 'IMPORT ERROR',failing_tests=failures,
                    caught=bool(failures),import_error=not summary)
                results.append(row)
                print(json.dumps(row,ensure_ascii=False),flush=True)
                (OUT/'sabotage-ergaenzung.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
            finally:p.write_text(original,encoding='utf-8')
        assert all(x.get('missing') or x['caught'] and not x['import_error'] for x in results)
        assert all(x['caught'] for x in results if x['group']=='refreshed template')
        print('Detected by actual failing tests:',sum(x['caught'] for x in results),'missing original templates:',sum(bool(x.get('missing')) for x in results),flush=True)

if __name__=='__main__':main()
