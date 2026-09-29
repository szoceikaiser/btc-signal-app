"""Network-free wrapper for production JavaScript sabotage probes."""
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
if __name__ == '__main__':
    print(subprocess.check_output(['node',str(ROOT/'tools/chart_5b_tests.cjs'),'--sabotage'],cwd=ROOT).decode())
