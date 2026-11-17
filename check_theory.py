"""Small exhaustive checks: grid-aligned discrepancies (Theorem 6) and the per-rule counter bound (Theorem 1)."""
import itertools, math
import numpy as np

# ---------- Theorem 6: implementations that are not grid-aligned escape the representatives; grid-aligned ones do not ----------
W = 8
def policy(rules, default=0):
    t = np.zeros((W, W), dtype=int) + default
    for (x0, x1), (y0, y1), a in reversed(rules):      # first match wins
        t[x0:x1 + 1, y0:y1 + 1] = a
    return t
rules = [((0, 3), (0, 7), 1), ((2, 6), (2, 5), 0), ((5, 7), (4, 7), 1)]
sigma = policy(rules)
xs = sorted({0, W} | {r[0][0] for r in rules} | {r[0][1] + 1 for r in rules})
ys = sorted({0, W} | {r[1][0] for r in rules} | {r[1][1] + 1 for r in rules})
cells = [((xs[i], xs[i + 1] - 1), (ys[j], ys[j + 1] - 1)) for i in range(len(xs) - 1) for j in range(len(ys) - 1)]
assert all(len(set(sigma[a:b + 1, c:d + 1].ravel())) == 1 for (a, b), (c, d) in cells), "sigma must be constant on its cells"
rep = [(a, c) for (a, b), (c, d) in cells]               # canonical representative = lower corner
# (i) counterexample: pi differs from sigma only at a non-representative header
big = [c for c in cells if (c[0][1] - c[0][0] + 1) * (c[1][1] - c[1][0] + 1) > 1][0]
h = (big[0][1], big[1][1]); assert h not in rep
pi = sigma.copy(); pi[h] ^= 1
g = [pi[r] ^ sigma[r] for r in rep]
print("not grid-aligned: pi != sigma is", bool((pi != sigma).any()), "| discrepancy cells seen via representatives:", sum(g))
# (ii) corrected class: every cell-constant pi != sigma is detected on some representative
C = len(cells); bad = 0
for mask in range(1, 2 ** C):
    pi = sigma.copy()
    for k, ((a, b), (c, d)) in enumerate(cells):
        if mask >> k & 1: pi[a:b + 1, c:d + 1] ^= 1
    if not any(pi[r] != sigma[r] for r in rep): bad += 1
print("cells C =", C, "| cell-constant deviations checked:", 2 ** C - 1, "| undetected:", bad)

# ---------- Theorem 1: Grover against a per-rule counter (hidden rule has its own counter) ----------
def measured_grover(N, T):
    """Uniform start; each oracle call: the counter records hit / no-hit of the hidden header (index 0).
    Returns total P[hit within T queries] + P[no hit, final measurement = hidden header]."""
    s = np.ones(N) / math.sqrt(N); chi = s.copy(); hit = 0.0
    for _ in range(T):
        hit += chi[0] ** 2; chi[0] = 0.0                 # query: branch with a recorded hit leaves
        chi = 2 * s * (s @ chi) - chi                    # diffusion (best the auditor can do between queries)
    return hit + chi[0] ** 2
