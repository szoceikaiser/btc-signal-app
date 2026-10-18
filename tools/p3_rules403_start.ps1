param(
    [Parameter(Mandatory=$true)][ValidateSet('Diagnose','DiagnoseFortsetzen','Upload')][string]$Phase,
    [Parameter(Mandatory=$true)][string]$AmendmentPath,
    [Parameter(Mandatory=$true)][string]$GrantPath,
    [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
    [string]$PlanPath = 'C:\Users\oeztu\BTC-Trading\audit-backups\p3-bootstrap-freigabevorbereitung-20261011\PLAN-NOT-APPROVED.json',
    [string]$PythonPath = 'C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference = 'Stop'
if ([Console]::IsInputRedirected) { throw 'Ein sichtbares interaktives PowerShell-Fenster verwenden.' }
Write-Host 'Nur nach eigener Hauptchat-Abnahme und exakt gebundenem Phasengrant starten.'
Write-Host 'Vorhandene Session bleibt massgeblich. Nichts loeschen, neu anlegen oder erneut starten.'
Write-Host 'Reader genau EINMAL verdeckt einfuegen, dann Enter. Keine Zeichen/Sternchen sind normal.'
if ($Phase -ne 'Upload') {
    $probePhase = if ($Phase -eq 'DiagnoseFortsetzen') { 'bootstrap-rules403-preget-once' } else { 'bootstrap-rules403-diagnose-once' }
    Write-Host 'Nur lesende Diagnose, kein Writer und kein Upload.'
    if ($Phase -eq 'DiagnoseFortsetzen') {
        $readerAmendment = Get-Content -LiteralPath $AmendmentPath -Raw | ConvertFrom-Json
        if ($readerAmendment.schema -ne 'p3-rules403-preget-amendment-v2') {
            throw 'Exakter Reader-Gueltigkeitsnachtrag erforderlich. Originalplan nicht umdatieren.'
        }
        Write-Host 'Eigenes Reader-Zeitfenster maximal60Minuten; aktueller Reviewgrant erforderlich.'
    }
} else {
    $probePhase = 'bootstrap-rules403-upload-once'
    Write-Host 'Upload braucht einen eigenen spaeteren Reviewgrant. Writer erst nach erfolgreicher frischer Vorpruefung.'
}
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_rules403.py') --real --phase $probePhase --plan $PlanPath `
    --amendment $AmendmentPath --grant $GrantPath --approved-amendment-sha256 $ApprovedAmendmentSha256
if ($LASTEXITCODE -ne 0) { throw 'HALT. Sichere Kategorie/Ergebnisort im Hauptchat melden, keine Tokenwerte. Nicht erneut starten.' }
Write-Host 'Nur diese Phase abgeschlossen. Keine Folgephase starten; neue Belege im Hauptchat pruefen lassen.'
