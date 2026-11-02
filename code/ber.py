"""
ber.py
======
Average-BER expressions for OOK with hard decisions and perfect CSI:

  * cond_ber        eq. (15)  P_b(h) = 1/2 erfc(eta P h / (sqrt(2) sigma_n))
  * ber_exact_naive eq. (16)  numerical integration of (15) against (10)
                              coded literally (fails for small sigma_s)
  * ber_exact       eq. (16)  same integral, done in the stable z variable
  * ber_approx17    eq. (17)  (15) integrated against the approximate PDF (14)
  * ber_approx18    eq. (18)  (17) with erfc approximated once more
  * outage_prob     stretch task (b): Pr{ P_b(h) > BER_target }
  * crossing_dBm    transmit power where a BER curve reaches the HD-FEC limit

Integration strategy
--------------------
All integrals are done over z = (ln(h/(A0 hl)) + 2 sX2)/(2 sX), in which
the exact density is the smooth EMG  kappa e^{kappa z + kappa^2/2} Q(z+kappa).

Eq. (14) has a 1/(z + kappa) factor (it comes from erfc(x) ~ e^{-x^2}/(x sqrt(pi)),
which blows up at x -> 0). The integrals (17), (18) and the area under (14)
therefore have a *logarithmic* singularity at h = h_hat (z = -kappa).
We substitute t = ln(z + kappa); then dz/(z+kappa) = dt and the integrand is
smooth in t. The singularity becomes an infinite t-range whose integrand tends
to the constant  kappa phi(kappa) P_b(h_hat).  We stop at z = -kappa + delta and
report how the result depends on delta (see area_approx and the report).
"""

import numpy as np
from scipy import special as sp
from scipy import integrate

from fso_model import (logpdf_Z, pdf_H_naive, cdf_Z, dBm_to_W)

HD_FEC = 3.84e-3


def Q(x):
    return 0.5 * sp.erfc(x / np.sqrt(2))


def cond_ber(h, P_W, op):
    """Eq. (15)."""
    return 0.5 * sp.erfc(op.p.eta * P_W * h / (np.sqrt(2) * op.p.sigma_n))


# --------------------------------------------------------------------------
# Exact average BER, eq. (16)
# --------------------------------------------------------------------------
def _z_grid_exact(kappa, n=40001):
    # left tail of f_Z decays like exp(kappa z), right tail like a Gaussian
    zmin = -kappa - 50.0 / kappa - 12.0
    zmax = 12.0
    return np.linspace(zmin, zmax, n)


def ber_exact(P_dBm, op, n=40001):
    """Eq. (16) evaluated stably (z variable, log-domain density)."""
    z = _z_grid_exact(op.kappa, n)
    w = np.exp(logpdf_Z(z, op.kappa))
    h = op.h_from_z(z)
    out = []
    for P in np.atleast_1d(dBm_to_W(P_dBm)):
        out.append(integrate.simpson(cond_ber(h, P, op) * w, x=z))
    return np.array(out)


def ber_exact_naive(P_dBm, op):
    """Eq. (16) the 'off-the-shelf' way: scipy.quad over h with the PDF (10)
    coded literally. Returns nan where the PDF evaluates to inf*0."""
    out = []
    hmax = op.A0hl * np.exp(12 * op.sX)           # practically all mass below
    for P in np.atleast_1d(dBm_to_W(P_dBm)):
        f = lambda h: cond_ber(h, P, op) * pdf_H_naive(h, op)
        with np.errstate(all="ignore"):
            val, _ = integrate.quad(f, 0.0, hmax, points=[op.A0hl], limit=400)
        out.append(val)
    return np.array(out)


# --------------------------------------------------------------------------
# Approximate PDF (14): area and BER (17), (18)
# --------------------------------------------------------------------------
def _t_grid(kappa, delta, n=40001, zmax=12.0):
    """t = ln(z + kappa) from ln(delta) to ln(zmax + kappa)."""
    return np.linspace(np.log(delta), np.log(zmax + kappa), n)


def area_approx(op, delta=1e-6, n=40001):
    """Area under eq. (14) over z > -kappa + delta.
    In t: integrand = kappa * phi(e^t - kappa)  (smooth)."""
    t = _t_grid(op.kappa, delta, n)
    z = np.exp(t) - op.kappa
    phi = np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    return integrate.simpson(op.kappa * phi, x=t)


def divergence_rate(op):
    """d(area)/d(ln 1/delta) as delta -> 0, i.e. kappa*phi(kappa).
    This is the extra area added per e-fold closer to h_hat."""
    return op.kappa * np.exp(-0.5 * op.kappa ** 2) / np.sqrt(2 * np.pi)


