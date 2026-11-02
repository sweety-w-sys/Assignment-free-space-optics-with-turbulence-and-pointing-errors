# How to run the assignment directly from GitHub

The whole assignment is automated: one Python command reproduces every figure and number of the report and the presentation.

| File in this folder | What it is |
|---|---|
| `run_in_colab.ipynb` | Google Colab notebook: clone → run → figures → numbers → (report PDF) → (push) → download |
| `run_local.sh` | Same thing on your own computer (macOS / Linux) |
| `README.md` | This guide |

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/sweety-w-sys/Assignment-free-space-optics-with-turbulence-and-pointing-errors/blob/main/how_to_run/run_in_colab.ipynb)

---

## Option A — Google Colab (nothing to install)

### Quickest way: one cell

Open [colab.research.google.com](https://colab.research.google.com) → **New notebook**, paste this into the first cell and press ▶:

```python
%cd /content
!git clone https://github.com/sweety-w-sys/Assignment-free-space-optics-with-turbulence-and-pointing-errors.git
%cd Assignment-free-space-optics-with-turbulence-and-pointing-errors/code
!python run_all.py
```

If you run it a second time in the same session, `git clone` says *"destination path already exists"*. That is harmless; to get the latest code use `!git pull` instead of cloning again.

### Full way: the ready-made notebook

1. Click the **Open in Colab** button above (or in Colab: **File → Open notebook → GitHub**, paste the repository URL and choose `how_to_run/run_in_colab.ipynb`).
2. Choose **Runtime → Run all**.
3. The notebook:
   1. clones the repository (or updates it with `git pull` if it is already there);
   2. runs `code/run_all.py` (set `QUICK = True` in step 2 for a fast check);
   3. shows all figures;
   4. prints the main numbers (Δ17, Δ18, area under (14), outage penalties);
   5. *(optional)* rebuilds `report/report.pdf` with the new figures;
   6. *(optional, repository owner only)* pushes the new results to GitHub;
   7. downloads a zip with `figures/`, `results/` and the report.

### Pushing results back to GitHub (owner only)

Step 6 needs a GitHub token:

1. GitHub → profile photo → **Settings → Developer settings → Personal access tokens → Tokens (classic) → Generate new token (classic)**, tick **repo**, copy the `ghp_...` token.
2. In Colab, click the **🔑 Secrets** icon on the left → **Add new secret** → name `GH_TOKEN`, value = the token → switch **Notebook access** on.
3. Run step 6 of the notebook. Never paste the token into a code cell.

---

## Option B — your own computer

Requirements: Python 3.10+ and Git.

```bash
bash run_local.sh            # full run
bash run_local.sh --quick    # 10x fewer Monte Carlo bits
```

or by hand:

```bash
git clone https://github.com/sweety-w-sys/Assignment-free-space-optics-with-turbulence-and-pointing-errors.git
cd Assignment-free-space-optics-with-turbulence-and-pointing-errors
pip install numpy scipy matplotlib
cd code
python run_all.py
```

---

## Where the results appear

| Output | Location |
|---|---|
| Console summary (Δ17, Δ18, area, outage, interleaver) | printed while `run_all.py` runs |
| Figures (PNG and PDF) | `figures/` — `fig_model_check`, `fig_ber`, `fig_ber_panels`, `fig_instability`, `fig_area`, `fig_outage`, `fig_interleaver` |
| Every number used in the report and slides | `results/results.json` |
| Console log | `results/run_log.txt` (when redirected) |

Run time: about 10–15 minutes for the full run (most of it is the interleaver study in Task 5); `--quick` only reduces the Monte Carlo bits of Task 2. The random seed is fixed (`--seed 2024`), so repeated runs give the same numbers up to the last decimal of the Monte Carlo estimates.

---

## Final steps — what to do to run it

1. Open Colab (or a terminal on your computer).
2. **First time in a session:** clone the repository
   `!git clone https://github.com/sweety-w-sys/Assignment-free-space-optics-with-turbulence-and-pointing-errors.git`
3. **Later in the same session:** update instead of cloning
   `%cd /content/Assignment-free-space-optics-with-turbulence-and-pointing-errors` then `!git pull`
4. Go to the code folder: `%cd /content/Assignment-free-space-optics-with-turbulence-and-pointing-errors/code`
5. Run: `!python run_all.py` (or `!python run_all.py --quick`)
6. Look at `figures/` and `results/results.json`.
7. *(Optional)* rebuild the report and push the results with steps 5–6 of `run_in_colab.ipynb`.
