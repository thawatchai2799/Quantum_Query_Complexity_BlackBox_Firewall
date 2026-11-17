"""Regenerate all figures of the paper from the CSV files in results/ (run the experiments first).

Outputs in figures/ (600 dpi PNG, plus a vector PDF of every figure):
  fig1_model_oracles      schematic of the auditing model and the four oracles
  fig2_results_map        which tasks keep a quantum speedup under which oracle
  fig3_Q1_needle          Q1
  fig4_Q3_structure       Q3
  fig5_Q5_hidden_corner   Q5
  fig6_Q6_real_oracle     Q6 (needs results/Q6_real_policy_oracle.csv)
  fig7_Q7_recording       Q7 (needs results/Q7_recording_oracles.csv)
All figures are drawn with matplotlib; no figure contains hand-edited elements.
"""
import csv
import math
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
from matplotlib.colors import ListedColormap

from qfa.core import ListedRule, grover_success_closed_form, hidden_corner_family
from qfa.paths import ensure_dirs

RESULTS, FIGURES = ensure_dirs()

# ---- style: light surface, recessive axes, one colour per entity everywhere
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e4e3df"
SURFACE = "#ffffff"
C_CLASSICAL = "#eb6834"      # classical auditor
C_QUANTUM = "#2a78d6"        # quantum auditor, unitary oracle
C_COUNTER = "#1baf7a"        # quantum auditor, per-rule counter
C_BOUND = "#6250d6"          # proven bounds / reference curves
C_NEUTRAL = "#8a8984"
TINT_BLUE = "#cde2fb"
TINT_GREY = "#ecebe7"
TINT_ORANGE = "#fbe0d4"
WIDTH = 5.46                 # inches = text column of the journal template

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2, "text.color": INK,
    "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6, "lines.linewidth": 1.5,
    "lines.markersize": 3.5, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5,
    "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "mathtext.fontset": "dejavusans",
})


def read_csv(name):
    p = RESULTS / name
    if not p.exists():
        return None
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def num(rows):
    for r in rows:
        for k in r:
            try:
                r[k] = float(r[k])
            except ValueError:
                pass
    return rows


def save(fig, name):
    fig.savefig(str(FIGURES / (name + ".png")), dpi=600, bbox_inches="tight", pad_inches=0.03)
    fig.savefig(str(FIGURES / (name + ".pdf")), bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    print("wrote", FIGURES / (name + ".png"))


q1 = read_csv("Q1_needle.csv")
q3 = read_csv("Q3_structure.csv")
q5 = read_csv("Q5_hidden_corner.csv")
if q1 is None or q3 is None or q5 is None:
    print("results/Q1..Q5 CSV files missing - run run_q1_q3_q5.py first")
    sys.exit(1)
q1, q3, q5 = num(q1), num(q3), num(q5)

# =============================================================================== Fig 1: model
fig, ax = plt.subplots(figsize=(WIDTH, 2.75))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.05)
ax.axis("off")


def node(x, y, w, h, title, lines):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=TINT_GREY, ec=INK2, lw=0.8))
    ax.text(x + w / 2, y + h - 0.32, title, ha="center", va="top", fontsize=8, fontweight="bold")
    ax.text(x + w / 2, y + h - 1.0, lines, ha="center", va="top", fontsize=6.6, color=INK2, linespacing=1.35)


node(0.05, 0.72, 1.95, 4.05, "Auditor", "knows the\nspecification $\\sigma$\n\nclassical or\nquantum")
node(8.0, 0.72, 1.95, 4.05, "Firewall", "unknown policy $\\pi$\n$N = W^{d}$ headers\n\nblack box")
rows_ = [
    (4.45, C_CLASSICAL, "Membership query  $h \\mapsto \\pi(h)$", "one header per query (classical)", False),
    (3.35, C_QUANTUM, "Unitary oracle  $O_{\\pi}|h,b\\rangle = |h,\\, b \\oplus \\pi(h)\\rangle$", "superposition of headers; nothing is recorded", False),
    (2.25, C_COUNTER, "Counter oracle: $O_{\\pi}$, and a per-rule hit counter", "the firewall keeps a hit count for every rule", True),
    (1.15, C_BOUND, "Logging oracle: $O_{\\pi}$, and $h$ is appended to a log", "the firewall keeps the queried header itself", True),
]
for y, col, l1, l2, rec in rows_:
    ax.add_patch(FancyArrowPatch((2.12, y), (7.88, y), arrowstyle="<|-|>", mutation_scale=8, color=col, lw=1.4))
    ax.text(5.0, y + 0.13, l1, ha="center", va="bottom", fontsize=7)
    ax.text(5.0, y - 0.13, l2, ha="center", va="top", fontsize=6.2, color=INK2)
