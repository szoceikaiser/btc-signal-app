param(
    [Parameter(Mandatory=$true)][string]$AmendmentPath,
    [Parameter(Mandatory=$true)][string]$GrantPath,
    [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
    [string]$PlanPath = 'C:\Users\oeztu\BTC-Trading\audit-backups\p3-bootstrap-freigabevorbereitung-20261011\PLAN-NOT-APPROVED.json',
    [string]$PythonPath = 'C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference = 'Stop'
if ([Console]::IsInputRedirected) { throw 'In einem interaktiven lokalen PowerShell-Fenster starten.' }
Write-Host 'Einmalige Reader-401-Fortsetzung: erst nach gesonderter Hauptchat-Abnahme und Freigabe.'
Write-Host 'Es wird der vorhandene, im Originalplan gepinnte Journalordner verwendet. Nichts loeschen oder neu anlegen.'
Write-Host 'Reader/Writer jeweils genau EINMAL einfuegen, dann Enter. Keine Zeichen/Sternchen sind normal.'
Write-Host 'Tokenwerte niemals im Chat, in Argumenten oder Dateien speichern.'
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_reader401_continue.py') --real --plan $PlanPath `
    --amendment $AmendmentPath --grant $GrantPath --approved-amendment-sha256 $ApprovedAmendmentSha256
if ($LASTEXITCODE -ne 0) {
    throw 'HALT. Nicht erneut starten. Nur Status ohne Schluesselwerte im Hauptchat melden.'
}
Write-Host 'Nur blocked-Bootstrap beendet. Keine weitere Phase starten; Hauptchat prueft die Belege.'
