"""
fso_model.py
============
Channel model of


  * SystemParams      - Table I of the paper and the quantities derived from it
                        (beam waist w_z, A0, equivalent beam width w_zeq, h_l).
  * OperatingPoint    - one (sigma_s, sigma_R^2) pair and its derived
                        parameters (gamma^2, sigma_X^2, mu, h_hat, kappa).
  * samplers          - draw h_a, h_p and h = h_l h_p h_a  (Monte Carlo).
  * PDFs              - eq. (5), eq. (7), eq. (10) "as written" (unstable),
                        eq. (10) in a numerically stable log form, eq. (14).

Notation used in the code (derived in the report, Sec. 1):

    u = ln( h / (A0 h_l) )                  log of the normalised gain
    z = (u + 2 sigma_X^2) / (2 sigma_X)     standardised log-gain
    kappa = 2 gamma^2 sigma_X  (= gamma^2 sigma_R)

With these, ln h_a contributes a standard Gaussian W to z and the pointing
error contributes an independent exponential E' with rate kappa:

    z = W - E',   W ~ N(0,1),  E' ~ Exp(kappa)

so z has an exponentially-modified Gaussian (EMG) distribution and
eq. (10) becomes   f_Z(z) = kappa * exp(kappa z + kappa^2/2) * Q(z + kappa).
The single number kappa decides both the numerical trouble of eq. (10) and the
accuracy of the approximation eq. (14).

"""



from dataclasses import dataclass, field
import numpy as np
from scipy import special as sp

LOG_DBL_MAX = np.log(np.finfo(float).max)          # ~ 709.78


# --------------------------------------------------------------------------
# System parameters (Table I)
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class SystemParams:
    wavelength: float = 1550e-9      # lambda [m]
    eta: float = 0.5                 # responsivity [A/W]
    L: float = 3e3                   # link distance [m]
    sigma_n: float = 1e-7            # noise standard deviation [A]
    att_dB_per_km: float = 0.2208    # attenuation coefficient sigma(lambda)
    theta_half: float = 0.66e-3      # Tx divergence half angle [rad]
    a: float = 0.05                  # receiver aperture radius [m]

    # ---- derived quantities -------------------------------------------
    @property
    def k(self):                     # optical wave number 2*pi/lambda
        return 2 * np.pi / self.wavelength

    @property
    def wz(self):                    # beam waist at receiver, w_z ~ theta_1/2 * L
        return self.theta_half * self.L

    @property
    def v(self):                     # v = sqrt(pi) a / (sqrt(2) w_z)
        return np.sqrt(np.pi) * self.a / (np.sqrt(2) * self.wz)

    @property
    def A0(self):                    # collected fraction without pointing error
        return sp.erf(self.v) ** 2

    @property
    def wzeq2(self):                 # equivalent beam width squared
        v = self.v
        return self.wz ** 2 * np.sqrt(np.pi) * sp.erf(v) / (2 * v * np.exp(-v ** 2))

    @property
    def wzeq(self):
        return np.sqrt(self.wzeq2)

    @property
    def hl(self):
        """Beer-Lambert loss, eq. (9). sigma(lambda) is given in dB/km, so
        h_l = 10^(-sigma_dB * L_km / 10)  (= exp(-sigma L) with sigma in 1/km)."""
        return 10 ** (-self.att_dB_per_km * (self.L / 1e3) / 10)

    def rytov_from_Cn2(self, Cn2):
        """Eq. (4): sigma_R^2 = 1.23 Cn^2 k^(7/6) L^(11/6)."""
        return 1.23 * Cn2 * self.k ** (7 / 6) * self.L ** (11 / 6)

    def Cn2_from_rytov(self, sR2):
        return sR2 / (1.23 * self.k ** (7 / 6) * self.L ** (11 / 6))


