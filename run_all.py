"""Run every experiment and regenerate every figure.

    python run_all.py            # Q1/Q3/Q5 (seconds) + Q6 (~1 min) + all figures
    python run_all.py --no-q6    # skip the Qiskit/Q6 part

Works from any current directory; paths are resolved relative to this file.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def run(script):
    print("=" * 70)
    print("running", script)
    print("=" * 70)
    runpy.run_path(str(ROOT / script), run_name="__main__")


if __name__ == "__main__":
    run("run_q1_q3_q5.py")
    if "--no-q6" not in sys.argv:
        run("run_q6.py")
    run("make_figures.py")
    print("done - see results/ and figures/")
