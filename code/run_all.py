"""
run_all.py
==========
Runs every numerical part of the assignment and writes figures + numbers.

    python run_all.py            # full run (~10-15 min)
    python run_all.py --quick    # fewer Monte Carlo bits, for a smoke test

Outputs (in ../figures and ../results):
  fig_model_check     MC histograms vs eqs. (5), (7), (10), (14)
  fig_instability     where eq. (10) breaks numerically + the 9 points (Fig. 2 left)
  fig_ber             Fig. 2 (right) reproduction: MC, (16), (17), (18)
  fig_ber_panels      same, one panel per operating point, with naive (16)
  fig_area            area under (14) vs delta and Delta vs kappa (Task 3)
  fig_outage          stretch (b): outage probability vs average BER
  fig_interleaver     "what next": required power vs interleaver depth
  results.json        every number quoted in the report and slides
"""

import argparse
import json
import os
import time

import numpy as np
import matplotlib
import matplotlib.ticker
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from fso_model import (SystemParams, OperatingPoint, FIG2_POINTS, GRID_SIGMA_S,
                       GRID_SIGMA_R2, PAPER_DELTA_17, sample_ha, sample_hp,
                       sample_h, pdf_ha, pdf_hp, pdf_H_naive, pdf_H_stable,
                       logpdf_Z, pdf_Z_approx, dBm_to_W)
from ber import (HD_FEC, cond_ber, ber_exact, ber_exact_naive, ber_approx17,
                 ber_approx18, ber_remedy, area_approx, area_remedy,
                 divergence_rate, lost_mass, outage_prob, crossing_dBm)
from montecarlo import simulate_ber, simulate_outage

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..", "figures")
RES = os.path.join(HERE, "..", "results")
os.makedirs(FIG, exist_ok=True)
os.makedirs(RES, exist_ok=True)

COL = {"green": "#2E9E44", "yellow": "#D99A00", "pink": "#D6337F"}
plt.rcParams.update({
    "font.size": 10, "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": True, "legend.fancybox": False, "legend.framealpha": 1.0,
    "legend.edgecolor": "black", "legend.facecolor": "white", "savefig.bbox": "tight", "savefig.dpi": 200,
})


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"))
    plt.close(fig)


# ==========================================================================
# 0. System numbers
# ==========================================================================
def system_numbers(p):
    d = dict(wz=p.wz, v=p.v, A0=p.A0, wzeq=p.wzeq, hl=p.hl, A0hl=p.A0 * p.hl)
    d["Cn2"] = {str(r): p.Cn2_from_rytov(r) for r in GRID_SIGMA_R2}
    d["points"] = {}
    for ss in GRID_SIGMA_S:
        for r2 in GRID_SIGMA_R2:
            op = OperatingPoint(ss, r2, p)
            d["points"][f"{ss}_{r2}"] = dict(
                sigma_s=ss, sigma_R2=r2, gamma2=op.g2, sX2=op.sX2, mu=op.mu,
                hhat=op.hhat, kappa=op.kappa, big_exponent=op.big_exponent,
                theta_s_mrad=ss / p.L * 1e3)
    return d