# --------------------------------------------------------------------------
# One operating point (sigma_s, sigma_R^2)
# --------------------------------------------------------------------------
@dataclass
class OperatingPoint:
    sigma_s: float                   # jitter std at the receiver [m]
    sigma_R2: float                  # Rytov variance
    p: SystemParams = field(default_factory=SystemParams)
    label: str = ""

    @property
    def sX2(self):                   # log-amplitude variance, eq. (3)
        return self.sigma_R2 / 4

    @property
    def sX(self):
        return np.sqrt(self.sX2)

    @property
    def gamma(self):                 # eq. (8)
        return self.p.wzeq / (2 * self.sigma_s)

    @property
    def g2(self):
        return self.gamma ** 2

    @property
    def mu(self):                    # eq. (11)
        return 2 * self.sX2 * (1 + 2 * self.g2)

    @property
    def A0hl(self):
        return self.p.A0 * self.p.hl

    @property
    def hhat(self):                  # support threshold of eq. (14)
        return self.A0hl * np.exp(-self.mu)

    @property
    def kappa(self):                 # single parameter of the composite model
        return 2 * self.g2 * self.sX

    @property
    def big_exponent(self):          # 2 sX2 g2 (1+g2): the exp() argument in (10)
        return 2 * self.sX2 * self.g2 * (1 + self.g2)

    # ---- variable changes ---------------------------------------------
    def h_from_z(self, z):
        return self.A0hl * np.exp(2 * self.sX * z - 2 * self.sX2)

    def z_from_h(self, h):
        return (np.log(h / self.A0hl) + 2 * self.sX2) / (2 * self.sX)

    def __str__(self):
        return (f"{self.label or 'op'}: sigma_s={self.sigma_s:.3f} m, "
                f"sigma_R^2={self.sigma_R2:.2f}, gamma^2={self.g2:.2f}, "
                f"kappa={self.kappa:.2f}")


# --------------------------------------------------------------------------
# Samplers (Monte Carlo)
# --------------------------------------------------------------------------
def sample_ha(n, op, rng):
    """Turbulence, eq. (5). The log-amplitude X is Gaussian with variance
    sigma_X^2 and mean -sigma_X^2 (so that E[h_a] = 1); the intensity is
    h_a = exp(2X)."""
    X = rng.normal(-op.sX2, op.sX, n)
    return np.exp(2 * X)


def sample_hp(n, op, rng):
    """Geometric spread + pointing error, eqs. (6)-(7).
    Horizontal and vertical displacements are i.i.d. N(0, sigma_s^2), so
    R = sqrt(x^2 + y^2) is Rayleigh; R is mapped through eq. (6)."""
    x = rng.normal(0.0, op.sigma_s, n)
    y = rng.normal(0.0, op.sigma_s, n)
    R2 = x * x + y * y
    return op.p.A0 * np.exp(-2 * R2 / op.p.wzeq2)


def sample_h(n, op, rng):
    """Composite channel gain, eq. (2): h = h_l * h_p * h_a."""
    return op.p.hl * sample_hp(n, op, rng) * sample_ha(n, op, rng)


# --------------------------------------------------------------------------
# PDFs
# --------------------------------------------------------------------------
def pdf_ha(ha, op):
    """Eq. (5)."""
    s = op.sX2
    return 1 / (2 * ha * np.sqrt(2 * np.pi * s)) * \
        np.exp(-(np.log(ha) + 2 * s) ** 2 / (8 * s))


def pdf_hp(hp, op):
    """Eq. (7), support 0 <= hp <= A0."""
    A0, g2 = op.p.A0, op.g2
    out = g2 / A0 ** g2 * hp ** (g2 - 1)
    return np.where((hp >= 0) & (hp <= A0), out, 0.0)


def pdf_H_naive(h, op):
    """Eq. (10) coded literally, the way an off-the-shelf implementation would.
    For small sigma_s, exp(2 sX2 g2 (1+g2)) overflows to inf and erfc()
    underflows to 0, giving inf*0 = nan. Kept on purpose to show the problem."""
    s, g2, A0hl, mu = op.sX2, op.g2, op.A0hl, op.mu
    with np.errstate(all="ignore"):
        return (g2 / (2 * A0hl ** g2) * h ** (g2 - 1)
                * sp.erfc((np.log(h / A0hl) + mu) / np.sqrt(8 * s))
                * np.exp(2 * s * g2 * (1 + g2)))


