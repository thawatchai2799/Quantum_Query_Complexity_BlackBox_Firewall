"""Regenerate all figures from the CSV files in results/ (run the experiments first).

Outputs (600 dpi PNG) in figures/:
  fig1_model_oracles.png, fig2_advantage_landscape.png, fig3_Q1_needle.png,
  fig4_Q3_structure.png, fig5_Q5_hidden_corner.png, fig6_Q6_real_oracle.png
fig6 requires results/Q6_real_policy_oracle.csv (run_q6.py); it is skipped otherwise.
"""
import csv
import math
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.colors import ListedColormap

from qfa.core import ListedRule, grover_success_closed_form, hidden_corner_family
from qfa.paths import ensure_dirs

RESULTS, FIGURES = ensure_dirs()
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
BG = "#070b1e"
FG = "#e8ecff"


def dark(ax):
    ax.set_facecolor(BG)
    for s in ax.spines.values():
        s.set_color("#5560a0")
    ax.tick_params(colors=FG)
    ax.xaxis.label.set_color(FG); ax.yaxis.label.set_color(FG); ax.title.set_color(FG)
    ax.grid(color="#2a3060", lw=0.5, alpha=0.7)


def stars(ax, n=300, seed=1):
    r = np.random.default_rng(seed)
    x0, x1 = ax.get_xlim(); y0, y1 = ax.get_ylim()
    ax.scatter(r.uniform(x0, x1, n), r.uniform(y0, y1, n), s=r.uniform(0.2, 2, n),
               c="white", alpha=0.35, zorder=0)


def read_csv(name):
    p = RESULTS / name
    if not p.exists():
        return None
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def save(fig, name, **kw):
    out = FIGURES / name
    fig.savefig(str(out), bbox_inches="tight", facecolor=BG, **kw)
    plt.close(fig)
    print("wrote", out)


grover_success = grover_success_closed_form
q1 = read_csv("Q1_needle.csv"); q3 = read_csv("Q3_structure.csv"); q5 = read_csv("Q5_hidden_corner.csv")
if q1 is None or q3 is None or q5 is None:
    print("results/Q1..Q5 CSV files missing - run run_q1_q3_q5.py first"); sys.exit(1)
for r in q1:
    for k in r: r[k] = float(r[k]) if r[k] not in ("", "nan") else float("nan")
for r in q3:
    for k in r: r[k] = float(r[k])
for r in q5:
    for k in r: r[k] = float(r[k])
# ================= FIGURES =================
# Fig1: model / three oracles
fig,ax=plt.subplots(figsize=(7.2,3.6),dpi=600); fig.patch.set_facecolor(BG); ax.set_xlim(0,10); ax.set_ylim(0,5); ax.axis("off"); stars(ax,400)
def box(x,y,w,h,txt,c,fs=8):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.05,rounding_size=0.15",fc=c,ec="white",lw=0.8,alpha=0.95))
    ax.text(x+w/2,y+h/2,txt,ha="center",va="center",color="white",fontsize=fs,fontweight="bold")
box(0.3,1.6,2.2,1.8,"Auditor\n(classical or\nquantum)","#4b2b8a")
box(7.5,1.6,2.2,1.8,"Firewall $\\pi$\n(black box)\n$W^d=2^{104}$ headers","#8a2b5c")
cols=["#1fb6a3","#f2a63b","#e04c6a"]
labels=["MQ oracle  $q\\mapsto\\pi(q)$  (classical, one header per query)",
        "Counter oracle  $q\\mapsto(\\pi(q),\\,\\mathrm{hit}(q))$  = the query is recorded",
        "Quantum oracle  $O_\\pi|q,b\\rangle=|q,b\\oplus\\pi(q)\\rangle$  (coherent superposition)"]
for i,(c,l) in enumerate(zip(cols,labels)):
    y=3.9-i*1.4
    ax.add_patch(FancyArrowPatch((2.6,y),(7.4,y),arrowstyle="<|-|>",mutation_scale=12,color=c,lw=2))
    ax.text(5,y+0.22,l,ha="center",va="bottom",color=c,fontsize=7.2)
ax.text(5,0.25,"Lemma 1: counter oracle $\\equiv$ measurement of the query register  $\\Rightarrow$  no quantum advantage",ha="center",color=FG,fontsize=7.5,style="italic")
save(fig, "fig1_model_oracles.png")

