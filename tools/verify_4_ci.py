"""Read-only remote branch, immutable tag and exact-SHA Tests verification."""
import verify_d01_ci
verify_d01_ci.BRANCH = 'codex/etappe-4-bestand-stop'
if __name__ == '__main__':
    raise SystemExit(verify_d01_ci.main())