# ==========================================================================
# 1. Model check: MC histograms vs PDFs
# ==========================================================================
def fig_model_check(p, rng, n=2_000_000):
    fig, ax = plt.subplots(3, 3, figsize=(11, 8.6))
    for j, (name, (ss, r2)) in enumerate(FIG2_POINTS.items()):
        op = OperatingPoint(ss, r2, p, name)
        # row 1: turbulence h_a vs eq. (5)
        a = ax[0, j]
        ha = sample_ha(n, op, rng)
        bins = np.linspace(np.quantile(ha, 1e-4), np.quantile(ha, 1 - 1e-4), 120)
        a.hist(ha, bins=bins, density=True, color=COL[name], alpha=0.35,
               label=r"MC $h_a$")
        x = np.linspace(bins[0], bins[-1], 400)
        a.plot(x, pdf_ha(x, op), color=COL[name], lw=1.8, label="eq. (5)")
        a.set_xlabel(r"$h_a$")
        a.set_title(f"{name}: $\\sigma_s$={ss} m, $\\sigma_R^2$={r2}", fontsize=10)
        a.legend(fontsize=7)
        # row 2: pointing h_p/A0 vs eq. (7)
        a = ax[1, j]
        hp = sample_hp(n, op, rng) / p.A0
        bins2 = np.linspace(np.quantile(hp, 1e-4), 1, 120)
        a.hist(hp, bins=bins2, density=True, color=COL[name], alpha=0.35,
               label=r"MC $h_p/A_0$ (Rayleigh $R$ via (6))")
        x2 = np.linspace(bins2[0], 1, 400)
        a.plot(x2, pdf_hp(x2 * p.A0, op) * p.A0, color=COL[name], lw=1.8,
               label=f"eq. (7), $\\gamma^2$={op.g2:.1f}")
        a.set_xlabel(r"$h_p/A_0$")
        a.legend(fontsize=7, loc="upper left")
        # row 3: composite, in the standardised log variable z
        b = ax[2, j]
        h = sample_h(n, op, rng)
        z = op.z_from_h(h)
        bins = np.linspace(np.quantile(z, 1e-5), np.quantile(z, 1 - 1e-6), 150)
        b.hist(z, bins=bins, density=True, color=COL[name], alpha=0.35,
               label="MC $h=h_l h_p h_a$")
        zz = np.linspace(min(bins[0], -op.kappa - 0.5), bins[-1], 1200)
        b.plot(zz, np.exp(logpdf_Z(zz, op.kappa)), color=COL[name], lw=1.8,
               label="eq. (10), stable")
        b.plot(zz, pdf_Z_approx(zz, op.kappa), "k--", lw=1.2, label="eq. (14)")
        b.axvline(-op.kappa, color="0.4", lw=0.8, ls=":")
        b.set_yscale("log")
        b.set_ylim(1e-5, 2)
        b.set_xlim(max(-op.kappa - 1.5, -8), 5.5)
        b.set_xlabel(r"$z=(\ln(h/A_0h_l)+2\sigma_X^2)/(2\sigma_X)$")
        b.set_title(f"$\\kappa=\\gamma^2\\sigma_R$ = {op.kappa:.1f}"
                    + ("" if op.kappa > 8 else r"  (dotted: $z=-\kappa$, i.e. $\hat h$)"),
                    fontsize=10)
        b.legend(fontsize=7, loc="lower center")
    ax[0, 0].set_ylabel("PDF")
    ax[1, 0].set_ylabel("PDF")
    ax[2, 0].set_ylabel("PDF of z (log scale)")
    fig.tight_layout()
    save(fig, "fig_model_check")


# ==========================================================================
# 2. Numerical instability of eq. (10) (Fig. 2 left)
# ==========================================================================
def naive_fails(op):
    """True if eq. (10), coded literally, returns non-finite values or
    loses the density (0 where the true PDF is > 1e-12) on the bulk of h."""
    z = np.linspace(-op.kappa - 4, 5, 400)
    h = op.h_from_z(z)
    with np.errstate(all="ignore"):
        f_naive = pdf_H_naive(h, op)
        f_true = pdf_H_stable(h, op)
        bad = ~np.isfinite(f_naive)
        rel = np.abs(f_naive - f_true) / f_true
        bad |= (f_true * h > 1e-12) & ~(rel < 1e-6)
    return bool(np.any(bad))