# Fig2: advantage landscape (4 rows)
fig,ax=plt.subplots(figsize=(7.2,4.8),dpi=600); fig.patch.set_facecolor(BG); dark(ax); ax.grid(False)
rows=[("Needle (hidden rule)\nunstructured", "$\\Theta(N)$", "$\\Theta(\\sqrt{N})=2^{52}$", 1.0),
      ("Non-equivalence witness\n$M$ differing headers", "$\\Theta(N/M)$", "$\\Theta(\\sqrt{N/M})$", 1.0),
      ("Certificate replay\n$m$ rules", "$\\Theta(m)$", "$\\Theta(\\sqrt{m})$ queries, $|S|=\\Theta(m)$", 0.5),
      ("Structured (tree / disjoint list)\nlocalise $m$ boundaries", "$\\Theta(m\\log W)$", "$\\Omega(m\\log W)$ — no $\\sqrt{\\;}$", 0.0),
      ("Hidden corner (overlapping list)\nlocalise 1 rule, antichain $n$", "$\\Omega(n)$", "$\\Theta(\\sqrt{n})$", 1.0)]
ax.set_xlim(0,10); ax.set_ylim(-0.5,4.6); ax.set_yticks([]); ax.set_xticks([])
cmap=plt.get_cmap("plasma")
for i,(name,cl,qu,adv) in enumerate(rows):
    y=4-i
    ax.add_patch(FancyBboxPatch((0.15,y-0.42),9.7,0.84,boxstyle="round,pad=0.02,rounding_size=0.2",fc=cmap(0.15+0.7*adv),ec="none",alpha=0.85))
    ax.text(0.4,y,name,va="center",ha="left",color="white",fontsize=7,fontweight="bold")
    ax.text(4.9,y,cl,va="center",ha="center",color="white",fontsize=9)
    ax.text(7.9,y,qu,va="center",ha="center",color="white",fontsize=8.5)
ax.text(4.9,4.62,"classical",ha="center",va="bottom",color=FG,fontsize=8,fontweight="bold")
ax.text(7.9,4.62,"quantum",ha="center",va="bottom",color=FG,fontsize=8,fontweight="bold")
ax.text(0.4,4.62,"auditing task",ha="left",va="bottom",color=FG,fontsize=8,fontweight="bold")
ax.set_ylim(-0.6,5.0)
sm=plt.cm.ScalarMappable(cmap=cmap,norm=plt.Normalize(0,1)); cb=fig.colorbar(sm,ax=ax,fraction=0.03,pad=0.02); cb.set_label("quantum advantage (exponent gain)",color=FG,fontsize=7); cb.ax.yaxis.set_tick_params(color=FG); plt.setp(cb.ax.get_yticklabels(),color=FG,fontsize=6); cb.set_ticks([0,0.5,1]); cb.set_ticklabels(["none","half","full $\\sqrt{\\;}$"])
save(fig, "fig2_advantage_landscape.png")

# Fig3: Q1 needle
fig,ax=plt.subplots(1,2,figsize=(7.2,3.0),dpi=600); fig.patch.set_facecolor(BG)
for a in ax: dark(a)
Ns=[r["N"] for r in q1]; ax[0].plot(Ns,[r["classical_expected"] for r in q1],"o-",color="#f2a63b",ms=3,label="classical expected $(N+1)/2$")
ax[0].plot(Ns,[r["grover_iters"] for r in q1],"s-",color="#1fb6a3",ms=3,label="Grover iterations $\\lfloor\\frac{\\pi}{4}\\sqrt{N}\\rfloor$")
ax[0].set_xscale("log",base=2); ax[0].set_yscale("log",base=2); ax[0].set_xlabel("$N$ (header-space size)"); ax[0].set_ylabel("queries"); ax[0].legend(fontsize=6,facecolor=BG,labelcolor=FG,edgecolor="#5560a0"); ax[0].set_title("(a) needle: queries vs $N$",fontsize=8)
N=1024; ks=np.arange(0,60); ax[1].plot(ks,[grover_success(N,1,k) for k in ks],color="#e04c6a",lw=1.4,label="exact statevector, $N=2^{10}$")
ax[1].plot(ks,[grover_success(4096,1,k) for k in ks],color="#8f7bff",lw=1.4,label="$N=2^{12}$")
ax[1].axhline(1,color="#5560a0",lw=0.6); ax[1].set_xlabel("Grover iterations $k$"); ax[1].set_ylabel("P[hit hidden rule]"); ax[1].legend(fontsize=6,facecolor=BG,labelcolor=FG,edgecolor="#5560a0"); ax[1].set_title("(b) success probability oscillates: measure at $k^*$",fontsize=8)
fig.tight_layout(); save(fig, "fig3_Q1_needle.png")

