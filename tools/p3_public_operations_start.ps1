param(
 [Parameter(Mandatory=$true)][ValidateSet('initial','takeover','inspect')][string]$Section,
 [Parameter(Mandatory=$true)][string]$PlanPath,
 [Parameter(Mandatory=$true)][string]$AmendmentPath,
 [Parameter(Mandatory=$true)][string]$GrantPath,
 [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
 [string]$TerminationReviewPath,[string]$ReceiptPath,
 [string]$PythonPath='C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference='Stop'
if([Console]::IsInputRedirected){throw 'Sichtbares interaktives PowerShell-Fenster verwenden.'}
Write-Host 'Nur nach Hauptchat-Abnahme und eigener menschlicher Abschnittsfreigabe starten.'
Write-Host 'Zugaenge einmal verdeckt je Abschnitt. Reiner Eingabeabbruch vor Start verbraucht keinen Versuch.'
$probeArgs=@('--real','--section',$Section,'--plan',$PlanPath,'--amendment',$AmendmentPath,'--grant',$GrantPath,'--approved-amendment-sha256',$ApprovedAmendmentSha256)
if($Section -eq 'initial'){
 if(!$ReceiptPath){throw 'Neuer Pfad fuer echte Elternquittung erforderlich.'}
 $probeArgs+=@('--receipt',$ReceiptPath)
}
if($Section -eq 'takeover'){
 if(!$TerminationReviewPath){throw 'Tatsaechlicher Owner-/Prozessende-Review erforderlich.'}
 $probeArgs+=@('--termination-review',$TerminationReviewPath)
}
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_public_operations.py') @probeArgs
if($LASTEXITCODE -eq 3){Write-Host 'Nur Eingabe abgebrochen; Status/Gueltigkeit erneut pruefen.';exit 3}
if($LASTEXITCODE -ne 0){throw 'HALT. Sichere Kategorie/Ergebnis im Hauptchat pruefen, nicht erneut starten.'}
Write-Host 'Abschnitt beendet. Keine automatische Folgephase. Nach Prozessverlust nur mit neuer Hauptchat-Abnahme weiter.'
