"""Q6: compile real first-match listed-rule policies into a quantum phase oracle
and run Grover on it.

Q6a  witness search: specification sigma with 4 rules over [16]^2 (N = 256, 8 qubits);
     the implementation pi shifts one edge of rule 2 by t cells. Grover searches for a
     header where pi != sigma. Also the BBHT schedule for unknown M (expected queries).
Q6b  hidden corner: compile the 8 members of H(8), verify the structural lemma
     exhaustively, then compare Grover over the 8 corner cells with naive Grover over
     all 256 headers.

Success probabilities are computed with the Qiskit Aer statevector simulator (if
installed) and always with an independent numpy statevector; both are written to the
CSV. Without Qiskit the Aer column is left empty. Runtime: about one minute.

Writes results/Q6_real_policy_oracle.csv
"""
import csv
import math
import os
import sys

import numpy as np

from qfa.core import (ListedRule, grover_success_statevector, hidden_corner_family,
                      k_star, verify_hidden_corner_family)
from qfa.paths import ensure_dirs

W = 16
N = W * W
NQ = 8

# ---------------------------------------------------------------- Qiskit (optional)
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit.quantum_info import Operator
    from qiskit_aer import AerSimulator
    try:                                   # Qiskit >= 1.3 / 2.x: function form
        from qiskit.circuit.library import grover_operator as _grover_operator
    except ImportError:                    # older Qiskit: class form
        from qiskit.circuit.library import GroverOperator as _grover_operator
    HAVE_QISKIT = True
except Exception as _e:  # ImportError or version problems
    HAVE_QISKIT = False
    QISKIT_IMPORT_ERROR = "%s: %s" % (type(_e).__name__, _e)
if os.environ.get("QFA_NO_QISKIT"):   # force the numpy-only path
    HAVE_QISKIT = False


def grover_qiskit(marked, nq, k):
    """P[success] after k Grover iterations, Aer statevector, phase oracle from a diagonal."""
    diag = np.ones(2 ** nq)
    diag[list(marked)] = -1.0
    oracle = QuantumCircuit(nq)
    oracle.unitary(Operator(np.diag(diag)), range(nq), label="O_pi")
    G = _grover_operator(oracle, insert_barriers=False)
    qc = QuantumCircuit(nq)
    qc.h(range(nq))
    for _ in range(k):
        qc.compose(G, inplace=True)
    qc.save_statevector()
    sim = AerSimulator(method="statevector")
    sv = np.asarray(sim.run(transpile(qc, sim)).result().get_statevector())
    return float(sum(abs(sv[i]) ** 2 for i in marked))


def bbht_expected_queries(marked, nq, trials=2000, seed=0):
    """Expected total oracle queries of the BBHT schedule (unknown number of marked
    items): pick j uniformly in [0, m), run j iterations, measure, verify with one
    query; on failure grow m by 6/5 up to sqrt(N). Success probability after j
    iterations is taken from the exact statevector, so only the schedule is random."""
    rng = np.random.default_rng(seed)
    n = 2 ** nq
    total = 0
    for _ in range(trials):
        lam, m, queries = 6.0 / 5.0, 1.0, 0
        while True:
            j = int(rng.integers(0, int(m)))
            queries += j + 1
            if rng.random() < grover_success_statevector(n, marked, j):
                break
            m = min(lam * m, math.sqrt(n))
        total += queries
    return total / trials


def spec_policy():
    return ListedRule([((0, 7), (0, 15), 1), ((8, 15), (0, 3), 1),
                       ((4, 11), (8, 11), 0), ((12, 15), (12, 15), 1)], default=0, width=W)


def impl_policy(t):
    """Same rules with the upper y-edge of rule 2 shifted from 3 to 3 + t."""
    return ListedRule([((0, 7), (0, 15), 1), ((8, 15), (0, 3 + t), 1),
                       ((4, 11), (8, 11), 0), ((12, 15), (12, 15), 1)], default=0, width=W)


COLUMNS = ["exp", "case", "N", "M", "k_star", "sqrt_N_over_M", "p_success_qiskit",
           "p_success_numpy", "classical_expected", "bbht_expected_queries",
           "naive_k_star", "naive_p_qiskit", "naive_p_numpy", "naive_classical_expected"]


