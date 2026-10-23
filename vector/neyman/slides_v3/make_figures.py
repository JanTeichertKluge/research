"""Figure for the slides: the moment map M(theta_0, eta_0 + r h) as a function of the amount r along a nuisance direction h.

Both panels are computed by numerical integration over X ~ Uniform(0, 1).
(a) ATE with a binary treatment: propensity score m0(x) = 0.25 + 0.5 x, g0(d, x) = d + 2 x, theta_0 = 1. The nuisance moves
    to g0 + r d and m0 + 0.15 r, and the representer alpha is computed from the moved propensity score.
(b) Partially linear model: m0(x) = E[D | X = x] = x, f0(x) = x^2, theta_0 = 1, l0 = theta_0 m0 + f0.
    The nuisance moves to f0 + r and l0 + r for the outcome nuisances and to m0 + 0.5 r for the treatment regression.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
x = (np.arange(200000) + 0.5) / 200000          # midpoint rule on [0, 1]
r = np.linspace(-1, 1, 201)
E = np.mean

# (a) binary treatment
m0 = 0.25 + 0.5 * x
g1, g0_ = 1 + 2 * x, 2 * x                      # g0(1, x), g0(0, x)
theta0 = 1.0
plug = r * 1.0                                  # <alpha_0, g - g0> with g - g0 = r d
ipw = np.array([E(m0 * g1 / (m0 + 0.15 * s) - (1 - m0) * g0_ / (1 - m0 - 0.15 * s)) - theta0 for s in r])
aipw = np.array([-s * E(m0 / (m0 + 0.15 * s) - 1) for s in r])   # -<g - g0, alpha - alpha0>

# (b) partially linear model
naive = -r * E(x)                               # -E[D (f - f0)] with f - f0 = r
iv = r ** 2 * 0.5                               # <f - f0, m - m0>
po = r ** 2 * 0.5 - theta0 * r ** 2 * 0.25      # <l - l0, m - m0> - theta0 ||m - m0||^2

ORANGE, BLUE, AQUA = "#eb6834", "#2a78d6", "#1baf7a"
GRAY = "#8a8a8a"
plt.rcParams.update({"font.size": 13, "axes.edgecolor": GRAY, "xtick.color": GRAY, "ytick.color": GRAY,
                     "xtick.labelcolor": "black", "ytick.labelcolor": "black", "axes.labelcolor": "black"})
fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))
panels = [
    (axes[0], [(plug, ORANGE, "--", r"naive/plugin"),
               (ipw, AQUA, ":", r"inverse probability weighting, $\alpha(Z)Y-\theta$"),
               (aipw, BLUE, "-", r"AIPW, $\psi_{\mathrm{DR}}$")],
     "(a) ATE with a binary treatment"),
    (axes[1], [(naive, ORANGE, "--", r"naive/plugin"),
               (iv, AQUA, ":", r"instrument $D-m(X)$, score $\psi_{\mathrm{IV}}$"),
               (po, BLUE, "-", r"partialling-out, score $\psi_{\mathrm{PO}}$")],
     "(b) Partially linear model"),
]
for ax, series, title in panels:
    for y, c, ls, lab in series:
        ax.plot(r, y, color=c, ls=ls, lw=2.2, label=lab)
    ax.axhline(0, color=GRAY, lw=0.8)
    ax.axvline(0, color=GRAY, lw=0.8)
    ax.grid(True, color="#dddddd", lw=0.6)
    ax.set_xlabel(r"amount $r$ along the direction $h$")
    ax.set_ylabel(r"$M(\theta_0,\eta_0+rh)$")
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1.25, 1.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=1, frameon=False, labelcolor="black")
    ax.set_title(title, y=-0.78, color="black")
fig.subplots_adjust(left=0.08, right=0.98, top=0.97, bottom=0.45, wspace=0.28)
os.makedirs(os.path.join(HERE, "figures"), exist_ok=True)
out = os.path.join(HERE, "figures", "moment-map.png")
fig.savefig(out, dpi=200)
print("written", out)
print("slopes at 0: plug-in %.3f, IPW %.3f, AIPW %.3f" % (np.gradient(plug, r)[100], np.gradient(ipw, r)[100], np.gradient(aipw, r)[100]))
print("slopes at 0: instrument D %.3f, IV-type %.3f, partialling-out %.3f" % (np.gradient(naive, r)[100], np.gradient(iv, r)[100], np.gradient(po, r)[100]))
