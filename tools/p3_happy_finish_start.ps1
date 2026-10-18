param(
 [Parameter(Mandatory=$true)][ValidateSet('close','rest','takeover','inspect')][string]$Section,
 [Parameter(Mandatory=$true)][string]$PlanPath,
 [Parameter(Mandatory=$true)][string]$AmendmentPath,
 [Parameter(Mandatory=$true)][string]$GrantPath,
 [Parameter(Mandatory=$true)][string]$ApprovedAmendmentSha256,
 [string]$TerminationReviewPath,[string]$ReceiptPath,
 [string]$PythonPath='C:\Users\oeztu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)
$ErrorActionPreference='Stop'
if([Console]::IsInputRedirected){throw 'Sichtbares menschliches PowerShellfenster verwenden.'}
$probeArgs=@('--real','--section',$Section,'--plan',$PlanPath,'--amendment',$AmendmentPath,'--grant',$GrantPath,'--approved-amendment-sha256',$ApprovedAmendmentSha256)
if($Section -eq 'rest'){if(!$ReceiptPath){throw 'Neuer tatsächlicher Parentwait-Quittungspfad erforderlich.'};$probeArgs+=@('--receipt',$ReceiptPath)}
if($Section -eq 'takeover'){if(!$TerminationReviewPath){throw 'Eigener tatsächlicher Exit23-/Ownerreview erforderlich.'};$probeArgs+=@('--termination-review',$TerminationReviewPath)}
Write-Host 'Nur eigener abgenommener Abschnitt. Reader/Writer verdeckt, keine automatische Folgefreigabe.'
& $PythonPath -B (Join-Path $PSScriptRoot 'p3_happy_finish.py') @probeArgs
if($LASTEXITCODE -eq 3){Write-Host 'Eingabe vor durablem Start abgebrochen; kein Versuch.';exit 3}
if($LASTEXITCODE -ne 0){throw 'HALT: keine erneute Mutation. Journal/sichere Kategorie im Hauptchat prüfen.'}
Write-Host 'STOPP für Hauptchat; ausschließlich freigegebener Abschnitt beendet.'
