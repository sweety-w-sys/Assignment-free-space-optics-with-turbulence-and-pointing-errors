#!/usr/bin/env bash
# Run the FSO assignment on your own computer (macOS / Linux).
# Usage:  bash run_local.sh          # full run
#         bash run_local.sh --quick  # 10x fewer Monte Carlo bits
set -e
REPO="Assignment-free-space-optics-with-turbulence-and-pointing-errors"
URL="https://github.com/sweety-w-sys/${REPO}.git"

if [ -d "$REPO" ]; then
  echo ">> Repository found, updating"
  git -C "$REPO" pull
else
  echo ">> Cloning repository"
  git clone "$URL"
fi

cd "$REPO"
python3 -m pip install --quiet numpy scipy matplotlib
cd code
python3 run_all.py "$@"

echo
echo ">> Done. Figures: $(pwd)/../figures"
echo ">> Numbers:  $(pwd)/../results/results.json"
