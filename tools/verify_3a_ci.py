"""Nur lesende Remote-/CI-Abnahme, gleiche Kontrollen wie beim D01-Abschluss.

Keine Workflows starten. Ausgabe lokal ausserhalb des Git-Arbeitsbaums sichern.
"""
import verify_d01_ci

verify_d01_ci.BRANCH = 'codex/etappe-3a-ausfuehrungsvertrag'

if __name__ == '__main__':
    raise SystemExit(verify_d01_ci.main())
