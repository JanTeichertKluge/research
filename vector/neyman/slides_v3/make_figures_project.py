"""Figures of the slides on the current project, from the records and facts of experiments/implicit_weights.

sensitivity.png: the sensitivity S_alpha along the Riesz representer and the root mean square bias of the plug-in
estimate against n, for the small networks (0.2M parameters) and the large networks of each backbone (4.9M) at the end
of training, averaged over the evaluated checkpoints with one record per checkpoint (results/summary_all.json).
larger.png: S_alpha, the root mean square bias and the mean standard deviation of the plug-in estimate of the eight large
networks of seed 1000 at the end of training at n = 100 to 2,000, and S_alpha of the plug-in estimate of Gaussian
process regressions per arm with fixed hyperparameters at the same truths and data sets (notes/facts_scale.json).
released.png: S_alpha and the root mean square bias at n = 500 of the large networks and of the released networks
(notes/facts_released.json).
level.png: the larger of the two pooled rejection rates at n = 250 and 500 of the block test with q = 4 for the two
estimators with zero sensitivity on the small networks, along the estimated representer, the representer with the
propensity clipped to [0.1, 0.9] and to [0.3, 0.7], and the overlap direction (2d - 1) m(1 - m)
(notes/facts_e13_interim.json and notes/facts_e13_level_pilot.json).
estimand.png: the correlation over truths between the per-truth mean share of the plug-in estimate and S_alpha at
n = 500 on the small networks, along the true representer and along the directions of the tests
(notes/facts_e13_pilot.json, and the records of results/e13/ for the true representer).
"""

from __future__ import annotations

import json
import os
import sys
from collections import defaultdict

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
IW = os.path.join(HERE, "..", "..", "experiments", "implicit_weights")
NOTES = os.path.join(IW, "notes")
BLUE, ORANGE, GREEN, PURPLE = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
GRAY = "#8a8a8a"
plt.rcParams.update({"font.size": 13, "axes.edgecolor": GRAY, "xtick.color": GRAY, "ytick.color": GRAY,
                     "xtick.labelcolor": "black", "ytick.labelcolor": "black", "axes.labelcolor": "black",
                     "text.color": "black"})
PRIORS = [("train", "training prior", BLUE), ("hard", "strong confounding", ORANGE)]
# With --small, the figures show only the small networks and are written with the suffix _small.
SMALL = "--small" in sys.argv


def out(name):
    return os.path.join(HERE, "figures", name.replace(".png", "_small.png") if SMALL else name)


def style(ax, grid="y"):
    ax.grid(True, axis=grid, color="#dddddd", lw=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def bars(ax, groups, series, width=0.36, fmt="{:.3f}", offset=0.004):
    """Grouped bars with the value above each bar; series is a list of (label, color, values)."""
    x = np.arange(len(groups))
    for k, (label, color, values) in enumerate(series):
        pos = x + (k - (len(series) - 1) / 2) * width
        ax.bar(pos, values, width=width - 0.04, color=color, label=label, zorder=2)
        for p, v in zip(pos, values, strict=True):
            ax.text(p, v + (offset if v >= 0 else -offset), fmt.format(v), ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=10.5, color="black")
    ax.set_xticks(x, groups)
    style(ax)


def sensitivity_figure():
    rows = json.load(open(os.path.join(IW, "results", "summary_all.json")))
    g, seen = defaultdict(list), set()
    for r in rows:
        c, key = r["checkpoint"], (r["prior"], r["estimator"], r["n"])
        if (c,) + key in seen:  # the same checkpoint and cell recorded by two experiments
            continue
        if c.startswith("p4r_final"):
            g[(c.split("/")[2].split("_")[0],) + key].append(r)
        elif c.startswith("seed") and "/e5/" not in r["source"] and "/e6/" not in r["source"]:
            g[("small",) + key].append(r)
        else:
            continue
        seen.add((c,) + key)

    def mean(cells, key):
        vals = [c[key] for c in cells if c[key] is not None]
        return float(np.mean(vals)) if vals else np.nan

    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), sharex=True)
    series = [("small", "small networks, 0.2M parameters", PURPLE, "s"),
              ("tabpfn", "large networks, nanoTabPFN backbone, 4.9M", BLUE, "o"),
              ("tabicl", "large networks, nanoTabICL backbone, 4.9M", ORANGE, "D")]
    if SMALL:
        series = series[:1]
    panels = [("s_alpha", r"sensitivity $S_\alpha$"), ("rms_bias", r"RMS bias (sd$(Y)$ units)")]
    ns = [100, 250, 500]
    for j, (prior, ptitle) in enumerate((("train", "training prior"), ("hard", "strong confounding"))):
        for i, (key, ylabel) in enumerate(panels):
            ax = axes[i, j]
            for grp, label, color, marker in series:
                ax.plot(ns, [mean(g[(grp, prior, "plugin", n)], key) for n in ns], color=color, marker=marker,
                        ms=8, lw=2, label=label)
            if key == "s_alpha":
                ax.axhline(0, color=GRAY, lw=1, ls="--")
                ax.set_ylim(-0.5, 0.05)
            else:
                ax.set_ylim(0, 0.4)
            ax.set_xscale("log")
            ax.set_xticks(ns, [str(n) for n in ns])
            ax.minorticks_off()
            ax.set_ylabel(ylabel if j == 0 else "")
            style(ax, grid="both")
            if i == 1:
                ax.set_xlabel(f"$n$\n({'ab'[j]}) {ptitle}")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=len(series), frameon=False, bbox_to_anchor=(0.5, 0.0),
               fontsize=12)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.97, bottom=0.2, hspace=0.12, wspace=0.18)
    fig.savefig(out("sensitivity.png"), dpi=200)