def fig_instability(p, delta_grid):
    ss = np.linspace(0.10, 0.36, 131)
    r2 = np.linspace(0.02, 1.2, 119)
    fail = np.zeros((len(r2), len(ss)))
    for i, r in enumerate(r2):
        for j, s in enumerate(ss):
            fail[i, j] = naive_fails(OperatingPoint(s, r, p))
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    ax.contourf(ss, r2, fail, levels=[-0.5, 0.5, 1.5],
                colors=["#DCE8F5", "#F6D2D2"])
    # overflow boundary 2 sX2 g2 (1+g2) = ln(DBL_MAX)
    S, R = np.meshgrid(ss, r2)
    BE = np.vectorize(lambda s, r: OperatingPoint(s, r, p).big_exponent)(S, R)
    ax.contour(ss, r2, BE, levels=[np.log(np.finfo(float).max)],
               colors="#B03030", linewidths=1.2, linestyles="--")
    K = np.vectorize(lambda s, r: OperatingPoint(s, r, p).kappa)(S, R)
    cs = ax.contour(ss, r2, K, levels=[2.5, 5, 10, 20, 40],
                    colors="0.45", linewidths=0.7)
    ax.clabel(cs, fmt=lambda v: f"$\\kappa$={v:g}", fontsize=7)
    for (s, r), d in delta_grid.items():
        c = "#1F5AA6"
        for name, pt in FIG2_POINTS.items():
            if pt == (s, r):
                c = COL[name]
        ax.scatter([s], [r], s=40 + 400 * min(d, 0.6), color=c, alpha=0.8,
                   edgecolor="k", lw=0.5, zorder=3)
        ax.annotate(f"{d:.3f} dB", (s, r), xytext=(6, 6),
                    textcoords="offset points", fontsize=7)
    ax.axhline(1.0, color="k", lw=0.8)
    ax.text(0.30, 1.08, r"strong turbulence ($\sigma_R^2>1$)", fontsize=8,
            ha="center", bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.8))
    ax.text(0.103, 0.80, "eq. (10)\nfails\n(inf·0 = nan)", color="#B03030",
            fontsize=8, bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.8))
    ax.set_xlabel(r"$\sigma_s$ [m]")
    ax.set_ylabel(r"$\sigma_R^2$")
    ax.set_title(r"Where eq. (10) breaks; $\Delta$ of eq. (17) at HD-FEC "
                 r"($\delta=10^{-6}$)", fontsize=10)
    ax.set_xlim(ss[0], ss[-1]); ax.set_ylim(r2[0], r2[-1])
    save(fig, "fig_instability")
    return fail


# ==========================================================================
# 3. BER curves (Fig. 2 right)
# ==========================================================================
def ber_curves(p, rng, n_bits):
    P = np.arange(-5, 11.01, 0.1)
    Pmc = np.arange(-5, 11.01, 1.0)
    out = {}
    for name, (ss, r2) in FIG2_POINTS.items():
        op = OperatingPoint(ss, r2, p, name)
        t0 = time.time()
        b16 = ber_exact(P, op)
        b16n = ber_exact_naive(Pmc, op)
        b17 = ber_approx17(P, op, delta=1e-6)
        b17_01 = ber_approx17(P, op, delta=0.1)
        b18 = ber_approx18(P, op, delta=1e-6)
        brem = ber_remedy(P, op)
        keep = ber_exact(Pmc, op) > 3e-6          # only simulate where meaningful
        mc = np.full(len(Pmc), np.nan)
        nerr = np.zeros(len(Pmc), int)
        nsim = np.zeros(len(Pmc), int)
        mc[keep], nerr[keep], nsim[keep] = simulate_ber(
            Pmc[keep], op, n_bits, rng, min_errors=None)
        out[name] = dict(
            P=P.tolist(), Pmc=Pmc.tolist(), ber16=b16.tolist(),
            ber16_naive=[None if not np.isfinite(v) else v for v in b16n],
            ber17=b17.tolist(), ber17_delta01=b17_01.tolist(),
            ber18=b18.tolist(), ber_remedy=brem.tolist(),
            mc=[None if not np.isfinite(v) else v for v in mc],
            mc_errors=nerr.tolist(), mc_bits=nsim.tolist(),
            P16=crossing_dBm(P, b16), P17=crossing_dBm(P, b17),
            P17_d01=crossing_dBm(P, b17_01), P18=crossing_dBm(P, b18),
            Prem=crossing_dBm(P, brem),
            Pmc_cross=crossing_dBm(Pmc[keep], mc[keep]),
            sigma_s=ss, sigma_R2=r2, kappa=op.kappa, runtime_s=time.time() - t0)
        o = out[name]
        o["D17"] = o["P17"] - o["P16"]
        o["D17_d01"] = o["P17_d01"] - o["P16"]
        o["D18"] = o["P18"] - o["P16"]
        o["Drem"] = o["Prem"] - o["P16"]
        o["Dmc"] = o["Pmc_cross"] - o["P16"]
        print(f"  {name}: P16={o['P16']:.3f} dBm  D17={o['D17']:.3f}  "
              f"D18={o['D18']:.3f}  MC-exact={o['Dmc']:+.3f} dB")
    return out


