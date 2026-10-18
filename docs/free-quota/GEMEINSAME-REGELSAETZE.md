# Gemeinsam gepruefte Regelsaetze

Der Nutzer hat nach Hauptchat-Anleitung genau drei aktive Rulesets fuer vier
Betriebsbranches eingerichtet. Der Store-Regelsatz enthaelt die zwei expliziten
Targets delivery-stream-v2 und delivery-fence-v2. Backup und Verifikation haben
je einen eigenen einzelnen Targetbranch. Die bisherige Admission verglich eine
Rulesetbedingung starr mit genau einem Target und haette den korrekt nach
Anleitung eingerichteten Store deshalb abgewiesen.

Die Admission erlaubt jetzt ein bis vier explizite refs/heads-Namen, die alle
als eigene geschuetzte Branchbindungen desselben Repositorys mit richtiger ID
in public_access.protections stehen. Der gerade gepruefte Branch muss enthalten
sein. Keine Wildcards, Default-/Allbranchmarker, Ausschluesse, Duplikate oder
unreviewten Migrationstargets. Der Hash des vollstaendigen oeffentlichen
Regelsatzes bindet weiterhin die komplette geordnete Targetliste. Jede einzelne
Branchbindung braucht ihre eigenen aktiven Rules und tatsaechlichen Bypassbeleg.

Die UI-/REST-Belege und der ausgefuellte Public-Access-Pruefdatensatz liegen
separat unter audit-backups/branchschutz-abnahme-20261015 im Hauptworkspace.
Dieser Datensatz belegt ausschliesslich die oeffentlichen Lese-/Schutzbindungen.
Writerreviews bleiben pending; produktive Runtimevorlagen und C05 bleiben aus.
Weder bestehende GitHub-Regeln noch laufende Engine wurden hier geaendert.