# Fig4: Q3 structure
fig,ax=plt.subplots(figsize=(7.2,3.2),dpi=600); fig.patch.set_facecolor(BG); dark(ax)
ms=[4,16,64,256,1024]
for W,c in zip([2**16,2**32,2**52],["#1fb6a3","#f2a63b","#e04c6a"]):
    sub=[r for r in q3 if r["W"]==W]
    ax.plot(ms,[r["classical_binsearch"] for r in sub],"o-",color=c,ms=3,label=f"classical binary search, $W=2^{{{int(math.log2(W))}}}$")
    ax.plot(ms,[0.32*m*math.log2(W) for m in ms],"-",color=c,lw=0.9,alpha=0.8,label=("best quantum algorithm $0.32\\,m\\log_2 W$ [BH08] (thin solid)" if W==2**16 else None))
    ax.plot(ms,[r["quantum_lower_bound"] for r in sub],"--",color=c,lw=1,label=("quantum lower bound, Thm 3 with $\\varepsilon=1/3$ (dashed)" if W==2**16 else None))
ax.plot(ms,[math.sqrt(m*52) for m in ms],":",color="#8f7bff",lw=1.5,label="hypothetical $\\sqrt{m\\log W}$ (does not exist)")
ax.set_xscale("log",base=2); ax.set_yscale("log",base=2); ax.set_xlabel("$m$ (rules / boundaries)"); ax.set_ylabel("queries"); ax.legend(fontsize=5.5,ncol=2,facecolor=BG,labelcolor=FG,edgecolor="#5560a0"); ax.set_title("Structure beats superposition: both scale as $m\\log W$ (constant gap only)",fontsize=8)
save(fig, "fig4_Q3_structure.png")

# ---- Fig 5 ----
W=16; n=8
corners, cover, members = hidden_corner_family(n, W)
tables=np.array([m.table() for m in members])
base=tables.min(0).reshape(W,W)
grid=np.zeros((W,W)); grid[base==1]=1
for (a,c) in corners: grid[a,c]=2
hidden=3; grid[corners[hidden]]=3
fig=plt.figure(figsize=(7.2,3.3),dpi=600); fig.patch.set_facecolor(BG)
ax=fig.add_subplot(1,2,1); dark(ax); ax.grid(False)
cm=ListedColormap(["#0e1440","#1f7a70","#8f7bff","#e04c6a"])
ax.imshow(grid.T,origin="lower",cmap=cm,vmin=0,vmax=3,interpolation="nearest")
ax.set_xlabel("$h_1$"); ax.set_ylabel("$h_2$"); ax.set_title("(a) hidden-corner family $\\mathfrak{H}(8)$, $W=16$",fontsize=8)
ax.set_xticks(range(0,16,3)); ax.set_yticks(range(0,16,3))
for i,(a,c) in enumerate(corners): ax.text(a,c,str(i+1),ha="center",va="center",fontsize=5,color="white",fontweight="bold")
ax.text(8,0.6,"teal: covered by the 2n known accept rules\npurple: candidate corners $K_1..K_n$ (antichain)\nred: the true corner of rule $R$ (accept)",fontsize=5.6,color=FG,ha="center",va="bottom",bbox=dict(fc=BG,ec="#5560a0",lw=0.5))
# ---- (b) queries vs n
ax2=fig.add_subplot(1,2,2); dark(ax2)
ns=[int(r["n"]) for r in q5]
ax2.plot(ns,[float(r["classical_worst"]) for r in q5],"o-",color="#f2a63b",ms=3,label="classical: $\\Omega(n)$ (Thm 5)")
ax2.plot(ns,[int(r["quantum_iters"]) for r in q5],"s-",color="#1fb6a3",ms=3,label="quantum: Grover on the antichain $\\Theta(\\sqrt{n})$")
ax2.plot(ns,[math.log2(1<<16) for _ in ns],"--",color="#8f7bff",lw=1.2,label="tree / disjoint list, per boundary: $\\log_2 W$ ($W=2^{16}$)")
ax2.set_xscale("log",base=2); ax2.set_yscale("log",base=2); ax2.set_xlabel("$n$ (antichain width, $n \\leq W$)"); ax2.set_ylabel("queries to localise one rule"); ax2.legend(fontsize=5.5,facecolor=BG,labelcolor=FG,edgecolor="#5560a0",loc="upper left"); ax2.set_title("(b) per-rule cost: overlapping list vs tree",fontsize=8)
fig.tight_layout(); save(fig, "fig5_Q5_hidden_corner.png")

