# Agentic Chat

Agentic Chat is a Python application with two UIs:
- Terminal chat UI
- Browser chat UI (Streamlit)

It uses OpenRouter for model responses and supports:
- Tool-calling (Exa web search + deterministic date/time)
- RAG grounding with in-memory Qdrant and OpenRouter embeddings

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
    core/
      __init__.py
      config.py
      modes.py
    externals/
      __init__.py
      openrouter.py
    rag/
      __init__.py
      bootstrap.py
      embeddings.py
      pipeline.py
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
docs/
  architecture.md
scripts/
  run_check.bat
  run_check.sh
tests/
  test_*.py
rag/
  data/
    README.md
    fairy_tale_rag.md
    fairy_tale_rag_chunks/
      chunk_01.md
      chunk_02.md
      ...
```

## What Each Folder Does

- `src/agentic_chat/app/`
  - Application entrypoints and launch routing.
  - `entrypoint.py` switches between terminal and web modes.

- `src/agentic_chat/core/`
  - Core state/config models.
  - Loads env settings, modes, and session defaults.

- `src/agentic_chat/externals/`
  - External API clients.
  - Handles OpenRouter request/response + tool-call loop.

- `src/agentic_chat/rag/`
  - RAG implementation.
  - Embedding client, in-memory Qdrant indexing, retrieval pipeline, and bootstrap wiring.

- `src/agentic_chat/tools/`
  - Tool schemas + tool execution.
  - Includes Exa search and date/time tools used by the LLM.

- `src/agentic_chat/ui/terminal/`
  - Terminal UX and commands.
  - Includes runtime RAG controls (`/rag on|off|status|reindex`).

- `src/agentic_chat/ui/web/`
  - Streamlit web UI.
  - Includes sidebar RAG toggle and reindex button.

- `docs/`
  - Project documentation.
  - `architecture.md` explains layers and request flow.

- `scripts/`
  - Developer quality-check scripts for Windows and Bash.

- `tests/`
  - Unit tests for app entrypoints, chat flow, tools, config, and UI behavior.

- `rag/data/`
  - Knowledge-base files consumed by RAG indexing.
  - Store Markdown/text/json/csv/rst files here.

- `rag/data/fairy_tale_rag_chunks/`
  - Example of pre-split content chunks to improve retrieval quality.

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
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-3-small

EXA_API_KEY=your_exa_api_key_here
EXA_NUM_RESULTS=5

RAG_ENABLED=1
RAG_DATA_DIR=rag/data
RAG_TOP_K=4
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120

WORKSHOP_NO_EFFECT=0
```

3. Put your knowledge files (`.md`, `.txt`, `.json`, `.csv`, `.rst`) into `rag/data`.

4. Install dependencies:

```bash
uv sync
```

## RAG Data Notes

- Prefer Markdown files for better readability and retrieval quality.
- Keep long stories/content split into multiple chunk files under a folder like `rag/data/<topic>_chunks/`.
- Qdrant index is in-memory, so restart requires reindexing.

## Run Terminal UI

```bash
uv run agentic-chat --terminal
```

Terminal RAG commands:
- `/rag` or `/rag status` shows indexed file/chunk counts and RAG on/off state
- `/rag on` enables RAG-grounded answers
- `/rag off` disables RAG-grounded answers
- `/rag reindex` rebuilds the in-memory Qdrant index from `rag/data`

## Run Browser UI

```bash
uv run agentic-chat --web
```

Web sidebar controls:
- `Use RAG for answers` toggle enables/disables RAG per session
- `Reindex RAG` rebuilds in-memory index and updates chunk/file counts in UI

## Quality Checks

Windows:

```bat
scripts\run_check.bat
```

Bash:

```bash
bash scripts/run_check.sh
```
