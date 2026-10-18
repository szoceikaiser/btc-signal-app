"""Read-only remote HEAD / exact SHA CI / immutable tag verification."""
import verify_d01_ci
verify_d01_ci.BRANCH = 'codex/etappe-5b-chart-identitaet'
if __name__ == '__main__': raise SystemExit(verify_d01_ci.main())