def fig_ber(curves):
    fig, ax = plt.subplots(figsize=(6.6, 4.8))
    for name, c in curves.items():
        P = np.array(c["P"])
        col = COL[name]
        ax.semilogy(P, c["ber16"], color=col, lw=1.8)
        ax.semilogy(P, c["ber17"], color=col, lw=1.5, ls="--")
        ax.semilogy(P, c["ber18"], color=col, lw=1.3, ls=":")
        mc = np.array([np.nan if v is None else v for v in c["mc"]])
        ax.semilogy(c["Pmc"], mc, "o", mfc="none", color=col, ms=6)
    ax.axhline(HD_FEC, color="k", lw=0.9)
    ax.text(-4.8, HD_FEC * 1.15, r"HD-FEC $3.84\times10^{-3}$", fontsize=8)
    ax.set_ylim(1e-4, 2e-1); ax.set_xlim(-5, 11)
    ax.set_xlabel("Transmit power P [dBm]")
    ax.set_ylabel(r"Average BER $\bar P_b$")
    leg = [Line2D([], [], color="k", lw=1.8, label="eq. (16) exact"),
           Line2D([], [], color="k", lw=1.5, ls="--", label="eq. (17)"),
           Line2D([], [], color="k", lw=1.3, ls=":", label="eq. (18)"),
           Line2D([], [], color="k", marker="o", mfc="none", ls="",
                  label="Monte Carlo, eq. (1)")]
    l1 = ax.legend(handles=leg, loc="upper right", fontsize=8)
    ax.add_artist(l1)
    leg2 = [Line2D([], [], color=COL[n], lw=2.5,
                   label=f"$\\sigma_s$={c['sigma_s']} m, $\\sigma_R^2$={c['sigma_R2']}: "
                         f"$\\Delta_{{17}}$={c['D17']:.2f} dB, $\\Delta_{{18}}$={c['D18']:.2f} dB")
            for n, c in curves.items()]
    ax.legend(handles=leg2, loc="lower left", fontsize=7.5)
    save(fig, "fig_ber")

    fig, axs = plt.subplots(1, 3, figsize=(12, 3.9), sharey=True)
    for a, (name, c) in zip(axs, curves.items()):
        P = np.array(c["P"]); col = COL[name]
        a.semilogy(P, c["ber16"], color=col, lw=2, label="(16) stable")
        nv = np.array([np.nan if v is None else v for v in c["ber16_naive"]])
        lab = "(16) naive quad" + ("  -> nan" if np.all(np.isnan(nv)) else "")
        a.semilogy(c["Pmc"], np.where(np.isnan(nv), np.nan, nv), "s",
                   color="0.3", ms=4, label=lab)
        a.semilogy(P, c["ber17"], "k--", lw=1.3, label=r"(17), $\delta=10^{-6}$")
        if name == "pink":
            a.semilogy(P, c["ber17_delta01"], color="0.5", ls="-.", lw=1.2,
                       label=r"(17), $\delta=0.1$")
        a.semilogy(P, c["ber18"], "k:", lw=1.3, label=r"(18)")
        mc = np.array([np.nan if v is None else v for v in c["mc"]])
        a.semilogy(c["Pmc"], mc, "o", mfc="none", color=col, ms=6, label="MC")
        a.axhline(HD_FEC, color="k", lw=0.8)
        a.set_title(f"{name}: $\\sigma_s$={c['sigma_s']} m, "
                    f"$\\sigma_R^2$={c['sigma_R2']}, $\\kappa$={c['kappa']:.1f}",
                    fontsize=9)
        a.set_xlabel("P [dBm]"); a.set_ylim(1e-4, 3e-1); a.set_xlim(-5, 11)
        a.legend(fontsize=7, loc="lower left")
        if np.all(np.isnan(nv)):
            a.text(4, 0.08, "naive (16) = nan\nat every P", fontsize=8,
                   color="0.3", bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.8))
    axs[0].set_ylabel(r"$\bar P_b$")
    fig.tight_layout()
    save(fig, "fig_ber_panels")


