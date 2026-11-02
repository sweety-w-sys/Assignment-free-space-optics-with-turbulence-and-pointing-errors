"""Slide-sized versions of the figures (larger fonts), from results/results.json."""
import sys, os, json
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mt
from matplotlib.lines import Line2D
import run_all as R
from fso_model import SystemParams, OperatingPoint, FIG2_POINTS, logpdf_Z, pdf_Z_approx
from ber import outage_prob, ber_exact, HD_FEC

OUT = os.path.join(HERE, "img")
os.makedirs(OUT, exist_ok=True)
R.FIG = OUT
COL = R.COL
plt.rcParams.update({"font.size": 13, "axes.titlesize": 13, "legend.fontsize": 11,
                     "axes.labelsize": 13, "savefig.dpi": 220})
res = json.load(open(os.path.join(HERE, "..", "results", "results.json")))
p = SystemParams()


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", transparent=False)
    plt.close(fig)


# composite PDF in z, one row
fig, ax = plt.subplots(1, 3, figsize=(12, 3.6), sharey=True)
rng = np.random.default_rng(1)
for a, (name, (ss, r2)) in zip(ax, FIG2_POINTS.items()):
    op = OperatingPoint(ss, r2, p)
    z = op.z_from_h(R.sample_h(1_000_000, op, rng))
    lo = max(-op.kappa - 1.2, -6)
    a.hist(z, bins=np.linspace(lo, 5, 120), density=True, color=COL[name], alpha=0.35, label="Monte Carlo")
    zz = np.linspace(lo, 5, 1500)
    a.plot(zz, np.exp(logpdf_Z(zz, op.kappa)), color=COL[name], lw=2.2, label="exact (10)")
    a.plot(zz, pdf_Z_approx(zz, op.kappa), "k--", lw=1.6, label="approx. (14)")
    a.set_yscale("log"); a.set_ylim(1e-4, 3)
    a.set_title(f"$\\sigma_s$={ss} m, $\\sigma_R^2$={r2}:  $\\kappa$={op.kappa:.1f}")
    a.set_xlabel("z")
ax[0].set_ylabel("PDF"); ax[2].legend(loc="lower center", fontsize=10)
fig.tight_layout(); save(fig, "s_pdf_z")

# BER (Fig 2 right) and panels, instability, area: reuse run_all with bigger fonts
R.fig_ber(res["curves"])
R.fig_ber_panels = None
R.fig_area(p, res["nine_points"])
R.fig_instability(p, {(x["sigma_s"], x["sigma_R2"]): x["D17"] for x in res["nine_points"]})

# green / pink detail panels
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for a, name in zip(axs, ["green", "pink"]):
    c = res["curves"][name]; P = np.array(c["P"]); col = COL[name]
    a.semilogy(P, c["ber16"], color=col, lw=2.4, label="(16) stable, log domain")
    nv = np.array([np.nan if v is None else v for v in c["ber16_naive"]])
    mc = np.array([np.nan if v is None else v for v in c["mc"]])
    a.semilogy(c["Pmc"], mc, "o", mfc="none", color=col, ms=8, label="Monte Carlo")
    if name == "green":
        a.text(-4.5, 1.5e-4, "(16) coded literally:\nNaN at every power", fontsize=12, color="#B03030")
    else:
        a.semilogy(P, c["ber17"], "k--", lw=1.6, label=r"(17), start $10^{-6}$ above $\hat h$")
        a.semilogy(P, c["ber17_delta01"], color="0.45", ls="-.", lw=1.6, label=r"(17), start $0.1$ above $\hat h$")
    a.axhline(HD_FEC, color="k", lw=0.9)
    a.set_title(f"{name}: $\\sigma_s$={c['sigma_s']} m, $\\sigma_R^2$={c['sigma_R2']}, $\\kappa$={c['kappa']:.1f}")
    a.set_xlabel("P [dBm]"); a.set_ylim(1e-4, 3e-1); a.set_xlim(-5, 11)
    a.legend(loc="upper right", fontsize=10)
axs[0].set_ylabel("average BER")
fig.tight_layout(); save(fig, "s_green_pink")

# outage
fig, ax = plt.subplots(figsize=(7, 4.6))
P = np.arange(-5, 25.01, 0.1)
for name, (ss, r2) in FIG2_POINTS.items():
    op = OperatingPoint(ss, r2, p)
    ax.semilogy(P, outage_prob(P, op), color=COL[name], lw=2.4, label=f"{name}: outage")
    ax.semilogy(P, ber_exact(P, op), color=COL[name], lw=1.3, ls="--")
