param(
 [Parameter(Mandatory=$true)][string]$PlanPath,
 [Parameter(Mandatory=$true)][string]$AmendmentPath,
 [Parameter(Mandatory=$true)][string]$GrantPath,
 [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
 [string]$PythonPath='C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference='Stop'
if([Console]::IsInputRedirected){throw 'Sichtbares menschliches PowerShellfenster verwenden.'}
Write-Host 'Nur separat abgenommenen einmaligen Reader-Abgleich starten: maximal13 GET; kein Writer/PUT/Git/Recovery.'
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_happy_readback.py') --real --plan $PlanPath --amendment $AmendmentPath --grant $GrantPath --approved-amendment-sha256 $ApprovedAmendmentSha256
if($LASTEXITCODE -eq 3){Write-Host 'Eingabeabbruch vor Sessionstart; kein Versuch.';exit 3}
if($LASTEXITCODE -ne 0){throw 'HALT: sichere Kategorie/aktuelles Journal im Hauptchat pruefen. Nicht erneut starten.'}
Write-Host 'Nur lesender Abgleich fertig. STOPP fuer Hauptchat; keine Recoveryfreigabe.'