# ==========================================================================
# 4. Task 3: area under (14) at the nine points
# ==========================================================================
def nine_points(p):
    P = np.arange(-6, 12.01, 0.05)
    rows = []
    for ss in GRID_SIGMA_S:
        for r2 in GRID_SIGMA_R2:
            op = OperatingPoint(ss, r2, p)
            b16 = ber_exact(P, op)
            P16 = crossing_dBm(P, b16)
            row = dict(sigma_s=ss, sigma_R2=r2, gamma2=op.g2, kappa=op.kappa,
                       naive_fails=naive_fails(op),
                       area_1e2=area_approx(op, 1e-2),
                       area_1e6=area_approx(op, 1e-6),
                       area_1e10=area_approx(op, 1e-10),
                       div_rate=divergence_rate(op), lost_mass=lost_mass(op),
                       area_remedy=area_remedy(op),
                       P16=P16,
                       D17=crossing_dBm(P, ber_approx17(P, op, 1e-6)) - P16,
                       D17_d01=crossing_dBm(P, ber_approx17(P, op, 0.1)) - P16,
                       D18=crossing_dBm(P, ber_approx18(P, op, 1e-6)) - P16,
                       Drem=crossing_dBm(P, ber_remedy(P, op)) - P16,
                       D17_paper=PAPER_DELTA_17[(ss, r2)])
            rows.append(row)
            print(f"  ss={ss} R2={r2} kappa={op.kappa:6.2f} "
                  f"area(1e-6)={row['area_1e6']:.4f} D17={row['D17']:.4f} "
                  f"paper={row['D17_paper']}")
    return rows