ax.axhline(1e-3, color="0.4", lw=0.8, ls=":")
ax.axhline(HD_FEC, color="k", lw=0.8)
ax.set_ylim(1e-7, 1); ax.set_xlim(-5, 24)
ax.set_xlabel("P [dBm]"); ax.set_ylabel(r"$P_{\rm out}$ (solid),  $\bar P_b$ (dashed)")
ax.legend(loc="lower left", fontsize=10)
save(fig, "s_outage")

# interleaver
il = res["interleaver"]
fig, ax = plt.subplots(figsize=(7, 4.6))
for name in FIG2_POINTS:
    ax.semilogx(il["N"], il[name]["required"], "o-", color=COL[name], lw=2, ms=6, label=name)
    ax.axhline(il[name]["P_inf"], color=COL[name], ls="--", lw=1)
ax.axvline(130, color="0.5", lw=0.8, ls=":")
ax.text(140, 12.3, r"$N\approx\frac{1/2}{3.84\cdot10^{-3}}$", fontsize=11, color="0.3")
ax.set_xlabel("interleaver depth N (independent fades per codeword)")
ax.set_ylabel("required P [dBm]")
ax.legend(fontsize=10, loc="lower left")
ax.xaxis.set_major_formatter(mt.FormatStrFormatter("%g"))
save(fig, "s_interleaver")

# equations as images
import subprocess, tempfile
from PIL import Image


def eq(name, tex, size=22):
    """Render a display equation with pdflatex (standalone) and make the
    white background transparent."""
    d = tempfile.mkdtemp()
    doc = (r"\documentclass[border=2pt,varwidth=30cm]{standalone}\usepackage{amsmath,amssymb}"
           r"\begin{document}\Large " + tex + r"\end{document}")
    open(os.path.join(d, "e.tex"), "w").write(doc)
    subprocess.run(["pdflatex", "-interaction=nonstopmode", "e.tex"], cwd=d,
                   stdout=subprocess.DEVNULL, check=True)
    subprocess.run(["pdftoppm", "-png", "-r", "400", "-singlefile", "e.pdf", "e"], cwd=d, check=True)
    im = Image.open(os.path.join(d, "e.png")).convert("L")
    rgba = Image.new("RGBA", im.size, (20, 27, 45, 0))
    rgba.putalpha(im.point(lambda v: 255 - v))
    rgba.save(os.path.join(OUT, name + ".png"))

eq("eq_z", r"$z=\dfrac{\ln\frac{h}{A_0h_l}+2\sigma_X^2}{2\sigma_X}=W-E',\quad W\sim\mathcal{N}(0,1),\ E'\sim\mathrm{Exp}(\kappa),\quad \kappa=\gamma^2\sigma_R$")
eq("eq_10", r"(10):$\quad f_Z(z)=\kappa\,e^{\kappa z+\kappa^2/2}\,Q(z+\kappa)$")
eq("eq_14", r"(14):$\quad f_Z(z)\approx\dfrac{\phi(z)}{1+z/\kappa},\quad z>-\kappa\ (h>\hat h)$")
eq("eq_nan", r"$\underbrace{e^{2\sigma_X^2\gamma^2(1+\gamma^2)}}_{e^{2353}}\cdot\underbrace{(A_0h_l)^{-\gamma^2}}_{e^{465}}\cdot\underbrace{h^{\gamma^2-1}}_{e^{-458}}\cdot\underbrace{\mathrm{erfc}(\cdot)}_{e^{-2319}}\ \to\ \infty\cdot 0=\mathrm{NaN}$", 20)
eq("eq_log", r"$\ln f_Z=\ln\kappa+\kappa z+\frac{\kappa^2}{2}+\ln Q(z+\kappa)$", 20)
eq("eq_area", r"area$(14)\approx 1+\frac{1}{\kappa^2}+\frac{3}{\kappa^4}+\kappa\phi(\kappa)\ln\frac{1}{\delta}$", 20)
eq("eq_out", r"$P_{\rm out}=\Pr\{h<h_{\rm th}\}=\Phi(z_{\rm th})+e^{\kappa z_{\rm th}+\kappa^2/2}Q(z_{\rm th}+\kappa)$", 20)
print("ok")