def lost_mass(op):
    """Probability mass of the exact PDF (10) below h_hat, which eq. (14) sets
    to zero:  Pr{z < -kappa} = Q(kappa) + 0.5 exp(-kappa^2/2)."""
    return float(cdf_Z(-op.kappa, op.kappa))


def ber_approx17(P_dBm, op, delta=1e-6, n=40001):
    """Eq. (17) with lower limit z = -kappa + delta (see module docstring)."""
    t = _t_grid(op.kappa, delta, n)
    z = np.exp(t) - op.kappa
    phi = np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    h = op.h_from_z(z)
    out = []
    for P in np.atleast_1d(dBm_to_W(P_dBm)):
        out.append(integrate.simpson(op.kappa * phi * cond_ber(h, P, op), x=t))
    return np.array(out)


def ber_approx18(P_dBm, op, delta=1e-6, n=40001):
    """Eq. (18): erfc in (17) replaced by e^{-x^2}/(x sqrt(pi)) as well."""
    t = _t_grid(op.kappa, delta, n)
    z = np.exp(t) - op.kappa
    phi = np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    h = op.h_from_z(z)
    out = []
    for P in np.atleast_1d(dBm_to_W(P_dBm)):
        x = op.p.eta * P * h / (np.sqrt(2) * op.p.sigma_n)
        pb = 0.5 * np.exp(-x * x) / (x * np.sqrt(np.pi))
        out.append(integrate.simpson(op.kappa * phi * pb, x=t))
    return np.array(out)


# --------------------------------------------------------------------------
# Remedy check: a Q-function approximation that stays bounded at x -> 0
# --------------------------------------------------------------------------
# Borjesson-Sundberg (1979):  Q(y) ~ phi(y) / ((1-a) y + a sqrt(y^2 + b)),
# a = 0.339, b = 5.510, relative error < 0.3 % for all y >= 0.
# Eq. (13) is the special case a = 0 (i.e. Q(y) ~ phi(y)/y), which is what
# makes eq. (14) blow up at h_hat. Keeping a > 0 removes the pole and,
# with Q(y) = 1 - Q(-y) for y < 0, gives a PDF on the whole real line.
BS_A, BS_B = 0.339, 5.510


def pdf_Z_remedy(z, kappa):
    y = z + kappa
    ay = np.abs(y)
    phi_z = np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    g = 1.0 / ((1 - BS_A) * ay + BS_A * np.sqrt(ay * ay + BS_B))
    with np.errstate(all="ignore"):
        neg = kappa * np.exp(kappa * z + 0.5 * kappa ** 2) - kappa * phi_z * g
    return np.where(y >= 0, kappa * phi_z * g, neg)


def ber_remedy(P_dBm, op, n=60001):
    z = _z_grid_exact(op.kappa, n)
    w = pdf_Z_remedy(z, op.kappa)
    h = op.h_from_z(z)
    return np.array([integrate.simpson(cond_ber(h, P, op) * w, x=z)
                     for P in np.atleast_1d(dBm_to_W(P_dBm))])


def area_remedy(op, n=60001):
    z = _z_grid_exact(op.kappa, n)
    return integrate.simpson(pdf_Z_remedy(z, op.kappa), x=z)


# --------------------------------------------------------------------------
# Stretch (b): outage probability under slow (block) fading
# --------------------------------------------------------------------------
def h_threshold(P_dBm, op, target=HD_FEC):
    """Smallest h with P_b(h) <= target:  h_th = sqrt(2) sigma_n erfcinv(2 target)/(eta P)."""
    P = dBm_to_W(P_dBm)
    return np.sqrt(2) * op.p.sigma_n * sp.erfcinv(2 * target) / (op.p.eta * P)


def outage_prob(P_dBm, op, target=HD_FEC):
    """Exact closed form: Pr{h < h_th} = F_Z(z_th)."""
    return cdf_Z(op.z_from_h(h_threshold(P_dBm, op, target)), op.kappa)


# --------------------------------------------------------------------------
# HD-FEC crossing and Delta
# --------------------------------------------------------------------------
def crossing_dBm(P_dBm, ber, target=HD_FEC):
    """Linear interpolation of log10(BER) vs P[dBm] at the target BER."""
    P_dBm = np.asarray(P_dBm, float)
    lb = np.log10(np.clip(np.asarray(ber, float), 1e-300, None))
    lt = np.log10(target)
    for i in range(len(P_dBm) - 1):
        if (lb[i] - lt) * (lb[i + 1] - lt) <= 0 and lb[i] != lb[i + 1]:
            return P_dBm[i] + (lt - lb[i]) * (P_dBm[i + 1] - P_dBm[i]) / (lb[i + 1] - lb[i])
    return np.nan
