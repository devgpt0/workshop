# Architecture

## Overview

Agentic Chat is organized into layers so UI concerns, business logic, RAG indexing/retrieval, external integrations, and tool execution remain separated.

```text
UI (terminal / web)
  -> app entrypoint
    -> core state/config
      -> RAG pipeline (optional, in-memory Qdrant)
      -> client(OpenRouter)
        -> tools registry
          -> concrete tools (Exa, datetime)
```

## Layers

### 1) UI Layer

- `src/agentic_chat/ui/terminal/`
  - Terminal interactions, commands, and rendering.
  - Includes runtime RAG controls (`/rag on`, `/rag off`, `/rag reindex`, `/rag status`).
- `src/agentic_chat/ui/web/`
  - Streamlit app and web session flow.
  - Includes sidebar RAG toggle and reindex button with live counts.

Responsibilities:
- collect user input
- display assistant output
- allow enabling/disabling RAG at runtime
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
- RAG-related configuration (`RAG_*`, embedding model)

### 4) RAG Layer

- `src/agentic_chat/rag/bootstrap.py`
- `src/agentic_chat/rag/embeddings.py`
- `src/agentic_chat/rag/pipeline.py`
- `rag/data/` knowledge folder

Responsibilities:
- read local knowledge files from `rag/data`
- create embeddings via OpenRouter embeddings API
- build/rebuild in-memory Qdrant collection
- retrieve top-k relevant chunks and inject as grounding context

Notes:
- index is in-memory (`QdrantClient(location=":memory:")`)
- markdown chunk files (for example `rag/data/fairy_tale_rag_chunks/*.md`) improve retrieval precision

### 5) Externals Layer

- `src/agentic_chat/externals/openrouter.py`

Responsibilities:
- send/receive OpenRouter chat requests
- process tool calls from model output
- append tool results into conversation

### 6) Tools Layer

- `src/agentic_chat/tools/registry.py`
- `src/agentic_chat/tools/exa_tool.py`
- `src/agentic_chat/tools/datetime_tool.py`

Responsibilities:
- determine likely tool triggers from user intent
- expose tool JSON schemas to the model
- execute requested tools safely and consistently

## RAG-Enabled Response Flow

1. User asks a question in terminal/web UI.
2. If RAG is enabled for that session, UI requests retrieved context from `RAGPipeline`.
3. Pipeline embeds query and retrieves top-k chunks from in-memory Qdrant.
4. UI injects retrieved context as an additional system message.
5. UI forwards messages to `OpenRouterClient.send_chat`.
6. Model answers grounded on supplied RAG context.

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
- **Runtime control**: users can turn RAG on/off without restarting.
- **Reliable grounding**: in-memory vector retrieval supplies local knowledge context.
- **Testability**: each layer can be mocked and tested independently.
