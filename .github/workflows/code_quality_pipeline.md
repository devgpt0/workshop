# Code Quality Pipeline

This repository runs automated code quality checks on every push to `main` and on pull requests targeting `main`.

Executable workflow file:
- `.github/workflows/code_quality_pipeline.yml`

Checks performed:
- `ruff check .`
- `ruff format --check .`
- `pytest -q`