def logpdf_Z(z, kappa):
    """Stable log-density of the standardised log-gain z (exact model).
    f_Z(z) = kappa exp(kappa z + kappa^2/2) Q(z + kappa); log Q is computed
    with log_ndtr, which never under/overflows."""
    return np.log(kappa) + kappa * z + 0.5 * kappa ** 2 + sp.log_ndtr(-(z + kappa))


def pdf_H_stable(h, op):
    """Eq. (10), same function, evaluated in the log domain (no overflow)."""
    z = op.z_from_h(h)
    return np.exp(logpdf_Z(z, op.kappa)) / (2 * op.sX * h)    # dz/dh = 1/(2 sX h)


def cdf_Z(z, kappa):
    """Exact CDF of z: F(z) = Phi(z) + exp(kappa z + kappa^2/2) Q(z+kappa)."""
    return sp.ndtr(z) + np.exp(kappa * z + 0.5 * kappa ** 2 + sp.log_ndtr(-(z + kappa)))


def pdf_Z_approx(z, kappa):
    """Eq. (14) in the z variable. After merging all exponents (report, Sec. 1)
    eq. (14) collapses to   kappa * phi(z) / (z + kappa)   for z > -kappa."""
    with np.errstate(all="ignore"):
        out = kappa * np.exp(-0.5 * z ** 2) / np.sqrt(2 * np.pi) / (z + kappa)
    return np.where(z > -kappa, out, 0.0)


def pdf_H_approx(h, op):
    """Eq. (14) in h (stable form):
    f_H(h) ~ g2 sqrt(2 sX2) / (sqrt(pi) h (u+mu)) * exp(-(u+2sX2)^2/(8 sX2)),
    u = ln(h/(A0 hl)), valid for h > h_hat, zero otherwise."""
    return pdf_Z_approx(op.z_from_h(h), op.kappa) / (2 * op.sX * h)


def pdf_H_approx_as_written(h, op):
    """Eq. (14) coded term-by-term as printed (still carries
    exp(2 sX2 g2(1+g2)) and h^(g2-1)/(A0 hl)^g2, so it overflows too)."""
    s, g2, A0hl, mu = op.sX2, op.g2, op.A0hl, op.mu
    with np.errstate(all="ignore"):
        u = np.log(h / A0hl)
        out = (g2 * h ** (g2 - 1) * np.sqrt(2 * s)
               / (np.sqrt(np.pi) * A0hl ** g2 * (u + mu))
               * np.exp(-((u + mu) ** 2) / (8 * s))
               * np.exp(2 * s * g2 * (1 + g2)))
    return np.where(h > op.hhat, out, 0.0)


# --------------------------------------------------------------------------
# Convenience
# --------------------------------------------------------------------------
def dBm_to_W(P_dBm):
    return 1e-3 * 10 ** (np.asarray(P_dBm, float) / 10)


# The three operating points of Fig. 2 (right) and the 3x3 grid of Fig. 2 (left)
FIG2_POINTS = {
    "green":  (0.12, 1.0),
    "yellow": (0.25, 0.5),
    "pink":   (0.35, 0.1),
}
GRID_SIGMA_S = (0.12, 0.25, 0.35)
GRID_SIGMA_R2 = (0.1, 0.5, 1.0)
PAPER_DELTA_17 = {                    # Delta [dB] read from Fig. 2 (left)
    (0.12, 0.1): 0.005, (0.12, 0.5): 0.003, (0.12, 1.0): 0.0,
    (0.25, 0.1): 0.11,  (0.25, 0.5): 0.02,  (0.25, 1.0): 0.01,
    (0.35, 0.1): 0.18,  (0.35, 0.5): 0.13,  (0.35, 1.0): 0.06,
}