def larger_figure():
    f = json.load(open(os.path.join(NOTES, "facts_scale.json")))
    ns = [100, 250, 500, 2000]
    fig, axes = plt.subplots(2, 2, figsize=(12, 7.6), sharex=True)
    for j, (prior, ptitle) in enumerate((("train", "training prior"), ("hard", "strong confounding"))):
        cells = [f[f"trend/seed1000/{prior}/plugin/{n}"] for n in ns]
        ax = axes[0, j]
        ax.plot(ns, [c["s_alpha"] for c in cells], color=BLUE, marker="o", ms=8, lw=2,
                label="large networks, plug-in estimate")
        ax.plot(ns, [f[f"final/tabicl/{prior}/plugin/{n}"]["gp_s_alpha"] for n in ns], color=GREEN, marker="s",
                ms=8, lw=2, label="Gaussian process regression per arm, plug-in estimate")
        ax.axhline(0, color=GRAY, lw=1, ls="--")
        ax.set_ylim(-0.5, 0.05)
        ax.set_ylabel(r"sensitivity $S_\alpha$" if j == 0 else "")
        ax = axes[1, j]
        ax.plot(ns, [c["rms_bias"] for c in cells], color=BLUE, marker="o", ms=8, lw=2)
        ax.plot(ns, [c["sd"] for c in cells], color=PURPLE, marker="D", ms=7, lw=2, ls="--",
                label="large networks, mean standard deviation of the plug-in estimate")
        ax.set_ylim(0, 0.14)
        ax.set_ylabel("RMS bias and standard\ndeviation (sd$(Y)$ units)" if j == 0 else "")
        ax.set_xlabel(f"$n$\n({'ab'[j]}) {ptitle}")
        for ax in axes[:, j]:
            ax.set_xscale("log")
            ax.set_xticks(ns, [f"{n:,}" for n in ns])
            ax.minorticks_off()
            style(ax, grid="both")
    handles, labels = [], []
    for ax in (axes[0, 0], axes[1, 0]):
        h, lab = ax.get_legend_handles_labels()
        handles += h
        labels += lab
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=12)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.97, bottom=0.22, hspace=0.12, wspace=0.18)
    fig.savefig(os.path.join(HERE, "figures", "larger.png"), dpi=200)


def released_figure():
    f = json.load(open(os.path.join(NOTES, "facts_released.json")))
    networks = [("our large\nnetworks", None), ("CausalPFN", "causalpfn"), ("CausalFM", "causalfm"), ("Do-PFN", "dopfn")]
    if SMALL:
        networks = networks[1:]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
    for ax, key, own_key, ylabel, panel in (
            (axes[0], "s_alpha", "stage1_s_alpha", r"$S_\alpha$", r"(a) sensitivity $S_\alpha$"),
            (axes[1], "rms_bias", "stage1_rms_bias", "RMS bias (sd$(Y)$ units)", "(b) RMS bias over truths")):
        series = [(label, color, [f[f"causalpfn/{prior}/500"][own_key] if m is None else f[f"{m}/{prior}/500"][key]
                                  for _, m in networks]) for prior, label, color in PRIORS]
        bars(ax, [n for n, _ in networks], series, fmt="{:.2f}", offset=0.012)
        ax.axhline(0, color=GRAY, lw=0.8)
        ax.set_ylabel(ylabel)
        ax.set_xlabel(panel)
        ax.tick_params(axis="x", labelsize=11.5)
    axes[0].set_ylim(-0.85, 0.05)
    axes[1].set_ylim(0, 0.95)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.08, right=0.98, top=0.97, bottom=0.27, wspace=0.25)
    fig.savefig(out("released.png"), dpi=200)


