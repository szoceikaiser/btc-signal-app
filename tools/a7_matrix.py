"""Run independent, resumable A7 batch lanes with bounded local processes."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def one(mode, package, scenario):
    if mode == "targeted":
        cmd = [sys.executable, str(ROOT / "tools" / "a7_targeted.py"),
               "--package", package, "--scenario", scenario]
    else:
        cmd = [sys.executable, str(ROOT / "tools" / "a7_batch.py"),
               "--mode", mode, "--package", package, "--scenario", scenario]
    begin = time.monotonic()
    result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return (mode, package, scenario, result.returncode, time.monotonic() - begin,
            result.stdout.splitlines(), result.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--set", choices=["grid", "halves", "pair", "fresh", "capital",
                                          "targeted"],
                        required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--skip-r0-s0", action="store_true")
    args = parser.parse_args()
    assert 1 <= args.workers <= 8
    scenarios = [f"S{i}" for i in range(5)]
    packages = ["R0", "R1"]
    if args.set == "targeted":
        jobs = [("targeted", p, s) for p in packages for s in scenarios]
    elif args.set == "grid":
        jobs = [("grid", p, s) for p in packages for s in scenarios]
    elif args.set == "halves":
        jobs = [(m, p, "S0") for m in ("half1", "half2") for p in packages]
    elif args.set == "pair":
        jobs = [("pair", p, s) for p in packages for s in scenarios]
    elif args.set == "fresh":
        jobs = [(m, p, s) for m in ("fresh1", "fresh2") for p in packages
                for s in scenarios]
    else:
        jobs = [(m, p, s) for m in ("capital06", "capital05") for p in packages
                for s in scenarios]
    if args.skip_r0_s0:
        jobs = [job for job in jobs if job[1:] != ("R0", "S0")]
    failed = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(one, *job) for job in jobs]
        for future in as_completed(futures):
            mode, package, scenario, code, seconds, output, error = future.result()
            print(mode, package, scenario, "PASS" if code == 0 else "FAIL",
                  round(seconds, 1), "s", len(output), "new rows", flush=True)
            if code:
                failed.append((mode, package, scenario))
                print("\n".join(output[-5:]), error, flush=True)
    if failed:
        raise SystemExit(f"A7 lanes failed: {failed}")


if __name__ == "__main__":
    main()
