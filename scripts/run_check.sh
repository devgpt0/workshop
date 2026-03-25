#!/usr/bin/env bash
set -euo pipefail

echo "[run_check] Running Ruff format check..."
uv run ruff format --check .

echo "[run_check] Running Ruff lint check..."
uv run ruff check .

echo "[run_check] Running pytest..."
uv run pytest -q

echo "[run_check] All checks passed."
