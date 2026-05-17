# PandaCLI

A local LLM chat interface that runs entirely on your machine. PandaCLI launches a [llama.cpp](https://github.com/ggerganov/llama.cpp) server as a subprocess and provides an interactive terminal chat loop.

## Model

| Detail | Value |
|---|---|
| **Model** | Gemma 3 4B Instruct (`Gemma-3-4B-It`) |
| **Format** | GGUF (Q4_K_M quantization) |
| **Architecture** | `gemma3` |
| **Parameters** | 4 billion |
| **Prompt template** | Gemma 3 IT — `<start_of_turn>` / `<end_of_turn>` with system, user, and model roles |

## Architecture

```
┌────────────┐  POST /completion   ┌──────────────┐
│ llm_client │ ───────────────────▶│ llama-server │
│   (REPL)   │ ◀─── SSE stream ── │  (subprocess)│
└────────────┘  data: {content}    └──────────────┘
       │                                  ▲
       │  readiness probe:                │
       │  POST /completion                │
       │  {"prompt":"Hi","n_predict":1}   │
       └──────────────────────────────────┘
```

- **`config.py`** — All tuneable parameters: model path, server port, inference settings, and system prompt.
- **`llm_client.py`** — Server lifecycle (`start_server`, `wait_for_server`), prompt formatting (`format_prompt`), streaming inference (`ask_llm`), and the interactive REPL.

### Key design details

- **Server readiness** — `wait_for_server` sends a trivial completion request (`POST /completion` with `n_predict: 1`) instead of polling `/health`. This confirms the model is fully loaded and can generate tokens, not just that the HTTP server is up. It retries indefinitely on connection errors, timeouts, and HTTP errors (10 s backoff).
- **Streaming responses** — `ask_llm` sets `"stream": true` and reads Server-Sent Events (`data: …` lines). Each token is printed to the terminal as it arrives, giving the user real-time feedback instead of waiting for the full response.

## Prerequisites

- **Python 3.10+**
- **[llama.cpp](https://github.com/ggerganov/llama.cpp)** — `llama-server` must be installed and on your `PATH`.
- **GGUF model file** — Place your model at `~/models/gemma.gguf` (configurable in `config.py`).

## Getting Started

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the interactive chat
python llm_client.py
```

The server starts automatically, sends a trivial completion to verify the model is loaded, then drops you into a chat prompt. Responses stream to the terminal in real time. Type `exit` or `quit` to stop.

## Configuration

All settings live in `config.py`:

| Parameter | Default | Description |
|---|---|---|
| `MODEL_PATH` | `~/models/gemma.gguf` | Path to the GGUF model file |
| `SERVER_PORT` | `8080` | Port for the llama-server |
| `TEMPERATURE` | `0.7` | Sampling temperature |
| `TOP_P` | `0.95` | Nucleus sampling threshold |
| `TOP_K` | `64` | Top-k sampling |
| `SYSTEM_PROMPT` | `You are a helpful assistant.` | System prompt sent with every request |
