# Quantum Query Complexity of Black-Box Firewall Auditing — Simulation Artefact

This repository contains the simulation code, the raw results (CSV) and the figure
scripts accompanying the paper *When the Record Kills the Speedup: Quantum Query
Complexity of Black-Box Firewall Auditing* (companion to *The Price of Auditing a
Firewall: Query Complexity of Black-Box Verification for Listed-Rule and Tree-Rule
Policies*).

Everything is small: the whole pipeline runs in about one minute on a laptop.

## What is computed

| Experiment | Script | What it does | Output |
|---|---|---|---|
| Q1 needle | `run_q1_q3_q5.py` | Grover on N = 2^4 … 2^20 items with one marked item; k* = ⌊(π/4)√N⌋, success probability from the closed form and (up to N = 2^14) from an explicit statevector; classical expectation (N+1)/2 | `results/Q1_needle.csv` |
| Q3 structure | `run_q1_q3_q5.py` | Cost of localising m boundaries of width W: classical binary search m·log₂W, best known exact quantum ordered search 4·log₆₀₅W ≈ 0.433·log₂W per boundary, and the adversary/direct-sum lower bound with error 1/3 | `results/Q3_structure.csv` |
| Q5 hidden corner | `run_q1_q3_q5.py` | Grover over an antichain of n = 2^2 … 2^16 candidate cells vs. classical n | `results/Q5_hidden_corner.csv` |
| Q6a witness | `run_q6.py` | A 4-rule first-match listed-rule policy over [16]² (N = 256, 8 qubits) is compiled into a phase oracle; the implementation shifts one rule edge by t cells; Grover finds a header where the two policies differ (M known), plus the BBHT schedule for unknown M (mean and standard error over 2000 runs) | `results/Q6_real_policy_oracle.csv` |
| Q6b hidden corner | `run_q6.py` | The eight members of the hidden-corner family H(8) are compiled; the structural lemma (informative headers = the 8 corner cells, antichain) is checked exhaustively; Grover over the 8 corners vs. naive Grover over all 256 headers | `results/Q6_real_policy_oracle.csv` |
| Q7 recording oracles | `run_q7.py` | Search for a hidden rule when the firewall records the query: a per-rule hit counter (exact evolution of the branch in which no hit has been recorded) and a per-packet log (classical), compared with the unitary oracle; success probability versus calls for N = 1024, calls needed for success 1/2 for N = 2^6 … 2^16, and a cross-check in which the counter is a real register (one qubit per call) on Qiskit Aer for N = 16 | `results/Q7_recording_oracles.csv` |
| Theory checks | `check_theory.py` | Exhaustive check of the grid-aligned discrepancy statement on a small policy, a counterexample for implementations that are not grid-aligned, and the counter-oracle success probabilities against the proven bound (4T+2)/N, and the separation-number formula for the adversary value on three small candidate families, and the Grover iteration against per-rule counters of a flipped rule (histogram decoherence), which returns the blind-guess probability 1/m | printed |
| Figures | `make_figures.py` | Figures 1–7 of the paper (600 dpi PNG and vector PDF), all drawn with matplotlib | `figures/` |

Q6 success probabilities are computed with the Qiskit Aer statevector simulator **and**
with an independent numpy statevector implementation; both columns are in the CSV and
agree to about 1e-14. The Q7 counter-register circuit agrees with the numpy evolution to about 1e-16. If Qiskit is not installed the Aer column is left empty and only
the numpy column is produced.

## Requirements

* Python 3.9 or newer (tested with 3.12)
* `numpy`, `matplotlib` (Q1/Q3/Q5 and all figures)
* `qiskit`, `qiskit-aer` (only for the Aer cross-checks in Q6 and Q7; tested with Qiskit 2.5 / Aer 0.17 and Qiskit 2.6 / Aer 0.18)

Install everything with

```
pip install -r requirements.txt
```

## How to run

From the repository root (Windows PowerShell / cmd, Linux or macOS — all paths are
resolved relative to the scripts, so no path separators need editing):

```
python run_all.py            # Q1/Q3/Q5, Q6, Q7, then all figures  (~1 min)
python run_all.py --no-q6    # skip Q6 (Figure 6 is then not produced)
```

