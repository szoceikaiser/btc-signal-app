"""Nur lesende GitHub-Abnahme des D01-Zweigs; keine Workflows starten."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
BRANCH = 'codex/fix-d01-kerzenschluss'
TAG = 'sicherung/vor-audit-korrekturen-2026-09-28'
BASE_MAIN = '469be65f65327a3b6abf2794ceba09c1fe0de9e2'


def main():
    command = ['git', '-c', f'safe.directory={ROOT.as_posix()}']
    commit = subprocess.run(command+['rev-parse', 'HEAD'], capture_output=True,
                            text=True, check=True).stdout.strip()
    credential = subprocess.run(command+['credential', 'fill'],
                                input='protocol=https\nhost=github.com\n\n',
                                capture_output=True, text=True, check=True,
                                env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
    fields = dict(line.split('=', 1) for line in credential.stdout.splitlines() if '=' in line)

    def get(path):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'btc-d01-check'}
        if fields.get('password'):
            headers['Authorization'] = 'Bearer '+fields['password']
        req = urllib.request.Request('https://api.github.com/repos/szoceikaiser/btc-signal-app'+path,
                                     headers=headers)
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)

    branch = get('/branches/'+BRANCH)
    assert branch['commit']['sha'] == commit
    ref = get('/git/ref/tags/'+TAG)
    tag_object = ref['object']
    tag_target = get('/git/tags/'+tag_object['sha'])['object']['sha'] if tag_object['type'] == 'tag' else tag_object['sha']
    assert tag_target == BASE_MAIN
    # Main kann durch die unabhaengige Live-Engine vorgerueckt sein. Nur ablesen.
    main_commit = get('/branches/main')['commit']['sha']
    runs = get('/actions/runs?head_sha='+commit+'&per_page=100')['workflow_runs']
    selected = [dict(id=r['id'], name=r['name'], status=r['status'], conclusion=r['conclusion'],
                     url=r['html_url'], head_sha=r['head_sha'], event=r['event']) for r in runs]
    assert all(r['name'] == 'Tests' for r in selected), selected
    completed = bool(selected) and all(r['status'] == 'completed' and r['conclusion'] == 'success' for r in selected)
    print(json.dumps(dict(branch=BRANCH, commit=commit, main_observed=main_commit,
                          tag_object=tag_object['sha'], tag_target=tag_target,
                          runs=selected, tests_success=completed), indent=2))
    return 0 if completed else 2


if __name__ == '__main__':
    raise SystemExit(main())