ax.text(5.0, 0.18, "A record kept by the firewall is never accessed by the auditor.", ha="center", va="center", fontsize=6.4, color=INK2, style="italic")
save(fig, "fig1_model_oracles")

# =============================================================================== Fig 2: results map
tasks = ["Hidden rule\n(Theorem 3)", "Witness, $M$ differing headers\n(Theorem 4)", "Localisation, slab family\n(Theorem 5)",
         "Discrepancy among grid\ncells (Theorem 6)", "Certificate replay\n(Theorem 7)", "Hidden corner\n(Theorem 8)"]
cols = ["Classical\nauditor", "unitary\noracle", "per-rule\ncounter", "per-packet\nlog"]
SQ, NO, CL, OP = "sqrt", "none", "classical", "open"
cells = [
    [("$\\Theta(N)$", CL), ("$\\Theta(\\sqrt{N})$", SQ), ("$\\Theta(N)$", CL), ("$\\Theta(N)$", CL)],
    [("$\\Theta(N/M)$", CL), ("$\\Theta(\\sqrt{N/M})$", SQ), ("hidden rule: $\\Theta(N/M)$\n$k$ flips: $\\Theta(m/k)$\nelse: open", OP), ("$\\Theta(N/M)$", CL)],
    [("$\\Theta(m \\log W)$", CL), ("$\\Theta(m \\log W)$", NO), ("$\\Theta(m \\log W)$", NO), ("$\\Theta(m \\log W)$", CL)],
    [("$\\Theta(C/K)$", CL), ("$\\Theta(\\sqrt{C/K})$", SQ), ("open except\nflipped actions", OP), ("$\\Theta(C/K)$", CL)],
    [("$\\Theta(m)$", CL), ("$\\Theta(\\sqrt{m})$", SQ), ("$\\Theta(m)$", CL), ("$\\Theta(m)$", CL)],
    [("$\\Theta(n)$", CL), ("$\\Theta(\\sqrt{n})$", SQ), ("depends on the\nposition of $R$", OP), ("$\\Theta(n)$", CL)],
]
fill = {SQ: TINT_BLUE, NO: TINT_GREY, CL: SURFACE, OP: SURFACE}
fig, ax = plt.subplots(figsize=(WIDTH, 3.75))
ax.axis("off")
x0, cw, rh = 3.3, 1.66, 0.78
ax.set_xlim(0, x0 + 4 * cw + 0.05)
ax.set_ylim(-1.25, 6 * rh + 1.15)
for j, c in enumerate(cols):
    ax.text(x0 + j * cw + cw / 2, 6 * rh + 0.38, c, ha="center", va="center", fontsize=6.4, fontweight="bold")
ax.text(x0 + 2.5 * cw, 6 * rh + 0.95, "Quantum auditor", ha="center", va="center", fontsize=6.8, fontweight="bold")
ax.plot([x0 + cw + 0.06, x0 + 4 * cw - 0.06], [6 * rh + 0.74, 6 * rh + 0.74], color=INK2, lw=0.6)
for i, t in enumerate(tasks):
    y = (5 - i) * rh
    ax.text(0.02, y + rh / 2, t, ha="left", va="center", fontsize=6.8)
    for j, (txt, kind) in enumerate(cells[i]):
        ax.add_patch(Rectangle((x0 + j * cw + 0.04, y + 0.05), cw - 0.08, rh - 0.10, fc=fill[kind], ec=INK2,
                               lw=0.6, ls=(0, (3, 2)) if kind == OP else "-"))
        ax.text(x0 + j * cw + cw / 2, y + rh / 2, txt, ha="center", va="center", fontsize=(4.7 if txt.count("\n") > 1 else 5.7) if "\n" in txt else (6.4 if "open" in txt and "Theta" in txt else 7.2))
leg = [(TINT_BLUE, "-", "square-root speedup"), (TINT_GREY, "-", "no asymptotic speedup (constant factor at most)"),
       (SURFACE, "-", "equal to the classical cost"), (SURFACE, (0, (3, 2)), "not settled in this paper")]
