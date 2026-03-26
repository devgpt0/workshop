# Architecture

## Overview

Agentic Chat is organized into layers so UI concerns, business logic, external integrations, and tool execution remain separated.

```text
UI (terminal / web)
  -> app entrypoint
    -> core state/config
      -> client(OpenRouter)
        -> tools registry
          -> concrete tools (Exa, datetime)
```

## Layers

### 1) UI Layer

- `src/agentic_chat/ui/terminal/`
  - Handles terminal interactions and rendering.
- `src/agentic_chat/ui/web/`
  - Streamlit app and web session flow.

Responsibilities:
- collect user input
- display assistant output
- delegate model execution to client/services

### 2) Application Layer

- `src/agentic_chat/app/entrypoint.py`
- `src/agentic_chat/app/terminal.py`
- `src/agentic_chat/app/web.py`

Responsibilities:
- route between terminal and web launchers (`entrypoint.py`)
- load config + construct dependencies for terminal runs (`terminal.py`)
- launch Streamlit for web runs (`web.py`)

### 3) Core Layer

- `src/agentic_chat/core/config.py`
- `src/agentic_chat/core/modes.py`

Responsibilities:
- central settings model + env validation
- mode definitions and session state

### 4) Externals Layer

- `src/agentic_chat/externals/openrouter.py`

Responsibilities:
- send/receive OpenRouter chat requests
- process tool calls from model output
- append tool results into conversation

### 5) Tools Layer

- `src/agentic_chat/tools/registry.py`
- `src/agentic_chat/tools/exa_tool.py`
- `src/agentic_chat/tools/datetime_tool.py`

Responsibilities:
- determine likely tool triggers from user intent
- expose tool JSON schemas to the model
- execute requested tools safely and consistently

## Tool Calling Flow

1. User asks a question in terminal/web UI.
2. UI forwards messages to `OpenRouterClient.send_chat`.
3. Client includes tool schemas from registry.
4. Registry may provide an initial forced tool choice for stronger accuracy.
5. If model emits tool calls, client executes via `registry.execute_tool`.
6. Tool result is added as `role=tool` and model completes final answer.

## Design Goals

- **Separation of concerns**: each folder has a single responsibility.
- **Replaceable UIs**: terminal/web can evolve independently.
- **Reliable tooling**: deterministic date/time and Exa search hooks improve factual accuracy.
- **Testability**: each layer can be mocked and tested independently.