def main():
    results, _ = ensure_dirs()
    print("Qiskit Aer available:", HAVE_QISKIT)
    if not HAVE_QISKIT and "QISKIT_IMPORT_ERROR" in globals():
        print("  (import failed:", QISKIT_IMPORT_ERROR, ")")
        print("  python executable:", sys.executable)
    rows = []
    sigma = spec_policy().table()

    # ---------------- Q6a: witness search, M known
    for t in [1, 2, 4, 8, 12]:
        pi = impl_policy(t).table()
        marked = np.flatnonzero(pi ^ sigma)
        M = len(marked)
        k = k_star(N, M)
        p_np = grover_success_statevector(N, marked, k)
        p_qk = grover_qiskit(marked, NQ, k) if HAVE_QISKIT else ""
        rows.append({"exp": "Q6a", "case": "rule2 y-edge +%d" % t, "N": N, "M": M,
                     "k_star": k, "sqrt_N_over_M": math.sqrt(N / M),
                     "p_success_qiskit": p_qk, "p_success_numpy": p_np,
                     "classical_expected": (N + 1) / (M + 1)})
        print("Q6a t=%2d  M=%3d  k*=%d  P_numpy=%.4f  P_aer=%s" %
              (t, M, k, p_np, ("%.4f" % p_qk) if HAVE_QISKIT else "n/a"))
        if HAVE_QISKIT and abs(p_np - p_qk) > 1e-9:
            print("WARNING: Aer and numpy disagree", p_np, p_qk)

    # ---------------- Q6a: BBHT, M unknown
    for t in [1, 4, 12]:
        marked = np.flatnonzero(impl_policy(t).table() ^ sigma)
        M = len(marked)
        eq = bbht_expected_queries(marked, NQ)
        rows.append({"exp": "Q6a-BBHT", "case": "rule2 y-edge +%d (M unknown)" % t,
                     "N": N, "M": M, "sqrt_N_over_M": math.sqrt(N / M),
                     "classical_expected": (N + 1) / (M + 1), "bbht_expected_queries": eq})
        print("Q6a-BBHT t=%2d  M=%3d  E[queries]=%.3f" % (t, M, eq))

    # ---------------- Q6b: hidden corner
    n = 8
    checks = verify_hidden_corner_family(n, W)
    print("H(%d) structural checks:" % n, checks)
    if not all(v is True for k_, v in checks.items() if k_ != "n_cover_rules"):
        print("ERROR: structural lemma check failed")
        sys.exit(1)
    corners, cover, members = hidden_corner_family(n, W)
    tables = np.array([m.table() for m in members])
    sigma_min = tables.min(axis=0)           # what the cover rules alone accept
    for hidden in range(n):
        pi = tables[hidden]
        f_struct = [k for k in range(n) if pi[members[0].index(*corners[k])] == 1]
        ks = k_star(n, 1)
        ps_np = grover_success_statevector(n, f_struct, ks)
        ps_qk = grover_qiskit(f_struct, 3, ks) if HAVE_QISKIT else ""
        f_naive = np.flatnonzero(pi ^ sigma_min)
        kn = k_star(N, 1)
        pn_np = grover_success_statevector(N, f_naive, kn)
        pn_qk = grover_qiskit(f_naive, NQ, kn) if HAVE_QISKIT else ""
        rows.append({"exp": "Q6b", "case": "hidden corner K_%d" % (hidden + 1), "N": N,
                     "M": 1, "k_star": ks, "sqrt_N_over_M": math.sqrt(n),
                     "p_success_qiskit": ps_qk, "p_success_numpy": ps_np,
                     "classical_expected": (n + 1) / 2, "naive_k_star": kn,
                     "naive_p_qiskit": pn_qk, "naive_p_numpy": pn_np,
                     "naive_classical_expected": (N + 1) / 2})
        print("Q6b corner %d: structured k*=%d P=%.4f | naive k*=%d P=%.4f" %
              (hidden + 1, ks, ps_np, kn, pn_np))

    out = results / "Q6_real_policy_oracle.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print("wrote", out)


if __name__ == "__main__":
    main()
