"""Core building blocks shared by all experiments.

- ListedRule: a first-match listed-rule packet-filter policy over the header space [W]^2.
- Grover simulators: exact 2-D closed form and an explicit numpy statevector.
- hidden_corner_family: the H(n) family (2n covering rules + one rule whose corner
  lies on an antichain of n candidate cells).

Everything here is pure numpy; the optional Qiskit Aer cross-check lives in run_q6.py.
"""
import math
import numpy as np


# ---------------------------------------------------------------------------
# Listed-rule policies over [W]^2
# ---------------------------------------------------------------------------
class ListedRule:
    """First-match listed-rule policy over the 2-field header space [W] x [W].

    rules: list of ((x0, x1), (y0, y1), action) with inclusive integer bounds and
           action in {0, 1} (1 = accept). The first rule whose box contains the
           header decides; `default` applies when no rule matches.
    """

    def __init__(self, rules, default=0, width=16):
        self.rules = list(rules)
        self.default = default
        self.W = width

    def __call__(self, x, y):
        for (x0, x1), (y0, y1), action in self.rules:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return action
        return self.default

    def index(self, x, y):
        """Header (x, y) -> integer index in [0, W^2)."""
        return x * self.W + y

    def table(self):
        """Truth table pi(h) for all W^2 headers, indexed by self.index."""
        W = self.W
        t = np.zeros(W * W, dtype=int)
        for x in range(W):
            for y in range(W):
                t[self.index(x, y)] = self(x, y)
        return t


# ---------------------------------------------------------------------------
# Grover
# ---------------------------------------------------------------------------
def grover_success_closed_form(n_items, n_marked, k):
    """P[measure a marked item] after k Grover iterations (exact 2-D rotation formula)."""
    if n_marked <= 0:
        return 0.0
    theta = math.asin(math.sqrt(n_marked / n_items))
    return math.sin((2 * k + 1) * theta) ** 2


def grover_success_statevector(n_items, marked, k):
    """Same quantity from an explicit real statevector (phase oracle + diffusion)."""
    v = np.ones(n_items) / math.sqrt(n_items)
    m = np.zeros(n_items, dtype=bool)
    m[list(marked)] = True
    for _ in range(k):
        v[m] *= -1.0                 # phase oracle
        v = 2.0 * v.mean() - v       # diffusion (inversion about the mean)
    return float((v[m] ** 2).sum())


def k_star(n_items, n_marked=1):
    """Optimal number of Grover iterations floor(pi/4 * sqrt(N/M))."""
    if n_marked <= 0:
        return 0
    return int(math.floor(math.pi / 4.0 * math.sqrt(n_items / n_marked)))


# ---------------------------------------------------------------------------
# Hidden-corner family H(n)
# ---------------------------------------------------------------------------
def hidden_corner_family(n=8, width=16):
    """Build the family H(n) over [width]^2.

    Returns (corners, cover, members) where
      corners : list of n candidate corner cells (a_k, c_k), an antichain
                (a increasing, c decreasing);
      cover   : the 2n known accept rules covering the down-set of every
                candidate corner except the corner cell itself;
      members : list of n ListedRule policies; member k has the extra rule
                R = [0, a_k] x [0, c_k] (accept), i.e. corner k is the true one.
    Requires 2n <= width.
    """
    if 2 * n > width:
        raise ValueError("need 2n <= width")
    corners = [(2 * i + 1, width - 1 - 2 * i) for i in range(n)]
    cover = []
    for (a, c) in corners:
        if a >= 1:
            cover.append(((0, a - 1), (0, c), 1))
        if c >= 1:
            cover.append(((0, a), (0, c - 1), 1))
    members = [ListedRule(cover + [((0, a), (0, c), 1)], default=0, width=width)
               for (a, c) in corners]
    return corners, cover, members


def verify_hidden_corner_family(n=8, width=16):
    """Exhaustively check the structural lemma for H(n):
    the headers on which the members disagree are exactly the n corner cells,
    each corner is accepted by exactly its own member, and the corners form an
    antichain. Returns a dict with the checks (all must be True)."""
    corners, cover, members = hidden_corner_family(n, width)
    tables = np.array([m.table() for m in members])
    varying = np.flatnonzero(tables.min(axis=0) != tables.max(axis=0))
    corner_idx = sorted(members[0].index(a, c) for (a, c) in corners)
    informative_ok = sorted(varying.tolist()) == corner_idx
    accept_ok = all(
        tables[k][members[0].index(*corners[j])] == (1 if j == k else 0)
        for k in range(n) for j in range(n))
    antichain_ok = True
    for i in range(n):
        for j in range(i + 1, n):
            (a1, c1), (a2, c2) = corners[i], corners[j]
            if (a1 <= a2 and c1 <= c2) or (a2 <= a1 and c2 <= c1):
                antichain_ok = False
    return {"informative_set_is_corners": informative_ok,
            "each_corner_accepted_by_own_member": accept_ok,
            "corners_form_antichain": antichain_ok,
            "n_cover_rules": len(cover)}
