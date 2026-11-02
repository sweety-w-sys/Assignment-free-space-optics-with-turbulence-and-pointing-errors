"""
montecarlo.py
=============
Bit-level Monte Carlo simulation of the IM/DD OOK link of Fig. 1:

    bits b_k -> OOK x_k in {0, 2P} -> (ideal interleaver) -> channel
    y_k = eta h_k x_k + n_k  (eq. 1),  h_k = h_l h_p h_a  (eq. 2)
    -> ML hard decision with perfect CSI -> b_hat_k

The infinite interleaver of the paper means consecutive symbols see
independent channel gains, so I simply draw a fresh h for every bit.

With perfect CSI and equiprobable bits the ML rule for the two hypotheses
y ~ N(0, sigma_n^2) and y ~ N(2 eta h P, sigma_n^2) is the midpoint threshold
    b_hat = 1  if  y > eta h P.
"""


import numpy as np
from fso_model import sample_h, dBm_to_W


def simulate_ber(P_dBm, op, n_bits, rng, chunk=1_000_000, min_errors=None):
    """Monte Carlo BER for each transmit power in P_dBm.

    Returns (ber, n_errors, n_simulated) arrays.
    If min_errors is given, simulation for a power stops early once that many
    errors have been counted (but never before one chunk)."""
    eta, sn = op.p.eta, op.p.sigma_n
    bers, errs, sims = [], [], []
    for P in np.atleast_1d(dBm_to_W(P_dBm)):
        n_err, n_sim = 0, 0
        while n_sim < n_bits:
            m = min(chunk, n_bits - n_sim)
            b = rng.integers(0, 2, m)                 # information bits
            x = 2 * P * b                             # OOK symbols {0, 2P}
            h = sample_h(m, op, rng)                  # fading, eq. (2)
            y = eta * h * x + sn * rng.standard_normal(m)   # eq. (1)
            b_hat = (y > eta * h * P).astype(b.dtype)       # ML / HD with CSI
            n_err += int(np.count_nonzero(b_hat != b))
            n_sim += m
            if min_errors is not None and n_err >= min_errors:
                break
        bers.append(n_err / n_sim); errs.append(n_err); sims.append(n_sim)
    return np.array(bers), np.array(errs), np.array(sims)


def simulate_outage(P_dBm, op, n_blocks, rng, target):

    """Block-fading Monte Carlo for stretch task (b): one h per coherence
    block; a block is 'in outage' if its conditional BER (15) > target."""

    from ber import cond_ber
    h = sample_h(n_blocks, op, rng)
    return np.array([np.mean(cond_ber(h, P, op) > target)
                     for P in np.atleast_1d(dBm_to_W(P_dBm))])
