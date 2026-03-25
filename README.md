# Workshop CLI

Simple CLI for chatting with OpenRouter using `requests` and `ujson`.
## Setup

1. Install `uv` with `pip`:

```bash
pip install uv
```

2. Create a `.env` file:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_MODELS=openrouter/free,openai/gpt-oss-20b:free,openai/gpt-oss-120b:free,minimax/minimax-m2.7
OPENROUTER_TIMEOUT=30
WORKSHOP_NO_EFFECT=0
```

Only these variables are used by the project.

3. Install the project dependencies:

```bash
uv sync
```

## Local Code Checks

Run all pre-push checks locally:

Windows (CMD/PowerShell):

```bat
scripts\run_check.bat
```

Bash (Linux/macOS/WSL):

```bash
bash scripts/run_check.sh
```

These scripts run:
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest -q`

## Usage

```bash
uv run workshop
```

This starts a continuous terminal chat session with a Bootcoding welcome screen.

Commands inside chat:

```text
/mode
/mode chat
/mode plan
/mode thinking
/models
/models use openrouter/free
/models add openai/gpt-oss-20b:free
/system
/system You are a senior software architect.
/system reset
/clear
/exit
```

Interactive behavior:
- `/mode` shows a numbered list and lets you choose a mode by number or name
- `/models` shows a numbered list and lets you choose a model by number or exact name
- `/system` shows the current system prompt and lets you replace or reset it interactively

Mode capabilities:
- `chat`: general conversation and assistance
- `plan`: planning, task breakdowns, and execution sequencing
- `thinking`: deeper reasoning and tradeoff analysis

You can still send a single prompt directly:

```bash
uv run workshop "What is the meaning of life?"
```

All configuration is loaded from `.env`.

Notes:
- `openrouter/free` is OpenRouter's official free router.
- Specific free variants use the `:free` suffix.
- Free models on OpenRouter have lower limits and availability than paid models.

Set `WORKSHOP_NO_EFFECT=1` to disable the styled startup screen.
