"""Q1, Q3, Q5: closed-form and numpy-statevector experiments (no Qiskit needed).

Q1  needle:        Grover on N = 2^4 .. 2^20 items with one marked item.
Q3  structure:     ordered-search cost curves for localising m boundaries of width W.
Q5  hidden corner: Grover on an antichain of n = 2^2 .. 2^16 candidate cells.

Writes results/Q1_needle.csv, results/Q3_structure.csv, results/Q5_hidden_corner.csv.
Runs in a few seconds.
"""
import csv
import math

from qfa.core import grover_success_closed_form, grover_success_statevector, k_star
from qfa.paths import ensure_dirs


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def run_q1(results):
    rows = []
    for e in range(4, 21):
        N = 2 ** e
        k = k_star(N, 1)
        p = grover_success_closed_form(N, 1, k)
        p_sv = grover_success_statevector(N, [0], k) if N <= 2 ** 14 else float("nan")
        rows.append({"N": N, "log2N": e, "grover_iters": k, "success": p,
                     "success_statevec": p_sv, "classical_expected": (N + 1) / 2,
                     "ratio": ((N + 1) / 2) / k})
    write_csv(results / "Q1_needle.csv", rows)
    return rows


def run_q3(results):
    """Classical binary search vs. best known quantum ordered search (~0.32 m log2 W)
    vs. the adversary/direct-sum lower bound with error 1/3:
    (1 - 2 sqrt(eps(1-eps)))/2 * m * (ln W - 1)/pi."""
    rows = []
    eps = 1.0 / 3.0
    pref = (1 - 2 * math.sqrt(eps * (1 - eps))) / 2
    for log2W in [8, 16, 32, 52]:
        W = 2 ** log2W
        for m in [4, 16, 64, 256, 1024]:
            classical = m * log2W
            q_lower = pref * m * (math.log(W) - 1) / math.pi
            q_best = 0.32 * m * log2W
            rows.append({"W": W, "log2W": log2W, "m": m,
                         "classical_binsearch": classical,
                         "quantum_best_known": q_best,
                         "quantum_lower_bound": q_lower,
                         "ratio_classical_over_best_quantum": classical / q_best})
    write_csv(results / "Q3_structure.csv", rows)
    return rows


def run_q5(results):
    rows = []
    for e in range(2, 17):
        n = 2 ** e
        k = k_star(n, 1)
        p = grover_success_closed_form(n, 1, k)
        rows.append({"n": n, "log2n": e, "quantum_iters": k, "success": p,
                     "classical_worst": n, "classical_expected": (n + 1) / 2})
    write_csv(results / "Q5_hidden_corner.csv", rows)
    return rows


def main():
    results, _ = ensure_dirs()
    q1 = run_q1(results)
    q3 = run_q3(results)
    q5 = run_q5(results)
    print("Q1 needle: rows =", len(q1), "| e.g. N=2^12 -> k* =",
          [r for r in q1 if r["log2N"] == 12][0]["grover_iters"])
    print("Q3 structure: rows =", len(q3))
    print("Q5 hidden corner: rows =", len(q5))
    print("wrote", results / "Q1_needle.csv")
    print("wrote", results / "Q3_structure.csv")
    print("wrote", results / "Q5_hidden_corner.csv")


if __name__ == "__main__":
    main()
