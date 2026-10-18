param(
 [Parameter(Mandatory=$true)][string]$PlanPath,
 [Parameter(Mandatory=$true)][string]$AmendmentPath,
 [Parameter(Mandatory=$true)][string]$GrantPath,
 [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
 [ValidateSet('bootstrap-public-root-once','bootstrap-public-missing-branch-once')][string]$Phase='bootstrap-public-root-once',
 [string]$PythonPath='C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference='Stop'
if([Console]::IsInputRedirected){throw 'Sichtbares interaktives PowerShell-Fenster verwenden.'}
Write-Host 'Nur mit eigener Public-Root-Abnahme und aktuellem gebundenem menschlichem Grant starten.'
Write-Host 'Reader verdeckt einfuegen, Enter. Reiner Eingabeabbruch vor Sessionstart verbraucht keinen Versuch.'
Write-Host 'Writer erst nach frischer positiver Public-Vorpruefung. Genau ein unveraenderter synthetischer Root, keine Aktivierung.'
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_public_root.py') --real --phase $Phase --plan $PlanPath --amendment $AmendmentPath --grant $GrantPath --approved-amendment-sha256 $ApprovedAmendmentSha256
if($LASTEXITCODE -eq 3){Write-Host 'Nur Reader-Eingabe abgebrochen; kein Sessionversuch. Gueltigkeit und Status vor neuem Eingabeversuch pruefen.';exit 3}
if($LASTEXITCODE -ne 0){throw 'HALT. Konkrete sichere Kategorie steht in der Python-Ausgabe. Nicht erneut starten; Ergebnis im Hauptchat pruefen lassen, keine Tokenwerte.'}
Write-Host 'Nur synthetischer Root bestaetigt. Keine weitere Phase starten.'