def fig_area(p, rows):
    fig, ax = plt.subplots(1, 2, figsize=(11, 4.0))
    deltas = np.logspace(-12, -0.5, 40)
    for ss, ls in zip(GRID_SIGMA_S, ["-", "--", ":"]):
        for r2, mk in zip(GRID_SIGMA_R2, ["o", "s", "^"]):
            op = OperatingPoint(ss, r2, p)
            A = [area_approx(op, d, n=8001) for d in deltas]
            ax[0].semilogx(deltas, A, ls=ls, marker=mk, ms=3, markevery=6,
                           label=f"$\\sigma_s$={ss}, $\\sigma_R^2$={r2} "
                                 f"($\\kappa$={op.kappa:.1f})")
    ax[0].axhline(1, color="k", lw=0.8)
    ax[0].invert_xaxis()
    ax[0].set_xlabel(r"lower limit $\delta$  (integrate (14) over $z>-\kappa+\delta$)")
    ax[0].set_ylabel("area under eq. (14)")
    ax[0].set_title("Area grows like $\\kappa\\phi(\\kappa)\\ln(1/\\delta)$: "
                    "visible only for small $\\kappa$", fontsize=10)
    ax[0].legend(fontsize=6.5, ncol=1, loc="upper left")

    k = np.array([r["kappa"] for r in rows])
    d17 = np.array([r["D17"] for r in rows])
    d17p = np.array([r["D17_paper"] for r in rows])
    d18 = np.array([r["D18"] for r in rows])
    drem = np.array([r["Drem"] for r in rows])
    d01 = np.array([r["D17_d01"] for r in rows])
    ax[1].loglog(k, np.maximum(d17, 1e-4), "o", color="#1F5AA6",
                 label=r"$\Delta_{17}$ (this work, $\delta=10^{-6}$)")
    ax[1].loglog(k, np.maximum(d01, 1e-4), "x", color="#1F5AA6",
                 label=r"$\Delta_{17}$ ($\delta=0.1$)")
    ax[1].loglog(k, np.maximum(d17p, 1e-4), "D", mfc="none", color="#D6337F",
                 label=r"$\Delta_{17}$ read from paper Fig. 2")
    ax[1].loglog(k, np.maximum(np.abs(drem), 1e-4), "v", color="#2E9E44",
                 label=r"$|\Delta|$ bounded-Q remedy")
    ax[1].set_xticks([2.5, 5, 10, 20, 40, 70])
    ax[1].xaxis.set_major_formatter(matplotlib.ticker.FormatStrFormatter("%g"))
    ax[1].xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax[1].set_xlabel(r"$\kappa=\gamma^2\sigma_R$")
    ax[1].set_ylabel(r"$\Delta$ at HD-FEC [dB]  (floored at $10^{-4}$)")
    ax[1].set_title(r"Accuracy is governed by one number, $\kappa$", fontsize=10)
    ax[1].legend(fontsize=7)
    fig.tight_layout()
    save(fig, "fig_area")


