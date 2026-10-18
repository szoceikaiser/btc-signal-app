"""Read-only exact branch SHA, immutable tag and Tests CI check."""
import verify_d01_ci
verify_d01_ci.BRANCH = 'codex/etappe-5a-telegram-outbox'
if __name__ == '__main__': raise SystemExit(verify_d01_ci.main())
