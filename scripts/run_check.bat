@echo off
setlocal enabledelayedexpansion

echo [run_check] Running Ruff format check...
call uv run ruff format --check .
if errorlevel 1 exit /b 1

echo [run_check] Running Ruff lint check...
call uv run ruff check .
if errorlevel 1 exit /b 1

echo [run_check] Running pytest...
call uv run pytest -q
if errorlevel 1 exit /b 1

echo [run_check] All checks passed.
exit /b 0
