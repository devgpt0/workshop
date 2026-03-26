# Agentic Chat

Agentic Chat is a Python application with two UIs:
- Terminal chat UI
- Browser chat UI (Streamlit)

It uses OpenRouter for model responses and supports tool-calling for:
- Web search/research via Exa
- Reliable current date/time answers

## Source Structure

```text
src/
  agentic_chat/
    __init__.py
    app/
      __init__.py
      entrypoint.py
      terminal.py
      web.py
    externals/
      __init__.py
      openrouter.py
    core/
      __init__.py
      config.py
      modes.py
    tools/
      __init__.py
      datetime_tool.py
      exa_tool.py
      registry.py
    ui/
      __init__.py
      terminal/
        __init__.py
        chat.py
        view.py
      web/
        __init__.py
        streamlit_app.py
```

## What Each Folder Does

- `app/`
  - Application entrypoints and startup orchestration.
  - `entrypoint.py` routes `agentic-chat` flags to terminal or web launcher.
  - `terminal.py` is terminal-only startup and chat execution.
  - `web.py` is web-only startup (Streamlit launcher).

- `externals/`
  - Integrations with external services.
  - `openrouter.py` manages OpenRouter API calls and the tool-calling loop.

- `core/`
  - Core domain logic and shared models.
  - `config.py` loads/validates environment settings.
  - `modes.py` defines available chat modes and session-state behavior.

- `tools/`
  - Tool-call implementations and routing.
  - `exa_tool.py` runs Exa web search via `exa-py`.
  - `datetime_tool.py` provides deterministic current date/time.
  - `registry.py` decides which tool to trigger and dispatches execution.

- `ui/terminal/`
  - Terminal interface behavior and rendering.
  - `chat.py` contains interactive command/chat loop.
  - `view.py` contains welcome screen + help rendering.

- `ui/web/`
  - Streamlit browser UI.
  - `streamlit_app.py` contains web chat session flow.

## Setup

1. Install `uv`:

```bash
pip install uv
```

2. Create `.env`:

```env
OPENROUTER_API_KEY=your_api_key_here
OPENROUTER_MODEL=openrouter/free
OPENROUTER_MODELS=openrouter/free,openai/gpt-oss-20b:free,openai/gpt-oss-120b:free,minimax/minimax-m2.7
OPENROUTER_TIMEOUT=30
OPENROUTER_SITE_URL=
OPENROUTER_SITE_NAME=
EXA_API_KEY=your_exa_api_key_here
EXA_NUM_RESULTS=5
WORKSHOP_NO_EFFECT=0
```

3. Install dependencies:

```bash
uv sync
```

## Run Terminal UI

```bash
uv run agentic-chat --terminal
```

## Run Browser UI

```bash
uv run agentic-chat --web
```

## Quality Checks

Windows:

```bat
scripts\run_check.bat
```

Bash:

```bash
bash scripts/run_check.sh
```

Both scripts run:
- `uv run ruff format --check .`
- `uv run ruff check .`
- `uv run pytest -q`

