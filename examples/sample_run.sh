#!/usr/bin/env bash
set -euo pipefail
# Simple example runner. Requires venv + deps installed.
# Usage: ./examples/sample_run.sh
OPENALEX_MAILTO="${OPENALEX_MAILTO:-you@example.com}" \
python3 cli.py "diffusion models for medical imaging" \
  --years 2022-2025 --per-source 50 \
  --min-score 0.2 \
  --outdir results
