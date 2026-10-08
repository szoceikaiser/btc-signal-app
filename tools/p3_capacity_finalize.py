"""Additive code/evidence sealing for the local N-P3-01 correction only."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'engine')]
import p3_backup_chain as b

BASE='a8d1979331442d8aa49c6919b55bd4c3b9742a72'


def git(repo,*args):
    clean={k:os.environ[k] for k in os.environ if not k.startswith(('GIT_','GH_','GITHUB_','TELEGRAM_','BTC_DELIVERY_'))}
    return subprocess.check_output(['git','-c','safe.directory='+Path(repo).resolve().as_posix(),
        '-c','core.autocrlf=false','-c','core.hooksPath='+('NUL' if os.name=='nt' else '/dev/null'),
        '-c','protocol.allow=never','-c','protocol.file.allow=always','-C',str(repo),*args],
        env=clean,stderr=subprocess.PIPE,timeout=180)


def code(out):
    assert not git(ROOT,'status','--porcelain').strip(),'Commit clean source before sealing'
    head=git(ROOT,'rev-parse','HEAD').decode().strip();tree=git(ROOT,'rev-parse','HEAD^{tree}').decode().strip()
    changed=git(ROOT,'diff','--name-only',BASE,head).decode().splitlines()
    pins=dict(base=BASE,head=head,tree=tree,files={n:b.sha(ROOT/n) for n in changed},
        active_workflow_diff=git(ROOT,'diff','--name-only',BASE,head,'--','.github/workflows').decode())
    assert not pins['active_workflow_diff']
    b.write_json(out/'CODE-PINS.json',pins)
    bundle=out/'p3-backup-korrektur.bundle';archive=out/'p3-code-canonical.zip'
    assert not bundle.exists() and not archive.exists()
    git(ROOT,'bundle','create',str(bundle),'refs/heads/codex/p3-betriebsvorbereitung')
    git(ROOT,'bundle','verify',str(bundle))
    git(ROOT,'archive','--format=zip','--output='+str(archive),head)
    target=out/'code-fresh-restore'
    assert not target.exists()
    git(out,'clone','--no-hardlinks','--branch','codex/p3-betriebsvorbereitung',str(bundle),str(target))
    git(target,'remote','set-url','--push','origin','DISABLED-OFFLINE-RESTORE')
    git(target,'fsck','--full')
    assert git(target,'rev-parse','HEAD').decode().strip()==head
    assert git(target,'rev-parse','HEAD^{tree}').decode().strip()==tree
    assert not git(target,'status','--porcelain').strip()
    hashes={}
    with zipfile.ZipFile(archive) as z:
        for item in z.infolist():
            if item.is_dir():continue
            h=hashlib.sha256(z.read(item)).hexdigest()
            assert b.sha(target/item.filename)==h,item.filename
            hashes[item.filename]=h
    tracked=git(target,'ls-files','-z').decode().rstrip('\0').split('\0')
    assert set(tracked)==set(hashes)
    b.write_json(out/'CODE-RESTORE-VERIFICATION.json',dict(passed=True,head=head,tree=tree,
        git_fsck=True,tracked_files=len(hashes),file_sha256=hashes,bundle_sha256=b.sha(bundle),
        archive_sha256=b.sha(archive),push_disabled=True))
    print('Code restore verified',head,tree,len(hashes),flush=True)


def report(out):
    cap=json.loads((out/'verified-capacity/CAPACITY-ACCEPTANCE.json').read_text())
    pins=json.loads((out/'CODE-PINS.json').read_text());protection=json.loads((out/'PROTECTED-AFTER.json').read_text())
    regression=(out/'REGRESSION-FINAL.log').read_text(encoding='utf-8')
    assert '--- 882 passed, 0 failed' in regression
    restored=(out/'RESTORED-P3-TESTS.log').read_text(encoding='utf-8')
    assert 'P3 RESTORE: 40 passed, 0 failed' in restored
    assert cap['passed'] and protection['passed']
    f=cap['fixture'];r=cap['restore'];m=cap['backups'][-1]['manifest']
    table='\n'.join(f"| {x['day']} | {x['states']} | {x['manifest']['package_count']} | {x['added_package_bytes']:,} | {x['metrics']['seconds']:.3f} | {x['metrics']['python_peak_rss']:,} | {x['metrics']['git_peak_rss']:,} |" for x in cap['backups'])
    total_objects=sum(v['bytes'] for v in cap['source_unpacked_objects'].values())
    report=f'''# N-P3-01: lokale Sicherungskapazität korrigiert

Lokal fertig: fortsetzbare vollständige Sicherung aus unveränderlicher Basis und
verketteten Inkrementen, überprüfter Abschluss und ausschließlich blocked-Restore.
N-P3-01 ist im verlangten lokalen technischen Prüfmaßstab behoben. Die Abnahme
durch den Hauptchat, reale private Proben, Online-CI dieses neuen HEADs und jede
Gesamtbetriebs-/Livefreigabe bleiben offen. Keine externe Aktion wurde ausgeführt.

## Was tatsächlich geprüft wurde

- Alte echte 1.001-Commit-Fixture: unveränderter Bundlehash
  `407ec3fe4704b5f83546b2d53beff44706ac1b816b8ebe5938c411578170c689`,390.039 Bytes.
  Alter Historyprüfer reproduziert `History size limit`. v2 sichert dieselben
  1.001 Commits bis `53392592cc77e47eb62a66c0d4a573d5f531972a`, Revision1000,
  vollständig und stellt sie mit Git-fsck gesperrt wieder her.
- Maßgeblich ist ausschließlich `verified-capacity/CAPACITY-ACCEPTANCE.json`:
  {f['days']} synthetische Tage, {f['states']:,} echte Gitcommits. Pro Tag102
  Signal-/Watch-Läufe mit je5 Writes =510; zusätzlich zwei synthetische Nachrichten
  mit Intent/sending/Quittung =6 Writes innerhalb des letzten übernommenen Watchs.
  Seed/Aktivierung kommen hinzu. Null tatsächlicher Transport.
- Beide Healthindizes enthalten8 Termine, tatsächliche lokale Commitlocators,
  Run-ID/Attempt/Nonce und bestätigte Revisionen. Maximal {f['max_health_bytes']:,}
  Healthbytes,60 erhaltene Nachrichten mit ca.2 KiB Payload/Text je Nachricht
  plus Journal-/Projektionseinträge. Dies ist keine konstante Minimalsnapshotprobe.
- Storebody {f['min_body_bytes']:,} bis {f['max_body_bytes']:,} Bytes; kumuliert
  {cap['unpacked_store_body_bytes']:,} unkomprimierte Storebodybytes. Sämtliche
  einzigartigen entpackten Gitobjekte zusammen {total_objects:,} Bytes.
- Quell-Gitdateien {cap['source_git_bytes']:,} Bytes; {m['package_count']} Pakete
  insgesamt {cap['package_bytes']:,} Bytes. Größtes Paket {cap['max_package_bytes']:,}
  Bytes, höchstens {cap['max_package_commits']} Commits und
  {cap['max_package_unpacked_bytes']:,} Storebodybytes pro Paket.
- Frischer Restore aus einer separat kopierten und vollständig hashgeprüften
  lokalen Sicherung: alle {f['states']:,} ursprünglichen Commit-SHAs in derselben
  Reihenfolge, Git-fsck, identische Objektanzahlen/-bytes, keine Alternates,
  jüngster Pin `{m['pin']}`, Revision{m['revision']}. Blocked, Nachfolgeabgleich
  erforderlich, Erfolgsindizes leer, sending wird uncertain, kein Replay.

| Tag | Stände | Pakete gesamt | neu geschriebene Paketbytes | Sekunden inkl. Vollrestore | Python-RSS Spitze | Git-Baum-RSS Spitze |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
{table}

Tage1/2/3 belegen aufeinanderfolgende Sicherungen;10/20/30 zusätzlich das begrenzte
Nachholen größerer Lücken. Alle früheren Paketdateien blieben bytegleich. Die
30-Tage-Vollprüfung im frischen Restore benötigte {r['seconds']:.3f}s,
Python-Spitze {r['python_peak_rss']:,}, Git-Baum-Spitze {r['git_peak_rss']:,} Bytes.
RSS ist gemessener Working Set, alle50ms sowie an Verarbeitungspunkten; keine
Behauptung über einen ungemessenen Instantanpeak. Windows-Jobobjekt begrenzt
zusätzlich den committed Memory aller Git-Kinder. Fixtureerstellung separat:
{f['metrics']['seconds']:.3f}s; ihre Quellpins stehen vollständig in fixture.json.

## Fehler, Grenzen und sichere Wiederaufnahme

Geprüft: fehlende/vertauschte Pakete, falsche Manifest-/Commitvorgänger, auch nach
äußerem Neuhashen, manipulierte Bytes/Identität, veralteter verlangter Endpin oder
Revision, ausgelassener Seed/Vorfahr, Unterbrechung vor/nach Paketveröffentlichung,
vor Vollrestore/Abschluss, echter Workerprozessverlust und nicht verfallender Lock.
Kein neuer Abschluss bei Fehler. Wiederaufnahme prüft bestehende Teile erneut.
Positiv beobachtetes Prozessende und explizite lokale Prüfung sind Voraussetzung
für Lockentfernung; kein zeitbasiertes Stehlen.

Separat geprüft: exakt768.000-Byte-Body zulässig,768.001 abgewiesen; Rotation am
Verarbeitungsbudget; Paket-/Verbund-/Anzahlgrenzen; Python-Speicher- und Zeitstopp;
hängender Git-Prozessbaum beendet. Ein Restore aktiviert weder Store noch Versand.
Der Monitor akzeptiert nur v2-Betriebsquittungen mit vollständigem Kettenroot und
Upload-/Readbackbeleg. v1 bleibt explizites Altformat mit altem Restore. Die lokale
Quittung `p3-local-backup-verification-v2` kann keine private Quittung vortäuschen.

Harte Grenzen:256 Commits,64 MiB Storebodies,20 MiB Dateien je Paket;512 Pakete,
8 GiB Dateien je Verbund;750 KiB einzelner Storebody;120s je Git-Prozessbaum,
1800s je Backup-/Restoreaufruf,256 MiB Python-RSS und192 MiB Git-Baum-RSS.
Commit-/Treeobjekte und Dateianzahl sind ebenfalls begrenzt; Storebranch enthält
ausschließlich delivery/stream.json. Warnungen bei80% der Größen-/Verbundgrenzen.
Planmäßige Rotation voller Commitpakete ist kein Fehler. Teilgefüllte Tagespakete
können das512-Paket-Limit früher erreichen als die theoretischen131.072 Commits.
Volle Restore-Lesearbeit wächst mit der Historie. Kein unbegrenztes Versprechen;
kein Entfernen abhängiger Basispakete und keine Journal-/Historienkürzung.

Die technische30-Tage-Probe ist keine Nutzer-SLA und keine Produktionsgrößenmessung.
Reale Body-/Git-/Paketgröße, Wachstum, freier Speicher und Hostressourcen sind vor
Freigabe zu messen. Das unveränderte primäre750-KiB-Storelimit bleibt relevant.
Signal45min ab erwartetem Schluss, Watch45min ab erwartetem Termin, Lauf15min,
Backup26h ab erwartetem Sicherungstermin und gemeinsames32-GET-Monitorbudget bleiben.

## Tests, Code und Sicherung

Lokale vollständige Regression: **882 bestanden,0 fehlgeschlagen**, einschließlich
28 bestehender P3-Gruppen und12 neuer Backupgruppen. Im frischen Code-Restore
zusätzlich40 P3-Gruppen bestanden. Kein Test übersprungen. Netzpfade sind in der
Suite gesperrt, aktive Credentialnamen entfernt. Die Entwicklungsvorläufe bleiben
additiv erhalten: erster Kapazitätslauf stoppte am256-MiB-Pythonbudget wegen
neu angelegter ctypes-Messstrukturen; behoben durch einmalige API-/Strukturbindung.
20.000 Messaufrufe prüfen dagegen. Früherer Deadlineversuch zeigte notwendige
Beendigung des gesamten Windows-Git-Prozessbaums; jetzt vor Start im Jobobjekt.
Zwischenstände in `final-capacity/` werden nicht als maßgebliche Abnahme ausgegeben.

Ausgangscommit `{BASE}`, neuer Commit `{pins['head']}`,
Baum `{pins['tree']}`. Alle geänderten Quellhashes: CODE-PINS.json. Codebundle,
kanonisches ZIP, frischer Clone/Git-fsck und vollständige Datei-Integritätsprüfung:
CODE-RESTORE-VERIFICATION.json. Zusätzliche Evidenzkopie und frischer ZIP-Restore:
SEAL.json und DELIVERY-SHA256SUMS (nach Abschluss der Versiegelung).

{protection['checked_files']:,} geschützte Dateien erneut gehasht: alle vier
geschützten Arbeitsbäume, deren HEAD/Baum/Status und alle alten Auditsets unverändert.
Aktive Workflowdateien bytegleich. Native Engine-/Geldregeln sowie inaktive
C05/S006 bleiben unberührt. Kein Push, PR, Dispatch, externer Store-/Backupwrite,
Mail, Broker, Host/cron oder Strategie-/Renditelauf. Keine Online-CI für diesen HEAD.

## Konkrete nächste externe Prüfung, noch nicht freigegeben

Die fünf vorhandenen getrennten Probenpläne bleiben bestehen. Nur Backupplan und
Quittungsvertrag wurden auf v2 angepasst: maximal6 neue Pakete/120 MiB Nutzdateien,
8 Nicht-Force-Pushes,128 MiB Gittransfer je Richtung,200 REST-Reads, danach Restore
aus der zweiten Kopie und separate bestätigte Quittung. Bei Unklarheit Halt.
Repo-/Branchnamen, IDs, Host, Rechte/Custodians, Termine und konkrete Freigaben
bleiben ungesetzt. Aufbewahrung muss sämtliche Inkrementabhängigkeiten erhalten.
Der Hauptchat entscheidet über Abnahme und weitere reale Schritte. Kein neuer
Start-/Fortsetzungsprompt wurde erstellt; kein Chat oder Messaging ausgelöst.
'''
    with (out/'BERICHT.md').open('x',encoding='utf-8') as file:file.write(report)
    b.write_json(out/'LOCAL-ACCEPTANCE.json',dict(passed=True,finding='N-P3-01',
        status='locally_corrected_pending_mainchat_review',head=pins['head'],tree=pins['tree'],
        regression_passed=882,regression_failed=0,restored_p3_passed=40,
        capacity_source_pin=m['pin'],capacity_revision=m['revision'],capacity_states=f['states'],
        capacity_manifest_sha256=digest_value(m),protected_files=protection['checked_files'],
        real_external_requests=0,online_ci_for_this_head=False,production_or_live_approval=False))


def digest_value(value):return hashlib.sha256(b.canonical(value).encode()).hexdigest()


def seal(out):
    archive=out/'p3-capacity-evidence.zip'
    excluded={'code-fresh-restore','evidence-fresh-restore','local-backup'}
    # Nested legacy migration manifests ARE evidence and must be included.
    files=sorted(p for p in out.rglob('*') if p.is_file()
        and not set(p.relative_to(out).parts)&excluded
        and p.relative_to(out).as_posix() not in {'p3-capacity-evidence.zip','SHA256SUMS','SEAL.json','DELIVERY-SHA256SUMS'})
    hashes={p.relative_to(out).as_posix():b.sha(p) for p in files}
    with (out/'SHA256SUMS').open('x',encoding='utf-8',newline='\n') as f:
        f.write(''.join(h+'  '+n+'\n' for n,h in hashes.items()))
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in [*files,out/'SHA256SUMS']:z.write(p,p.relative_to(out).as_posix())
    fresh=out/'evidence-fresh-restore';fresh.mkdir(exist_ok=False)
    with zipfile.ZipFile(archive) as z:z.extractall(fresh)
    for name,h in hashes.items():assert b.sha(fresh/name)==h,name
    assert b.sha(fresh/'SHA256SUMS')==b.sha(out/'SHA256SUMS')
    actual={p.relative_to(fresh).as_posix() for p in fresh.rglob('*') if p.is_file()}
    assert actual==set(hashes)|{'SHA256SUMS'}
    copies=out/'local-backup';copies.mkdir(exist_ok=False)
    names=['p3-capacity-evidence.zip','p3-backup-korrektur.bundle','p3-code-canonical.zip','SHA256SUMS']
    for name in names:
        shutil.copy2(out/name,copies/name);assert b.sha(copies/name)==b.sha(out/name)
    proof=dict(passed=True,files=len(hashes),fresh_restore_verified=True,
        files_sha256={name:b.sha(out/name) for name in names},
        sizes={name:(out/name).stat().st_size for name in names})
    b.write_json(out/'SEAL.json',proof);shutil.copy2(out/'SEAL.json',copies/'SEAL.json')
    names+=['SEAL.json','BERICHT.md','LOCAL-ACCEPTANCE.json','CODE-PINS.json']
    with (out/'DELIVERY-SHA256SUMS').open('x',encoding='utf-8',newline='\n') as f:
        f.write(''.join(b.sha(out/n)+'  '+n+'\n' for n in names))
    shutil.copy2(out/'DELIVERY-SHA256SUMS',copies/'DELIVERY-SHA256SUMS')
    print(json.dumps(proof),flush=True)


if __name__=='__main__':
    out=Path(sys.argv[2]).resolve()
    {'code':code,'report':report,'seal':seal}[sys.argv[1]](out)