lpos = [(0.02, -0.55), (3.3, -0.55), (0.02, -1.0), (3.3, -1.0)]
for (fc, ls, lab), (x, y) in zip(leg, lpos):
    ax.add_patch(Rectangle((x, y - 0.13), 0.32, 0.26, fc=fc, ec=INK2, lw=0.6, ls=ls))
    ax.text(x + 0.42, y, lab, ha="left", va="center", fontsize=6.3, color=INK2)
save(fig, "fig2_results_map")

# =============================================================================== Fig 3: Q1
fig, ax = plt.subplots(1, 2, figsize=(WIDTH, 2.25))
Ns = [r["N"] for r in q1]
ax[0].plot(Ns, [r["classical_expected"] for r in q1], "o-", color=C_CLASSICAL, label="classical, expected $(N+1)/2$")
ax[0].plot(Ns, [r["grover_iters"] for r in q1], "s-", color=C_QUANTUM, label="Grover, $k^{*} = \\lfloor (\\pi/4)\\sqrt{N} \\rfloor$")
ax[0].set_xscale("log", base=2)
ax[0].set_yscale("log", base=2)
ax[0].set_xlabel("header-space size $N$")
ax[0].set_ylabel("queries")
ax[0].set_title("(a) queries to find the hidden rule", loc="left")
ax[0].legend(loc="upper left")
ks = np.arange(0, 61)
ax[1].plot(ks, [grover_success_closed_form(1024, 1, k) for k in ks], color=C_QUANTUM, label="$N = 2^{10}$")
ax[1].plot(ks, [grover_success_closed_form(4096, 1, k) for k in ks], color=C_QUANTUM, ls="--", label="$N = 2^{12}$")
ax[1].set_xlabel("Grover iterations $k$")
ax[1].set_ylabel("probability of finding the rule")
ax[1].set_title("(b) success probability", loc="left")
ax[1].set_ylim(0, 1.08)
ax[1].legend(loc="upper left")
fig.tight_layout(w_pad=1.6)
save(fig, "fig3_Q1_needle")

# =============================================================================== Fig 4: Q3
fig, ax = plt.subplots(figsize=(WIDTH, 2.6))
ms = sorted({r["m"] for r in q3})
sub = [r for r in q3 if r["log2W"] == 32]
ax.plot(ms, [r["classical_binsearch"] for r in sub], "o-", color=C_CLASSICAL, label="classical binary search, $m \\lceil \\log_{2} W \\rceil$")
ax.plot(ms, [r["quantum_best_known"] for r in sub], "s-", color=C_QUANTUM, label="best known exact quantum algorithm, $\\approx 0.433\\, m \\log_{2} W$")
ax.plot(ms, [r["quantum_lower_bound"] for r in sub], "^-", color=C_BOUND, label="quantum lower bound of Theorem 5 ($\\varepsilon = 1/3$)")
ax.plot(ms, [math.sqrt(m * 32) for m in ms], ":", color=C_NEUTRAL, label="hypothetical $\\sqrt{m \\log_{2} W}$ (excluded for large $m$)")
ax.set_xscale("log", base=2)
ax.set_yscale("log", base=2)
ax.set_xlabel("number of boundaries $m$")
ax.set_ylabel("queries")
ax.set_title("Localising $m$ boundaries, $W = 2^{32}$", loc="left")
ax.set_ylim(2 ** -1.2, 2 ** 20.5)
ax.legend(loc="upper left")
save(fig, "fig4_Q3_structure")

# =============================================================================== Fig 5: Q5
W, n = 16, 8
corners, cover, members = hidden_corner_family(n, W)
tables = np.array([m.table() for m in members])
base = tables.min(0).reshape(W, W)
grid = np.zeros((W, W))
grid[base == 1] = 1
for (a, c) in corners:
    grid[a, c] = 2
hidden = 3
grid[corners[hidden]] = 3
fig = plt.figure(figsize=(WIDTH, 2.55))
ax = fig.add_axes([0.07, 0.17, 0.36, 0.72])
ax.imshow(grid.T, origin="lower", cmap=ListedColormap([SURFACE, TINT_BLUE, C_QUANTUM, C_CLASSICAL]), vmin=0, vmax=3, interpolation="nearest")
ax.set_xticks(np.arange(-0.5, W, 1), minor=True)
ax.set_yticks(np.arange(-0.5, W, 1), minor=True)
ax.grid(which="minor", color=GRID, lw=0.4)
ax.grid(which="major", visible=False)
ax.tick_params(which="minor", length=0)
ax.set_xticks(range(0, 16, 3))
ax.set_yticks(range(0, 16, 3))
for sp in ax.spines.values():
    sp.set_visible(True)
