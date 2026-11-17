"""Q7: what a recording firewall does to Grover search for a hidden rule.

Three oracles are compared on the needle family (one hidden single-header rule among N headers):

  coherent      the unitary oracle O_pi (no record)                      -> Grover, closed form
  counter       a per-rule hit counter: every call records whether the   -> exact branch simulation
                hidden rule was hit (Theorem 1)
  log           a per-packet log: every call records the queried header  -> exact (Lemma 1)

For the counter oracle the auditor runs the Grover iteration (the natural strategy); the
success probability is the probability that a hit has been recorded within T calls plus the
probability that the final measurement returns the hidden header. The proven bound is
(4T + 2)/N. For the log oracle the best possible strategy is classical: (T + 1)/N.

Q7a  success probability versus T for N = 1024.
Q7b  smallest T with success >= 1/2 versus N = 2^6 .. 2^16.
Q7c  cross-check of the counter simulation with a circuit in which the counter is a real
     register (one fresh qubit per call), on the Qiskit Aer statevector simulator (N = 16).

Writes results/Q7_recording_oracles.csv. Runs in a few seconds (plus Aer start-up).
"""
import csv
import math
import os
import warnings

import numpy as np

from qfa.core import grover_success_closed_form
from qfa.paths import ensure_dirs

warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    from qiskit import QuantumCircuit, transpile
    from qiskit_aer import AerSimulator
    HAVE_QISKIT = True
except Exception as _e:  # ImportError or version problems
    HAVE_QISKIT = False
    QISKIT_IMPORT_ERROR = "%s: %s" % (type(_e).__name__, _e)
if os.environ.get("QFA_NO_QISKIT"):
    HAVE_QISKIT = False


def counter_success(N, T):
    """Grover iteration against the per-rule counter oracle, hidden header = index 0.
    Returns the list p[0..T], p[t] = P[hit recorded within t calls] + P[no hit, measure hidden header]."""
    s = np.ones(N) / math.sqrt(N)
    chi = s.copy()                       # unnormalised no-hit branch
    hit = 0.0
    out = [chi[0] ** 2]
    for _ in range(T):
        hit += chi[0] ** 2               # the call records a hit with this probability
        chi[0] = 0.0                     # ... and that branch leaves the no-hit component
        chi = 2.0 * s * (s @ chi) - chi  # diffusion
        out.append(hit + chi[0] ** 2)
    return out


def log_success_grover(N, T):
    """Grover iteration against the per-packet log oracle (every call measures the header).
    By symmetry the state after a call is a basis state; track P[found] exactly."""
    found = 0.0
    p_star = 1.0 / N                     # probability that the measured header is the hidden one
    alive = 1.0
    out = [1.0 / N]
    for _ in range(T):
        found += alive * p_star          # the call reads the hidden header: answer 1, found
        alive *= (1.0 - p_star)
        # diffusion applied to a basis state |h>, h != hidden, then next call measures again
        p_star = (2.0 / N) ** 2
        out.append(found + alive * p_star)
    return out


def classical_success(N, T):
    return min(1.0, (T + 1) / N)         # T distinct probes, then a guess among the rest


def first_T(curve, level=0.5):
    for t, p in enumerate(curve):
        if p >= level:
            return t
    return None


def aer_counter_success(nq, T):
    """Counter as a real register: one fresh qubit per call, flipped iff the query register holds
    the hidden header |0...0>. Success = P[some counter qubit is 1] + P[all 0 and register = hidden]."""
    N = 2 ** nq
    qc = QuantumCircuit(nq + T)
    q = list(range(nq))
    qc.h(q)
    for t in range(T):
        qc.x(q)
        qc.mcx(q, nq + t)                # record the hit in counter qubit t
        qc.x(q)
        # diffusion 2|s><s| - I on the query register
        qc.h(q)
        qc.x(q)
        qc.h(q[-1])
        qc.mcx(q[:-1], q[-1])
        qc.h(q[-1])
        qc.x(q)
        qc.h(q)
    qc.save_statevector()
    sim = AerSimulator(method="statevector")
    sv = np.asarray(sim.run(transpile(qc, sim)).result().get_statevector())
    probs = np.abs(sv) ** 2
    idx = np.arange(len(probs))
    counter_bits = idx >> nq
    query_bits = idx & (N - 1)
    return float(probs[counter_bits != 0].sum() + probs[(counter_bits == 0) & (query_bits == 0)].sum())


COLUMNS = ["exp", "N", "T", "p_coherent", "p_counter", "p_counter_bound", "p_log_grover", "p_classical",
           "T_half_coherent", "T_half_counter", "T_half_classical", "T_half_counter_lower_bound", "p_counter_aer"]


def main():
    results, _ = ensure_dirs()
    rows = []

    # ---- Q7a
    N = 1024
    Tmax = N
    cnt = counter_success(N, Tmax)
    logg = log_success_grover(N, Tmax)
    for T in sorted(set(list(range(0, 65)) + list(range(64, Tmax + 1, 16)))):
        rows.append({"exp": "Q7a", "N": N, "T": T, "p_coherent": grover_success_closed_form(N, 1, T),
                     "p_counter": cnt[T], "p_counter_bound": min(1.0, (4 * T + 2) / N),
                     "p_log_grover": logg[T], "p_classical": classical_success(N, T)})
    kstar = int(math.floor(math.pi / 4 * math.sqrt(N)))
    print("Q7a N=%d: at T=k*=%d  coherent %.4f | counter %.4f | bound %.4f | classical %.4f | Grover under log %.4f"
          % (N, kstar, grover_success_closed_form(N, 1, kstar), cnt[kstar], (4 * kstar + 2) / N,
             classical_success(N, kstar), logg[kstar]))

    # ---- Q7b
    for e in range(6, 17):
        N = 2 ** e
        coh = [grover_success_closed_form(N, 1, t) for t in range(int(math.sqrt(N)) + 2)]
        c = counter_success(N, N)
        t_coh, t_cnt = first_T(coh), first_T(c)
        t_cl = math.ceil(N / 2) - 1
        lb = max(0.0, (N / 2 - 2) / 4)
        rows.append({"exp": "Q7b", "N": N, "T_half_coherent": t_coh, "T_half_counter": t_cnt,
                     "T_half_classical": t_cl, "T_half_counter_lower_bound": lb})
        print("Q7b N=2^%-2d  T(1/2): coherent %4d | counter %6d (%.3f N) | classical %6d | proven lower bound %.1f"
              % (e, t_coh, t_cnt, t_cnt / N, t_cl, lb))

    # ---- Q7c
    print("Qiskit Aer available:", HAVE_QISKIT)
    if not HAVE_QISKIT and "QISKIT_IMPORT_ERROR" in globals():
        print("  (import failed:", QISKIT_IMPORT_ERROR, ")")
    nq = 4
    c16 = counter_success(2 ** nq, 8)
    worst = 0.0
    for T in range(0, 9):
        p_aer = aer_counter_success(nq, T) if HAVE_QISKIT else ""
        rows.append({"exp": "Q7c", "N": 2 ** nq, "T": T, "p_counter": c16[T], "p_counter_aer": p_aer,
                     "p_counter_bound": min(1.0, (4 * T + 2) / 2 ** nq)})
        if HAVE_QISKIT:
            worst = max(worst, abs(p_aer - c16[T]))
    if HAVE_QISKIT:
        print("Q7c N=16, T=0..8: max |Aer - numpy| = %.2e" % worst)

    out = results / "Q7_recording_oracles.csv"
    with open(out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in COLUMNS})
    print("wrote", out)


if __name__ == "__main__":
    main()
