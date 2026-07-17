# F.R.I.D.A.Y. — Tony Stark Demo

🎉 **Official Public Release:** F.R.I.D.A.Y. is now officially released to the public as a standalone application! You can easily install it without needing to set up the development environment.

* **Download:** Visit [https://xoraxi.com/](https://xoraxi.com/)
* **Installers Available:** `.exe` for Windows and `.dmg` for macOS.

> *"Fully Responsive Intelligent Digital Assistant for You"*

A Tony Stark-inspired AI assistant split into two cooperating pieces:

| Component | What it is |
| --- | --- |
| **MCP Server** (`uv run friday`) | A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes tools (news, web search, system info, …) over SSE. Think of it as the Stark Industries backend — it does the actual work. |
| **Voice Agent** (`uv run friday_voice`) | A [LiveKit Agents](https://github.com/livekit/agents) voice pipeline that listens to your microphone, reasons with an LLM (Gemini / OpenAI / Groq), and speaks back with TTS — all while pulling tools from the MCP server and managing persistent memory in real time. |


---

## How it works

```text
Microphone ──► STT (Sarvam Saaras v3)
                    │
                    ▼
          LLM (Groq LLaMA 3.3)  ◄──────► MCP Server (FastMCP / SSE)
                    │                             ├─ get_world_news
                    ▼                             ├─ open_world_monitor
             TTS (Deepgram / OpenAI)              ├─ search_web
                    │                             └─ …more tools
                    ▼
          Memory Pipeline (Mem0 & Built-in)
                    │
                    ▼
          Speaker / LiveKit room
```

The voice agent connects to the MCP server via SSE at `http://127.0.0.1:8000/sse` (auto-resolved to the Windows host IP when running inside WSL).

---

## Memory System (Hermes Architecture)

FRIDAY features a Hermes-inspired memory system to persist facts across conversations:

* **Built-in Memory**: A local Markdown-based filesystem storage (saved under `USER.md`).
* **Mem0 Memory**: An external cloud-based vector memory provider for semantically searchable and persistent user profiles.
* **Prefetch & Context Injection**: Before the LLM begins generating a response for a turn, FRIDAY queries both memory sources, merges, deduplicates, and ranks the relevant memories, then injects them as structured background context.
* **Asynchronous Extraction & Sync**: After each turn, FRIDAY extracts new facts from the user-assistant dialog in the background and saves them, automatically filtering out duplicates to keep the profile clean.

---

## Project structure

```text
friday/
├── server.py           # uv run friday  → starts the MCP server (SSE on :8000)
├── agent_friday.py     # uv run friday_voice → starts the LiveKit voice agent
├── pyproject.toml
├── .env.example        # copy → .env and fill in your keys
│
├── friday/             # MCP server package
│   ├── config.py       # env-var loading & app-wide settings
│   ├── tools/          # MCP tools (callable by the LLM)
│   │   ├── web.py      # search_web, fetch_url, get_world_news, open_world_monitor
│   │   ├── system.py   # get_current_time, get_system_info
│   │   └── utils.py    # format_json, word_count
│   ├── prompts/        # MCP prompt templates (summarize, explain_code, …)
│   └── resources/      # MCP resources exposed to clients (friday://info)
│
└── friday/memory/      # Memory pipeline files (Prefetch, Extraction, Cache, Providers)
```

---

## Quick start (For Developers)

### 1. Prerequisites

* Python ≥ 3.11
* [`uv`](https://github.com/astral-sh/uv) — run `pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh | sh`
* A [LiveKit Cloud](https://cloud.livekit.io) project (the free tier works)

### 2. Clone & install

```bash
git clone https://github.com/eNVy047/f.r.i.d.a.y.git
cd f.r.i.d.a.y
uv sync          
```

*(This creates the .venv and installs all dependencies)*

### 3. Set up environment

```bash
cp .env.example .env
```

*(Open the newly created `.env` file and fill in your API keys using the reference below)*

### 4. Run — two terminals

**Terminal 1 — MCP server** (must start first)

```bash
uv run friday
```

Starts the FastMCP server on `http://127.0.0.1:8000/sse`. The voice agent connects here to fetch its tools.

**Terminal 2 — Voice agent**

```bash
uv run friday_voice
```

Starts the LiveKit voice agent in **dev mode** — it joins a LiveKit room and begins listening. Open the [LiveKit Agents Playground](https://agents-playground.livekit.io) and connect to your room to talk to FRIDAY.

---

## `uv run friday` vs `uv run friday_voice`

| Command | Entry point | What it does |
| --- | --- | --- |
| `uv run friday` | `server.py → main()` | Launches the **FastMCP server** over SSE transport on port 8000. This is the "brain backend" — it registers all tools, prompts, and resources that the LLM can call. |
| `uv run friday_voice` | `agent_friday.py → dev()` | Launches the **LiveKit voice agent**. It builds the STT / LLM / TTS pipeline, connects to your LiveKit room, and wires up the MCP server as a tool source. The `dev()` wrapper auto-injects the `dev` CLI flag so you don't have to type it manually. |

> **Note:** Both processes must run **simultaneously**. The voice agent calls the MCP server in real time whenever it needs a tool (e.g., fetching news).

---

## Environment variables

Copy `.env.example` to `.env` and fill in the values below.

| Variable | Required | Where to get it |
| --- | --- | --- |
| `LIVEKIT_URL` | ✅ | [LiveKit Cloud dashboard](https://cloud.livekit.io) → your project URL |
| `LIVEKIT_API_KEY` | ✅ | LiveKit Cloud → API Keys |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit Cloud → API Keys |
| `GROQ_API_KEY` | Optional | [console.groq.com](https://console.groq.com) — needed if `LLM_PROVIDER` is `"groq"` |
| `SARVAM_API_KEY` | ✅ *(Default STT)* | [dashboard.sarvam.ai](https://dashboard.sarvam.ai) |
| `OPENAI_API_KEY` | Optional | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) — needed if `LLM_PROVIDER` is `"openai"` |
| `DEEPGRAM_API_KEY` | Optional | [console.deepgram.com](https://console.deepgram.com) |
| `GOOGLE_API_KEY` | Optional | [aistudio.google.com](https://aistudio.google.com/projects) — needed if `LLM_PROVIDER` is `"gemini"` |
| `MEM0_API_KEY` | ✅ | [mem0.ai](https://mem0.ai) — for external memory persistence |
| `SUPABASE_URL` | Optional | [supabase.com](https://supabase.com) — for the ticketing tool |
| `SUPABASE_API_KEY` | Optional | Supabase project → API settings |

---

## Switching providers

Open `agent_friday.py` and change the provider constants at the top:

```python
STT_PROVIDER = "sarvam"   # Options: "sarvam" | "whisper"
LLM_PROVIDER = "groq"     # Options: "gemini" | "openai" | "groq"
TTS_PROVIDER = "deepgram" # Options: "openai" | "sarvam" | "deepgram"
```

---

## Adding a new tool

1. Create or open a file in `friday/tools/`
2. Define a `register(mcp)` function and decorate your tools with `@mcp.tool()`
3. Import and call `register(mcp)` inside `friday/tools/__init__.py`

The MCP server will pick up your new tool on the next start.

---

## Tech stack

* **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server framework
* **[LiveKit Agents](https://github.com/livekit/agents)** — real-time voice pipeline
* **Sarvam Saaras v3** — STT (Indian-English optimised)
* **Groq LLaMA 3.3** / **Google Gemini 2.5 Flash** — LLM
* **Deepgram TTS** / **OpenAI TTS** — TTS
* **Mem0** — Vector-backed external memory
* **[uv](https://github.com/astral-sh/uv)** — fast Python package manager

---

## License

MIT