def level_figure():
    first = json.load(open(os.path.join(NOTES, "facts_e13_interim.json")))["pilot"]["level"]["rates"]
    later = json.load(open(os.path.join(NOTES, "facts_e13_level_pilot.json")))["pilot"]["level"]["rates"]
    large = json.load(open(os.path.join(NOTES, "facts_e13.json")))["stage1"]["level"]["rates"]
    panels = [("(a) small networks", [("$\\hat\\alpha_{0.01}$, estimated\nrepresenter", later, "t_q4"),
                                      ("$\\hat\\alpha_{0.1}$, clipped\nrepresenter", first, "t_q4_clip"),
                                      ("$\\hat\\alpha_{0.3}$, clipped\nrepresenter", later, "t_q4_clip"),
                                      ("$h_{\\mathrm{o}}$, overlap\ndirection", later, "t_q4_bnd")]),
              ("(b) large networks", [("$\\hat\\alpha_{0.01}$, estimated\nrepresenter", large, "t_q4"),
                                      ("$\\hat\\alpha_{0.3}$, clipped\nrepresenter", large, "t_q4_clip"),
                                      ("$h_{\\mathrm{o}}$, overlap\ndirection", large, "t_q4_bnd")])]
    estimators = (("aipw_cf_alpha0", r"AIPW, true $\alpha_0$, outcome regression of the network cross-fitted", GREEN),
                  ("aipw_oracle", "AIPW, true nuisances", PURPLE))
    if SMALL:
        panels = panels[:1]
        fig, ax0 = plt.subplots(1, 1, figsize=(10, 5.8))
        axes = [ax0]
    else:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.8), sharey=True, gridspec_kw={"width_ratios": [4, 3.3]})
    for ax, (title, directions) in zip(axes, panels, strict=True):
        series = [(label, color, [max(rates[f"{test}/{est}/{n}"]["pooled"] for n in (250, 500))
                                  for _, rates, test in directions]) for est, label, color in estimators]
        bars(ax, [d[0] for d in directions], series)
        ax.axhline(0.05, color=GRAY, lw=1, ls=":", label="nominal level 5%")
        if not SMALL:
            ax.axhline(0.07, color=GRAY, lw=1.2, ls="--", label="threshold of criterion (1), 7%")
        ax.set_xlim(-0.6, len(directions) - 0.4)
        ax.set_xlabel(title)
        ax.tick_params(axis="x", labelsize=11)
    axes[0].set_ylim(0, 0.115)
    axes[0].set_ylabel("rejection rate, pooled over priors")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.97, bottom=0.3, wspace=0.06)
    fig.savefig(out("level.png"), dpi=200)


def estimand_figure():
    sys.path.insert(0, IW)
    import summarise_e13 as s  # noqa: E402

    cwd = os.getcwd()
    os.chdir(IW)
    try:
        oracle = {g: s.estimand(s.load(g), ("share_alpha0", "s_alpha"))
                  for g in (("pilot",) if SMALL else ("pilot", "stage1"))}
    finally:
        os.chdir(cwd)
    facts = json.load(open(os.path.join(NOTES, "facts_e13.json")))
    groups = (("pilot", "(a) small networks"), ("stage1", "(b) large networks"))
    if SMALL:
        fig, ax0 = plt.subplots(1, 1, figsize=(10, 5.6))
        axes, groups = [ax0], (("pilot", "small networks"),)
    else:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.6), sharey=True)
    for ax, (group, title) in zip(axes, groups, strict=True):
        est = facts[group]["estimand"]
        directions = [("$\\alpha_0$, true\nrepresenter", oracle[group]),
                      ("$\\hat\\alpha_{0.01}$, estimated\nrepresenter", est["sel"]),
                      ("$\\hat\\alpha_{0.3}$, clipped\nrepresenter", est["clip"]),
                      ("$h_{\\mathrm{o}}$, overlap\ndirection", est["bnd"])]
        series = [(label, color, [d[1][prior]["corr"] for d in directions]) for prior, label, color in PRIORS]
        bars(ax, [d[0] for d in directions], series, fmt="{:.2f}", offset=0.02)
        if not SMALL:
            ax.axhline(0.8, color=GRAY, lw=1.2, ls="--")
        ax.axhline(0, color=GRAY, lw=0.8)
        ax.set_xlim(-0.6, 3.6)
        ax.set_xlabel(title)
        ax.tick_params(axis="x", labelsize=10.5)
    if not SMALL:
        axes[1].text(3.58, 0.815, "threshold 0.8", ha="right", va="bottom", fontsize=10.5, color="black")
    axes[0].set_ylim(-0.6, 1.12)
    axes[0].set_ylabel(r"correlation with $S_\alpha$ over truths")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.subplots_adjust(left=0.08, right=0.99, top=0.97, bottom=0.25, wspace=0.06)
    fig.savefig(out("estimand.png"), dpi=200)


def main():
    os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
    sensitivity_figure()
    if not SMALL:
        larger_figure()
    released_figure()
    level_figure()
    estimand_figure()
    if SMALL:
        print("written figures/sensitivity_small.png, released_small.png, level_small.png and estimand_small.png")
    else:
        print("written figures/sensitivity.png, larger.png, released.png, level.png and estimand.png")


if __name__ == "__main__":
    main()