ax.set_xlabel("field $h_{1}$")
ax.set_ylabel("field $h_{2}$")
ax.set_title("(a) the family $\\mathfrak{H}(8)$, $W = 16$", loc="left")
for i, (a, c) in enumerate(corners):
    ax.text(a, c, str(i + 1), ha="center", va="center", fontsize=4.6, color="white", fontweight="bold")
for yy, col, lab in [(14.6, TINT_BLUE, "known rules"), (13.2, C_QUANTUM, "candidates $K_{k}$"), (11.8, C_CLASSICAL, "true corner")]:
    ax.add_patch(Rectangle((8.3, yy - 0.4), 0.8, 0.8, fc=col, ec=INK2, lw=0.4))
    ax.text(9.5, yy, lab, ha="left", va="center", fontsize=5.8, color=INK2)
ax2 = fig.add_axes([0.56, 0.17, 0.42, 0.72])
ns = [r["n"] for r in q5]
ax2.plot(ns, [r["classical_worst"] for r in q5], "o-", color=C_CLASSICAL, label="classical, worst case $n$")
ax2.plot(ns, [r["quantum_iters"] for r in q5], "s-", color=C_QUANTUM, label="Grover over the corners, $\\lfloor (\\pi/4)\\sqrt{n} \\rfloor$")
ax2.plot(ns, [16.0 for _ in ns], "--", color=C_NEUTRAL, label="tree boundary, $\\log_{2} W = 16$")
ax2.set_xscale("log", base=2)
ax2.set_yscale("log", base=2)
ax2.set_xlabel("antichain width $n$")
ax2.set_ylabel("queries to re-localise one rule")
ax2.set_title("(b) cost per rule", loc="left")
ax2.set_ylim(2 ** -0.6, 2 ** 21)
ax2.legend(loc="upper left")
save(fig, "fig5_Q5_hidden_corner")

# =============================================================================== Fig 6: Q6
rows = read_csv("Q6_real_policy_oracle.csv")
if rows is None:
    print("results/Q6_real_policy_oracle.csv missing - run run_q6.py to get fig6")
else:
    a_rows = [r for r in rows if r["exp"] == "Q6a"]
    b_rows = [r for r in rows if r["exp"] == "Q6a-BBHT"]
    c_rows = [r for r in rows if r["exp"] == "Q6b"]
    fig = plt.figure(figsize=(WIDTH, 2.35))
    ax = fig.add_axes([0.065, 0.19, 0.25, 0.66])
    spec = ListedRule([((0, 7), (0, 15), 1), ((8, 15), (0, 3), 1), ((4, 11), (8, 11), 0), ((12, 15), (12, 15), 1)], default=0, width=W)
    impl = ListedRule([((0, 7), (0, 15), 1), ((8, 15), (0, 7), 1), ((4, 11), (8, 11), 0), ((12, 15), (12, 15), 1)], default=0, width=W)
    sig = spec.table().reshape(W, W)
    pim = impl.table().reshape(W, W)
    g = sig.astype(float).copy()
    g[(pim ^ sig) == 1] = 2
    ax.imshow(g.T, origin="lower", cmap=ListedColormap([SURFACE, TINT_BLUE, C_CLASSICAL]), vmin=0, vmax=2, interpolation="nearest")
    ax.set_xticks(np.arange(-0.5, W, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, W, 1), minor=True)
    ax.grid(which="minor", color=GRID, lw=0.4)
    ax.grid(which="major", visible=False)
    ax.tick_params(which="minor", length=0)
    ax.set_xticks(range(0, 16, 5))
    ax.set_yticks(range(0, 16, 5))
    for sp in ax.spines.values():
        sp.set_visible(True)
    ax.set_xlabel("field $h_{1}$")
    ax.set_ylabel("field $h_{2}$")
    ax.set_title("(a) $\\sigma$ and the\n$M = 32$ differing headers", loc="left", fontsize=7)
    ax = fig.add_axes([0.415, 0.19, 0.25, 0.66])
    Ms = [int(r["M"]) for r in a_rows]
    ax.plot(Ms, [float(r["classical_expected"]) for r in a_rows], "o-", color=C_CLASSICAL, label="classical, expected")
    ax.plot([int(r["M"]) for r in b_rows], [float(r["bbht_expected_queries"]) for r in b_rows], "^-", color=C_BOUND, label="quantum, $M$ unknown")
    ax.plot(Ms, [int(r["k_star"]) for r in a_rows], "s-", color=C_QUANTUM, label="Grover, $M$ known")
    ax.plot(Ms, [math.sqrt(256 / m) for m in Ms], ":", color=C_NEUTRAL, label="$\\sqrt{N/M}$")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xlabel("differing headers $M$")
    ax.set_ylabel("queries")
    ax.set_title("(b) witness search,\n$N = 256$", loc="left", fontsize=7)
    ax.set_ylim(0.8, 220)
    ax.legend(loc="upper right", fontsize=5.4, handlelength=1.6, borderaxespad=0.1)
    ax = fig.add_axes([0.765, 0.19, 0.225, 0.66])
    vals = [float(c_rows[0]["naive_classical_expected"]), float(c_rows[0]["naive_k_star"]), float(c_rows[0]["classical_expected"]), float(c_rows[0]["k_star"])]
    labs = ["classical\nall $N$", "Grover\nall $N$", "classical\ncorners", "Grover\ncorners"]
    bars = ax.bar(labs, vals, color=[C_CLASSICAL, C_QUANTUM, C_CLASSICAL, C_QUANTUM], width=0.62)
    for b_, v in zip(bars, vals):
        ax.text(b_.get_x() + b_.get_width() / 2, v * 1.12, "%g" % v, ha="center", va="bottom", fontsize=6)
    ax.set_yscale("log", base=2)
    ax.set_ylim(1, 400)
    ax.grid(axis="x", visible=False)
    ax.set_ylabel("queries")
    ax.set_title("(c) hidden corner,\n$n = 8$, $N = 256$", loc="left", fontsize=7)
    ax.tick_params(axis="x", labelsize=4.9)
    save(fig, "fig6_Q6_real_oracle")