for N in [256, 4096]:
    for T in [int(math.pi / 4 * math.sqrt(N)), N // 16, N // 4]:
        p = measured_grover(N, T)
        print(f"N={N:5d} T={T:5d}  success with counter = {p:.4f}   bound (4T+2)/N = {min(1,(4*T+2)/N):.4f}   coherent Grover at k* = "
              f"{math.sin((2*int(math.pi/4*math.sqrt(N))+1)*math.asin(1/math.sqrt(N)))**2:.4f}")

# ---------- Proposition 1: candidate families, separation number and symmetry ----------
def separation(F):
    """F: (n, X) 0/1 array, row i = candidate i. Returns (a, primal) with primal = ||J-I|| / max_h ||(J-I) o D_h||."""
    n = F.shape[0]; G = np.ones((n, n)) - np.eye(n)
    a = max(min(int(c), n - int(c)) for c in F.sum(axis=0))
    worst = max(np.linalg.norm(G * (F[:, [h]] != F[:, [h]].T), 2) for h in range(F.shape[1]))
    return a, (n - 1) / worst
def dual_value(F, a):
    """Weight scheme of the proof of Proposition 1(d): queries with split a : n-a, weight 1/a on the small side."""
    n = F.shape[0]; cols = [h for h in range(F.shape[1]) if min(F[:, h].sum(), n - F[:, h].sum()) == a]
    P = np.zeros((n, len(cols)))
    for k, h in enumerate(cols):
        small = F[:, h] == (1 if F[:, h].sum() == a else 0)
        if 2 * a == n: small = F[:, h] == 1
        P[:, k] = np.where(small, 1.0 / a, 1.0 / (n - a))
    P = P / P.sum(axis=1, keepdims=True)
    m = min(sum(math.sqrt(P[i, k] * P[j, k]) for k, h in enumerate(cols) if F[i, h] != F[j, h])
            for i in range(n) for j in range(i))
    return 1.0 / m
n = 16
needle = np.eye(n, dtype=int)                                              # hidden rule: S_n acts on headers
pts = [(x, y, z) for x in (0, 1) for y in (0, 1) for z in (0, 1)]
hyper = np.array([[(p[0] & u[0]) ^ (p[1] & u[1]) ^ (p[2] & u[2]) ^ c for u in pts[1:] for c in (0, 1)] for p in pts])
thresh = np.array([[1 if x <= b else 0 for x in range(n)] for b in range(n)])   # ordered search: no 2-transitive group
print("Proposition 1  (n, a, (n-1)/sqrt(a(n-a)), numerical primal, dual of part (d))")
for name, F, sym in [("hidden rule", needle, True), ("affine hyperplanes", hyper, True), ("thresholds", thresh, False)]:
    nn = F.shape[0]; a, primal = separation(F); formula = (nn - 1) / math.sqrt(a * (nn - a))
    dual = dual_value(F, a) if sym else float("nan")
    print(f"  {name:20s} n={nn:3d} a={a:2d} formula={formula:.4f} primal={primal:.4f} dual={dual:.4f}")
    assert abs(formula - primal) < 1e-9 and (not sym or abs(dual - formula) < 1e-9)


# ---------- Theorem 2: per-rule counters and flipped actions (histogram decoherence) ----------
import collections
def grover_vs_counters(m, T, jstar=0):
    """Grover iteration with a phase oracle against m rules, each with its own hit counter. The environment keeps the
    histogram c of queried rules; branches with different c never interfere. Returns P[output = jstar] when rule jstar
    is flipped, and P[c_jstar > 0] in the run against the unflipped policy."""
    s = np.ones(m) / math.sqrt(m)
    st = {tuple([0] * m): s.copy()}          # flipped rule jstar
    st0 = {tuple([0] * m): s.copy()}         # unflipped policy
    for _ in range(T):
        nw, nw0 = collections.defaultdict(lambda: np.zeros(m)), collections.defaultdict(lambda: np.zeros(m))
        for src, dst, flip in ((st, nw, True), (st0, nw0, False)):
            for c, v in src.items():
                for j in range(m):
                    if v[j] == 0.0: continue
                    c2 = list(c); c2[j] += 1
                    dst[tuple(c2)][j] += (-v[j] if (flip and j == jstar) else v[j])
        st = {c: 2 * s * (s @ v) - v for c, v in nw.items()}
        st0 = {c: 2 * s * (s @ v) - v for c, v in nw0.items()}
    succ = sum(v[jstar] ** 2 for v in st.values())
    hit = sum(v @ v for c, v in st0.items() if c[jstar] > 0)
    return succ, hit
print("Theorem 2  (m, T, Grover-iteration success against counters, blind guess 1/m, bound (T+1)/m, m*H_j <= T)")
for m, Ts in ((8, (1, 2, 3, 4, 5, 6)), (12, (1, 2, 3, 4, 5, 6)), (16, (1, 2, 3, 4, 5, 6))):
    for T in Ts:
        succ, hit = grover_vs_counters(m, T)
        assert abs(succ - 1.0 / m) < 1e-9 and m * hit <= T + 1e-9 and succ <= (T + 1) / m
        print(f"  m={m:2d} T={T}  success={succ:.4f}  1/m={1/m:.4f}  (T+1)/m={(T+1)/m:.4f}  m*H_j={m*hit:.3f}")