or step by step:

```
python run_q1_q3_q5.py       # seconds   -> results/Q1_*.csv, Q3_*.csv, Q5_*.csv
python run_q6.py             # ~1 minute -> results/Q6_real_policy_oracle.csv
python run_q7.py             # seconds   -> results/Q7_recording_oracles.csv
python check_theory.py       # seconds   -> prints the checks
python make_figures.py       # seconds   -> figures/*.png
```

To force the numpy-only path (no Qiskit call), set the environment variable
`QFA_NO_QISKIT=1` before running `run_q6.py` or `run_q7.py`.

`run_q6.py` aborts with a non-zero exit code if the exhaustive structural check of the
hidden-corner family fails; a successful run prints
`H(8) structural checks: {... True, ... True, ... True, 'n_cover_rules': 16}`.

## Expected numbers (spot checks)

* Q1: N = 2^12 → k* = 50, P[success] = 0.99995; N = 2^20 → k* = 804.
* Q3: W = 2^52, m = 256 → classical 13 312, best known exact quantum 5 762.3, lower bound 163.3; the ratio classical / best known quantum is 2.31 for every W and m.
* Q5: n = 2^16 → k* = 201.
* Q6a: t = 1 → M = 8, k* = 4, P = 0.9992; t = 4 → M = 32, k* = 2, P = 0.9453; t = 12 → M = 80 (not 96, because the shifted region runs into a rule that already accepts). BBHT expected queries (seed 0): 10.505 ± 0.119 / 5.3355 ± 0.079 / 3.061 ± 0.049 for t = 1 / 4 / 12.
* Q7: N = 1024, T = 25 calls → success 0.9995 (unitary oracle), 0.0940 (per-rule counter), 0.0254 (classical = per-packet log); calls for success 1/2 at N = 2^16: 101 (unitary), 11 357 (counter, 0.173·N), 32 767 (classical); proven lower bound for the counter 8 191.5. Counter register on Aer versus numpy: difference below 1e-15.
* Q6b: structured Grover over the 8 corners: k* = 2, P = 0.9453; naive Grover over 256 headers: k* = 12, P = 0.9999; classical expectations 4.5 and 128.5.

All Grover quantities are deterministic (no sampling), so they must reproduce exactly.
The only randomised part is the BBHT schedule in Q6a, which uses a fixed seed.
There are no shots: every probability is read from a state vector or a closed form.

## Layout

```
run_all.py            run everything
run_q1_q3_q5.py       Q1, Q3, Q5 (numpy only)
run_q6.py             Q6a, Q6b (Qiskit Aer + numpy)
run_q7.py             Q7 (numpy; counter-register cross-check on Qiskit Aer)
check_theory.py       small exhaustive checks of two statements
make_figures.py       Figures 1-7
qfa/core.py           ListedRule policy engine, Grover simulators, hidden-corner family H(n)
qfa/paths.py          output directories (results/, figures/)
requirements.txt
results/              CSV outputs (regenerated by the scripts)
figures/              PNG and PDF outputs (regenerated by the scripts)
```

## Model in one paragraph

A policy is a first-match list of boxes with actions over the header space [W]^d
(here d = 2, W = 16 for the compiled examples). The quantum oracle is the unitary
O_π|h,b⟩ = |h, b⊕π(h)⟩; for a search task the function π⊕σ (or the corner
indicator) is turned into a phase oracle as a diagonal ±1 matrix, and Grover's
algorithm is run against it. The hidden-corner family H(n) consists of 2n known accept
rules that cover the down-set of each candidate corner cell except the cell itself,
plus one rule whose corner is one of the n candidates; the members disagree only on
the n corner cells, which form an antichain, so localising the rule is unstructured
search of size n.

A firewall may also keep a record of each query. A per-rule hit counter is modelled as a
register that is incremented for the matched rule and never read by the auditor; a
per-packet log as a register to which the queried header is appended. `run_q7.py`
follows the branch of the state in which the counter of the hidden rule is still zero.

## License

MIT (see `LICENSE`).