# ---- Fig 6: Q6 ----
rows=read_csv("Q6_real_policy_oracle.csv")
if rows is None:
    print("results/Q6_real_policy_oracle.csv missing - run run_q6.py to get fig6"); sys.exit(0)
a_rows=[r for r in rows if r["exp"]=="Q6a"]; b_rows=[r for r in rows if r["exp"]=="Q6a-BBHT"]; c_rows=[r for r in rows if r["exp"]=="Q6b"]
fig=plt.figure(figsize=(7.2,3.3),dpi=600); fig.patch.set_facecolor(BG)
# (a) spec policy map with differing headers for t=4
ax=fig.add_subplot(1,3,1); dark(ax); ax.grid(False)
spec=ListedRule([((0,7),(0,15),1),((8,15),(0,3),1),((4,11),(8,11),0),((12,15),(12,15),1)],default=0,width=W); sig=spec.table().reshape(W,W)
impl=ListedRule([((0,7),(0,15),1),((8,15),(0,7),1),((4,11),(8,11),0),((12,15),(12,15),1)],default=0,width=W); pi=impl.table().reshape(W,W)
g=sig.astype(float).copy(); g[(pi^sig)==1]=2
ax.imshow(g.T,origin="lower",cmap=ListedColormap(["#0e1440","#1f7a70","#e04c6a"]),vmin=0,vmax=2,interpolation="nearest")
ax.set_title("(a) Q6a: $\\sigma$ (teal=accept) and\nthe $M=32$ headers where $\\pi\\neq\\sigma$ (red)",fontsize=7); ax.set_xlabel("$h_1$"); ax.set_ylabel("$h_2$"); ax.set_xticks(range(0,16,5)); ax.set_yticks(range(0,16,5))
# (b) queries vs M
ax=fig.add_subplot(1,3,2); dark(ax)
Ms=[int(r["M"]) for r in a_rows]
ax.plot(Ms,[float(r["classical_expected"]) for r in a_rows],"o-",color="#f2a63b",ms=3,label="classical E[queries] $(N+1)/(M+1)$")
ax.plot(Ms,[int(r["k_star"]) for r in a_rows],"s-",color="#1fb6a3",ms=3,label="Grover $k^*$, $M$ known")
ax.plot([int(r["M"]) for r in b_rows],[float(r["bbht_expected_queries"]) for r in b_rows],"^-",color="#e04c6a",ms=3,label="BBHT E[queries], $M$ unknown")
ax.plot(Ms,[math.sqrt(256/m) for m in Ms],":",color="#8f7bff",lw=1.2,label="$\\sqrt{N/M}$")
ax.set_xscale("log",base=2); ax.set_yscale("log",base=2); ax.set_xlabel("$M$ (differing headers)"); ax.set_ylabel("queries"); ax.set_title("(b) Q6a: witness search, $N=256$",fontsize=7); ax.legend(fontsize=4.8,facecolor=BG,labelcolor=FG,edgecolor="#5560a0")
# (c) Q6b bars
ax=fig.add_subplot(1,3,3); dark(ax); ax.grid(axis="x",alpha=0)
vals=[float(c_rows[0]["naive_classical_expected"]),int(c_rows[0]["naive_k_star"]),float(c_rows[0]["classical_expected"]),int(c_rows[0]["k_star"])]
labs=["classical\nall $N$","Grover\nall $N$","classical\n$n$ corners","Grover\n$n$ corners"]
bars=ax.bar(labs,vals,color=["#f2a63b","#1fb6a3","#f2a63b","#1fb6a3"],edgecolor="white",lw=0.5)
for b_,v in zip(bars,vals): ax.text(b_.get_x()+b_.get_width()/2,v*1.15,f"{v:g}",ha="center",color=FG,fontsize=6)
ax.set_yscale("log",base=2); ax.set_ylabel("queries (expected / $k^*$)"); ax.set_title("(c) Q6b: hidden corner, $n=8$, $N=256$",fontsize=7); ax.tick_params(axis="x",labelsize=5.5)
fig.tight_layout(); save(fig, "fig6_Q6_real_oracle.png")
print("all figures done")