# =============================================================================== Fig 7: Q7
rows = read_csv("Q7_recording_oracles.csv")
if rows is None:
    print("results/Q7_recording_oracles.csv missing - run run_q7.py to get fig7")
else:
    a = num([r for r in rows if r["exp"] == "Q7a"])
    b = num([r for r in rows if r["exp"] == "Q7b"])
    fig, ax = plt.subplots(1, 2, figsize=(WIDTH, 2.9))
    T = [r["T"] for r in a]
    Tc = [r["T"] for r in a if 1 <= r["T"] <= 25]
    ax[0].plot(Tc, [r["p_coherent"] for r in a if 1 <= r["T"] <= 25], color=C_QUANTUM, label="unitary oracle (Grover)")
    ax[0].plot(T, [r["p_counter"] for r in a], color=C_COUNTER, label="per-rule counter (Grover iteration)")
    ax[0].plot(T, [r["p_counter_bound"] for r in a], ":", color=C_BOUND, label="proven limit for the per-rule counter (Theorem 1)")
    ax[0].plot(T, [r["p_classical"] for r in a], "--", color=C_CLASSICAL, label="per-packet log = classical auditor")
    ax[0].set_xscale("log", base=2)
    ax[0].set_xlim(1, 1024)
    ax[0].set_ylim(0, 1.05)
    ax[0].set_xlabel("oracle calls $T$")
    ax[0].set_ylabel("probability of finding the rule")
    ax[0].set_title("(a) $N = 1024$", loc="left")
    Ns = [r["N"] for r in b]
    ax[1].plot(Ns, [r["T_half_classical"] for r in b], "o-", color=C_CLASSICAL, label="per-packet log = classical")
    ax[1].plot(Ns, [r["T_half_counter"] for r in b], "D-", color=C_COUNTER, label="per-rule counter, Grover iteration")
    ax[1].plot(Ns, [r["T_half_counter_lower_bound"] for r in b], ":", color=C_BOUND, label="lower bound of Theorem 1")
    ax[1].plot(Ns, [r["T_half_coherent"] for r in b], "s-", color=C_QUANTUM, label="unitary oracle (Grover)")
    ax[1].set_xscale("log", base=2)
    ax[1].set_yscale("log", base=2)
    ax[1].set_xlabel("header-space size $N$")
    ax[1].set_ylabel("calls for success probability 1/2")
    ax[1].set_title("(b) scaling with $N$", loc="left")
    handles, labels_ = ax[0].get_legend_handles_labels()
    fig.tight_layout(w_pad=1.6, rect=(0, 0.13, 1, 1))
    fig.legend(handles, labels_, loc="lower center", ncol=2, fontsize=6.3, handlelength=2.6, columnspacing=2.0)
    save(fig, "fig7_Q7_recording")

print("all figures done")
