# FSO channel with weak turbulence and pointing errors — code

Python implementation for the TU/e ICT Lab student assignment on
C. Álvarez Roa et al., "A simplified FSO channel model with weak turbulence and
pointing errors", ICTON 2024.

## Files

| File | What it contains |
|---|---|
| `fso_model.py` | Table I parameters, operating points, samplers for h_a, h_p, h, PDFs (5), (7), (10) naive and stable, (14) |
| `ber.py` | Eq. (15), exact average BER (16) (naive and stable), approximations (17), (18), area under (14), outage probability, bounded-Q remedy, HD-FEC crossing |
| `montecarlo.py` | Bit-level Monte Carlo of Fig. 1 (OOK, eq. (1), ML hard decision with CSI) and block-fading outage MC |
| `run_all.py` | Runs every task, writes `../figures/*.pdf|png` and `../results/results.json` |

## Run

```bash
pip install numpy scipy matplotlib
python run_all.py          # full run, about 10-15 minutes (the interleaver study dominates)
python run_all.py --quick  # 10x fewer Monte Carlo bits
```

Python 3.10+, NumPy >= 1.24, SciPy >= 1.10, Matplotlib >= 3.7. Seed is fixed (`--seed 2024`).

## Main idea used throughout

With u = ln(h/(A0 h_l)) and z = (u + 2σ_X²)/(2σ_X), the composite gain is
z = W − E′ with W ~ N(0,1) (turbulence) and E′ ~ Exp(κ) (pointing error),
κ = 2γ²σ_X = γ²σ_R. Eq. (10) becomes f_Z(z) = κ exp(κz + κ²/2) Q(z + κ),
which is evaluated stably with `scipy.special.log_ndtr`, and eq. (14) becomes
κ φ(z)/(z + κ) for z > −κ.