# ==========================================================================
# 5. Stretch (b): outage probability
# ==========================================================================
def outage_study(p, rng, Rs=10e9, Tc=(1e-3, 5e-3)):
    P = np.arange(-5, 25.01, 0.1)
    Pmc = np.arange(-4, 24.01, 2.0)
    out = {"Rs": Rs, "Tc": list(Tc),
           "symbols_per_block": [Rs * t for t in Tc]}
    fig, ax = plt.subplots(figsize=(6.6, 4.6))
    for name, (ss, r2) in FIG2_POINTS.items():
        op = OperatingPoint(ss, r2, p, name)
        po = outage_prob(P, op)
        mc = simulate_outage(Pmc, op, 2_000_000, rng, HD_FEC)
        b16 = ber_exact(P, op)
        ax.semilogy(P, po, color=COL[name], lw=2,
                    label=f"{name}: outage (closed form)")
        ax.semilogy(Pmc, np.where(mc > 0, mc, np.nan), "o", mfc="none",
                    color=COL[name], ms=5)
        ax.semilogy(P, b16, color=COL[name], lw=1, ls="--")
        res = dict(P_avg=crossing_dBm(P, b16))
        for q in (1e-2, 1e-3, 1e-6):
            res[f"P_out_{q:g}"] = crossing_dBm(P, po, target=q)
        res["penalty_1e-3"] = res["P_out_0.001"] - res["P_avg"]
        res["penalty_1e-6"] = res["P_out_1e-06"] - res["P_avg"]
        out[name] = res
        print(f"  {name}: P(avgBER=FEC)={res['P_avg']:.2f}  "
              f"P(Pout=1e-3)={res['P_out_0.001']:.2f}  "
              f"P(Pout=1e-6)={res['P_out_1e-06']:.2f} dBm")
    ax.axhline(HD_FEC, color="k", lw=0.8)
    ax.set_ylim(1e-7, 1); ax.set_xlim(-5, 25)
    ax.set_xlabel("Transmit power P [dBm]")
    ax.set_ylabel(r"$P_{\rm out}=\Pr\{P_b(h)>3.84\times10^{-3}\}$  /  $\bar P_b$")
    ax.set_title("Solid: outage (o: block-fading MC).  Dashed: average BER",
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
    save(fig, "fig_outage")
    return out


# ==========================================================================
# 6. What next: finite interleaver depth
# ==========================================================================
def required_power(op, N, rng, M=40_000, q=1e-3):
    """Smallest P such that Pr{ (1/N) sum_i P_b(h_i) > HD_FEC } <= q, where a
    codeword is spread by the interleaver over N independent fading blocks."""
    h = sample_h(M * N, op, rng).reshape(M, N)

    def viol(PdBm):
        pb = cond_ber(h, dBm_to_W(PdBm), op).mean(axis=1)
        return np.mean(pb > HD_FEC)

    lo, hi = -15.0, 40.0
    for _ in range(26):
        mid = 0.5 * (lo + hi)
        if viol(mid) > q:
            lo = mid
        else:
            hi = mid
    return hi


def interleaver_study(p, rng, Ns=(1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024), q=1e-3):
    out = {"N": list(Ns), "q": q}
    for name, (ss, r2) in FIG2_POINTS.items():
        op = OperatingPoint(ss, r2, p, name)
        req = [required_power(op, N, rng, M=max(20_000, 400_000 // N), q=q)
               for N in Ns]
        P = np.arange(-6, 30, 0.02)
        p_inf = crossing_dBm(P, ber_exact(P, op))
        p_one = crossing_dBm(P, outage_prob(P, op), target=q)
        out[name] = dict(required=req, P_inf=p_inf, P_N1_closed=p_one)
        print(f"  {name}: N=1 {req[0]:.2f} (closed {p_one:.2f}) ... "
              f"N={Ns[-1]} {req[-1]:.2f}  N=inf {p_inf:.2f} dBm")
    fig_interleaver(out)
    return out


def fig_interleaver(out):
    """Plot of the interleaver study (also usable from results.json)."""
    Ns, q = out["N"], out["q"]
    fig, ax = plt.subplots(figsize=(6.4, 4.3))
    for name in FIG2_POINTS:
        ax.semilogx(Ns, out[name]["required"], "o-", color=COL[name], label=name)
        ax.axhline(out[name]["P_inf"], color=COL[name], ls="--", lw=0.9)
    ax.set_xlabel("interleaver depth N (independent fades per codeword)")
    ax.set_ylabel(f"required P [dBm] for Pr(fail) = {q:g}")
    ax.set_title("Dashed: infinite interleaver (average BER = HD-FEC)",
                 fontsize=10)
    ax.legend(fontsize=8)
    save(fig, "fig_interleaver")


# ==========================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=2024)
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)
    n_bits = 400_000 if args.quick else 4_000_000

    p = SystemParams()
    results = {"system": system_numbers(p)}
    print("System:", {k: results["system"][k] for k in
                      ("wz", "A0", "wzeq", "hl")})

    print("[1] model check");      fig_model_check(p, rng)
    print("[2] nine points");      rows = nine_points(p)
    results["nine_points"] = rows
    print("[3] instability map")
    fig_instability(p, {(r["sigma_s"], r["sigma_R2"]): r["D17"] for r in rows})
    print("[4] BER curves");       curves = ber_curves(p, rng, n_bits)
    results["curves"] = curves
    fig_ber(curves)
    fig_area(p, rows)
    print("[5] outage");           results["outage"] = outage_study(p, rng)
    print("[6] interleaver");      results["interleaver"] = interleaver_study(p, rng)

    with open(os.path.join(RES, "results.json"), "w") as f:
        json.dump(results, f, indent=1, default=float)
    print("done ->", os.path.abspath(RES))


if __name__ == "__main__":
    main()
