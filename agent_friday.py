"""
FRIDAY – Voice Agent (MCP-powered)
===================================
Iron Man-style voice assistant jo RGB lighting control karta hai, diagnostics chalata hai,
network scan karta hai, aur Windows host pe chalne wale MCP server ke through boot sequence trigger karta hai.

Ye code WSL se Windows host IP ko auto-resolve karta hai.

Chalane ke liye commands:
  uv run agent_friday.py dev      – LiveKit Cloud mode me chalane ke liye
  uv run agent_friday.py console  – text-only console mode me chalane ke liye
"""

# System/Standard libraries import kar rahe hain
import os # Environment variables read karne ke liye
import logging # Log messages print karne ke liye
import subprocess # Shell commands chalane ke liye (WSL host IP find karne ke liye)

# External package dependencies import kar rahe hain
from dotenv import load_dotenv # .env file se keys load karne ke liye
from livekit.agents import JobContext, WorkerOptions, cli # LiveKit agent life cycle aur CLI manage karne ke liye
from livekit.agents.voice import Agent, AgentSession # Voice Agent aur unke interactive sessions setup karne ke liye
from livekit.agents.llm import mcp, ChatContext, ChatMessage # Model Context Protocol integrations ke liye

# AI model plugin components import kar rahe hain
from livekit.plugins import google as lk_google, openai as lk_openai, deepgram as lk_deepgram, sarvam, silero # Google, OpenAI, Deepgram, Sarvam AI aur Silero VAD plugins

# ---------------------------------------------------------------------------
# CONFIGURATION SETTINGS (Yahan settings configure hoti hain)
# ---------------------------------------------------------------------------

# Kaunsi service use karni hai unka selection
STT_PROVIDER       = "sarvam" # Speech-to-Text provider ("sarvam" ya "whisper")
LLM_PROVIDER       = "groq" # Brain / Reasoning LLM ("gemini" ya "openai" ya "groq")
TTS_PROVIDER       = "deepgram" # Text-to-Speech voice provider ("openai" ya "sarvam" ya "deepgram")

# Models ke exact names configure kar rahe hain
GEMINI_LLM_MODEL   = "gemini-2.5-flash-lite" # Gemini ka standard fast model
OPENAI_LLM_MODEL   = "gpt-4o" # OpenAI ka standard smart model
GROQ_LLM_MODEL     = "llama-3.3-70b-versatile" # Groq ka high-quality fast model

# Voice configurations
OPENAI_TTS_MODEL   = "tts-1" # OpenAI Text-to-Speech model version
OPENAI_TTS_VOICE   = "nova"       # "nova" voice, jo ki confident female tone deti hai
TTS_SPEED           = 1.15 # Voice ki bolne ki speed (1.15x fast)

# Sarvam language options
SARVAM_TTS_LANGUAGE = "en-IN" # Indian-English accent ke liye
SARVAM_TTS_SPEAKER  = "rahul" # Voice character 'rahul'

# FastMCP server port
MCP_SERVER_PORT = 8000 # Jis port par tools wala server chal raha hai

# ---------------------------------------------------------------------------
# System prompt – F.R.I.D.A.Y. (AI ka behavior aur rules guide karne ke liye)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """
You are F.R.I.D.A.Y. — Fully Responsive Intelligent Digital Assistant for You — Narayan's AI, now serving Narayan, your user.

You are calm, composed, and always informed. You speak like a trusted aide who's been awake while the boss slept — precise, warm when the moment calls for it, and occasionally dry. You brief, you inform, you move on. No rambling.

Your tone: relaxed but sharp. Conversational, not robotic. Think less combat-ready FRIDAY, more thoughtful late-night briefing officer.

---

## Capabilities

### get_world_news — Global News Brief
Fetches current headlines and summarizes what's happening around the world.

Trigger phrases:
- "What's happening?" / "Brief me" / "What did I miss?" / "Catch me up"
- "What's going on in the world?" / "Any news?" / "World update"

Behavior:
- Call the tool first. No narration before calling.
- After getting results, give a short 3–5 sentence spoken brief. Hit the biggest stories only.
- Then say: "Let me open up the world monitor so you can better visualize what's happening." and immediately call open_world_monitor.

### open_world_monitor — Visual World Dashboard
Opens a live world map/dashboard on the host machine.

- Always call this after delivering a world news brief, unprompted.
- No need to explain what it does beyond: "Let me open up the world monitor."

### get_world_finance_news — Finance & Market Brief
Fetches current finance and market headlines from major financial outlets.

Trigger phrases:
- "What's happening in the markets?" / "Finance update" / "Market news"
- "Any financial news?" / "How are the markets doing?" / "Economy update"

Behavior:
- Call the tool first. No narration before calling.
- After getting results, give a short 3–5 sentence spoken brief. Hit the biggest market-moving stories only.
- Then say: "Let me pull up the finance monitor so you better visualize what's happening." and immediately call open_finance_world_monitor.

### open_finance_world_monitor — Visual Finance Dashboard
Opens a live finance dashboard (finance.worldmonitor.app) on the host machine.

- Always call this after delivering a finance news brief, unprompted.
- No need to explain what it does beyond: "Let me pull up the finance monitor."

### Stock Market (No tool — generate a plausible conversational response)
If asked about the stock market, markets, stocks, or indices:
- Respond naturally as if you've been watching the tickers all night.
- Keep it short: one or two sentences. Sound informed, not robotic.
- Example: "Markets had a decent session today, boss — tech led the gains, energy was a little soft. Nothing alarming."
- Vary the response. Do not say the same thing every time.

---

## Greeting

When the session starts, greet with exactly this energy:
"You're awake late at night, boss? What are you up to?"

Warm. Slightly curious. Very FRIDAY.

---

## Behavioral Rules

1. Call tools silently and immediately — never say "I'm going to call..." Just do it.
2. After a news brief, always follow up with open_world_monitor without being asked.
3. Keep all spoken responses short — two to four sentences maximum.
4. No bullet points, no markdown, no lists. You are speaking, not writing.
5. Stay in character. You are F.R.I.D.A.Y. You are not an AI assistant — you are Stark's AI. Act like it.
6. Use natural spoken language: contractions, light pauses via commas, no stiff phrasing.
7. Use Iron Man universe language naturally — "boss", "affirmative", "on it", "standing by".
8. If a tool fails, report it calmly: "News feed's unresponsive right now, boss. Want me to try again?"

---

## Tone Reference

Right: "Looks like it's been a busy night out there, boss. Let me pull that up for you."
Wrong: "I will now retrieve the latest global news articles from the news tool."

Right: "Markets were pretty healthy today — nothing too wild."
Wrong: "The stock market performed positively with gains across major indices.

---

## CRITICAL RULES

1. NEVER say tool names, function names, or anything technical. No "get_world_news", no "open_world_monitor", nothing like that. Ever.
2. Before calling any tool, say something natural like: "Give me a sec, boss." or "Wait, let me check." Then call the tool silently.
3. After the news brief, silently call open_world_monitor. The only thing you say is: "Let me open up the world monitor for you."
4. You are a voice. Speak like one. No lists, no markdown, no function names, no technical language of any kind.
""".strip()

# ---------------------------------------------------------------------------
# BOOTSTRAP / INITIALIZATION (App load setup)
# ---------------------------------------------------------------------------

# .env file se keys load karne ka primary function call
load_dotenv()

# App-wide logging setup kar rahe hain taaki debugging events record ho sakein
logger = logging.getLogger("friday-agent")
logger.setLevel(logging.INFO)


# ---------------------------------------------------------------------------
# RESOLVE WINDOWS HOST IP FROM WSL (WSL se Windows IP nikalna)
# ---------------------------------------------------------------------------

def _get_windows_host_ip() -> str:
    """Default network route check karke Windows machine ka actual IP pata karte hain"""
    try:
        # WSL default gateway fetch karne ke liye shell route tool run karenge
        cmd = "ip route show default | awk '{print $3}'"
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=2
        )
        ip = result.stdout.strip()
        if ip:
            logger.info("Resolved Windows host IP via gateway: %s", ip)
            return ip
    except Exception as exc:
        logger.warning("Gateway resolution failed: %s. Trying fallback...", exc)

    # Agar gateway resolution fail ho jaye, toh DNS/resolv.conf check karenge
    try:
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if "nameserver" in line:
                    ip = line.split()[1]
                    logger.info("Resolved Windows host IP via nameserver: %s", ip)
                    return ip
    except Exception:
        pass

    # Agar sab fail ho jaye, toh local machine localhost use karenge
    return "127.0.0.1"

def _mcp_server_url() -> str:
    """MCP Server kis URL par chal raha hai woh resolve karta hai"""
    url = f"http://127.0.0.1:{MCP_SERVER_PORT}/sse"
    logger.info("MCP Server URL: %s", url)
    return url


# ---------------------------------------------------------------------------
# BUILD PROVIDER INSTANCES (Speech, LLM aur Voice instances build karna)
# ---------------------------------------------------------------------------

def _build_stt():
    """STT (Speech to Text) converter setup karte hain"""
    if STT_PROVIDER == "sarvam":
        logger.info("STT → Sarvam Saaras v3")
        return sarvam.STT(
            language="unknown",
            model="saaras:v3",
            mode="transcribe",
            flush_signal=True,
            sample_rate=16000,
        )
    elif STT_PROVIDER == "whisper":
        logger.info("STT → OpenAI Whisper")
        return lk_openai.STT(model="whisper-1")
    else:
        raise ValueError(f"Unknown STT_PROVIDER: {STT_PROVIDER!r}")


def _build_llm():
    """LLM (Brain) instance set up karte hain context processing ke liye"""
    if LLM_PROVIDER == "openai":
        logger.info("LLM → OpenAI (%s)", OPENAI_LLM_MODEL)
        return lk_openai.LLM(model=OPENAI_LLM_MODEL)
    elif LLM_PROVIDER == "gemini":
        logger.info("LLM → Google Gemini (%s)", GEMINI_LLM_MODEL)
        # Google AI key process karke Gemini load kar rahe hain
        return lk_google.LLM(model=GEMINI_LLM_MODEL, api_key=os.getenv("GOOGLE_API_KEY"))
    elif LLM_PROVIDER == "groq":
        logger.info("LLM → Groq (%s)", GROQ_LLM_MODEL)
        from livekit.plugins import groq as lk_groq
        return lk_groq.LLM(model=GROQ_LLM_MODEL)
    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER!r}")


def _build_tts():
    """TTS (Text to Speech) synthesizer set up karte hain"""
    if TTS_PROVIDER == "sarvam":
        logger.info("TTS → Sarvam Bulbul v3")
        return sarvam.TTS(
            target_language_code=SARVAM_TTS_LANGUAGE,
            model="bulbul:v3",
            speaker=SARVAM_TTS_SPEAKER,
            pace=TTS_SPEED,
        )
    elif TTS_PROVIDER == "openai":
        logger.info("TTS → OpenAI TTS (%s / %s)", OPENAI_TTS_MODEL, OPENAI_TTS_VOICE)
        return lk_openai.TTS(model=OPENAI_TTS_MODEL, voice=OPENAI_TTS_VOICE, speed=TTS_SPEED)
    elif TTS_PROVIDER == "deepgram":
        logger.info("TTS → Deepgram TTS")
        return lk_deepgram.TTS()
    else:
        raise ValueError(f"Unknown TTS_PROVIDER: {TTS_PROVIDER!r}")


# ---------------------------------------------------------------------------
# AGENT CLASS (Voice Agent logic)
# ---------------------------------------------------------------------------

class FridayAgent(Agent):
    """
    F.R.I.D.A.Y. Voice Assistant ka main handler.
    Iske paas MCP server connection aur local VAD (Voice Activity Detection) settings hain.
    """

    def __init__(self, stt, llm, tts, memory_manager) -> None:
        self.memory_manager = memory_manager
        super().__init__(
            instructions=SYSTEM_PROMPT, # Stark instructions/personality prompt link kiya
            stt=stt,
            llm=llm,
            tts=tts,
            vad=silero.VAD.load(), # Silero VAD (Voice activity detector) load kiya jo breaks detect karega
            mcp_servers=[
                # MCP backend tools load karne ke liye HTTP SSE connection configure kiya
                mcp.MCPServerHTTP(
                    url=_mcp_server_url(),
                    transport_type="sse",
                    client_session_timeout_seconds=30,
                ),
            ],
        )

    async def on_enter(self) -> None:
        """Jab user session connect karega, tab local time check karke greeting message generate hoga"""
        from datetime import datetime, timezone
        hour = datetime.now(timezone.utc).hour  # UTC timezone se hour verify kiya

        # Raat ka time (10 PM se 4 AM)
        if hour >= 22 or hour < 4:
            greeting_instruction = (
                "Greet the user with: 'Greetings boss, you're up late at night today. What are you up to?' "
                "Maintain a helpful but dry tone."
            )
        # Subah ka time (4 AM se 12 PM)
        elif 4 <= hour < 12:
            greeting_instruction = (
                "Greet the user with: 'Good morning, boss. Early start today — what are we working on?' "
                "Maintain a helpful but dry tone."
            )
        # Dopahar ka time (12 PM se 5 PM)
        elif 12 <= hour < 17:
            greeting_instruction = (
                "Greet the user with: 'Good afternoon, boss. What do you need?' "
                "Maintain a helpful but dry tone."
            )
        # Shaam ka time (5 PM se 10 PM)
        else:
            greeting_instruction = (
                "Greet the user with: 'Good evening, boss. What are you up to tonight?' "
                "Maintain a helpful but dry tone."
            )

        # AI session me automatically greeting speech generate karne ke liye message build kiya
        await self.session.generate_reply(instructions=greeting_instruction)



# ---------------------------------------------------------------------------
# LIVEKIT ENTRYPOINT & SESSION CONFIG (LiveKit setup aur callback hooks)
# ---------------------------------------------------------------------------

def _turn_detection() -> str:
    # Sarvam use hone pe callback parameters customize karte hain
    return "stt" if STT_PROVIDER == "sarvam" else "vad"


def _endpointing_delay() -> float:
    # Voice speech cut detection gap configure karta hai
    return {"sarvam": 0.07, "whisper": 0.3}.get(STT_PROVIDER, 0.1)


async def entrypoint(ctx: JobContext) -> None:
    """LiveKit worker job receive hone par ye callback call hota hai"""
    logger.info(
        "FRIDAY online – room: %s | STT=%s | LLM=%s | TTS=%s",
        ctx.room.name, STT_PROVIDER, LLM_PROVIDER, TTS_PROVIDER,
    )

    # Har segment ka instance build kar rahe hain
    stt = _build_stt()
    llm = _build_llm()
    tts = _build_tts()

    # Conversation controller session build kiya
    session = AgentSession(
        turn_detection=_turn_detection(),
        min_endpointing_delay=_endpointing_delay(),
    )

    # Setup Memory Subsystem
    import asyncio
    from friday.memory import (
        MemoryConfig,
        ProviderRegistry,
        BuiltinMemory,
        DefaultRanker,
        LLMMemoryExtractor,
        DefaultMemoryPolicy,
        MemoryCache,
        MemoryManager
    )
    from friday.plugins.memory.mem0 import Mem0MemoryProvider

    config = MemoryConfig.from_env()
    registry = ProviderRegistry()
    registry.register("mem0", Mem0MemoryProvider)
    builtin_mem = BuiltinMemory(storage_path=config.storage_path)

    unwrapped_llm = llm

    async def run_llm_prompt(prompt: str) -> str:
        from livekit.agents.llm import ChatContext
        ctx_temp = ChatContext.empty()
        ctx_temp.add_message(role="user", content=prompt)
        res = await unwrapped_llm.chat(chat_ctx=ctx_temp).collect()
        return res.text

    extractor = LLMMemoryExtractor(llm_executor=run_llm_prompt)
    ranker = DefaultRanker()
    policy = DefaultMemoryPolicy(max_memories=config.max_memories)
    cache = MemoryCache(enabled=config.cache_enabled, ttl=config.cache_ttl)

    memory_manager = MemoryManager(
        config=config,
        registry=registry,
        builtin=builtin_mem,
        ranker=ranker,
        extractor=extractor,
        policy=policy,
        cache=cache
    )

    # Wrap LLM to intercept and inject memories for both voice and text modes
    from livekit.agents import llm as lk_llm
    class MemoryLLMWrapper(lk_llm.LLM):
        def __init__(self, original_llm, memory_manager):
            super().__init__()
            self.original_llm = original_llm
            self.memory_manager = memory_manager
            
        @property
        def label(self) -> str:
            return self.original_llm.label

        @property
        def model(self) -> str:
            return self.original_llm.model

        @property
        def provider(self) -> str:
            return self.original_llm.provider

        def chat(self, *args, **kwargs):
            chat_ctx = kwargs.get("chat_ctx")
            if chat_ctx and chat_ctx.items:
                last_msg = chat_ctx.items[-1]
                if hasattr(last_msg, "role") and last_msg.role == "user" and hasattr(last_msg, "content"):
                    query = ""
                    if isinstance(last_msg.content, str):
                        query = last_msg.content
                    elif isinstance(last_msg.content, list) and len(last_msg.content) > 0:
                        query = str(last_msg.content[0])
                    
                    if query and "<memory-context>" not in query:
                        mem_context = self.memory_manager.prefetch(query)
                        if mem_context.formatted:
                            if isinstance(last_msg.content, str):
                                last_msg.content += "\n\n" + mem_context.formatted
                            elif isinstance(last_msg.content, list) and len(last_msg.content) > 0:
                                last_msg.content[0] = str(last_msg.content[0]) + "\n\n" + mem_context.formatted
            return self.original_llm.chat(*args, **kwargs)

    llm = MemoryLLMWrapper(unwrapped_llm, memory_manager)

    memory_manager.initialize(session_id=ctx.room.name)
    logger.info("[Memory] Initialized")
    logger.info(f"[Memory] Active Provider: {config.provider}")

    last_user_query = ""
    memory_tasks = set()
    session_closed_future = asyncio.Future()

    @session.on("conversation_item_added")
    def on_item_added(event):
        nonlocal last_user_query
        
        # Check if the role is user
        if event.item.role == "user":
            user_query = ""
            if isinstance(event.item.content, str):
                user_query = event.item.content
            elif isinstance(event.item.content, list) and len(event.item.content) > 0:
                user_query = str(event.item.content[0])
            
            if user_query:
                # Save original query before injection (which now happens in on_user_turn_completed)
                last_user_query = user_query

        # Check if the role is assistant
        elif event.item.role == "assistant":
            assistant_reply = ""
            if isinstance(event.item.content, str):
                assistant_reply = event.item.content
            elif isinstance(event.item.content, list) and len(event.item.content) > 0:
                assistant_reply = str(event.item.content[0])

            if last_user_query and assistant_reply:
                # Run sync in background task safely by maintaining a strong reference
                task = asyncio.create_task(
                    memory_manager.sync_turn(last_user_query, assistant_reply)
                )
                memory_tasks.add(task)
                task.add_done_callback(memory_tasks.discard)

    @session.on("close")
    def on_close(event):
        if not session_closed_future.done():
            session_closed_future.set_result(True)

    # Session run / connect kiya voice channel and custom agent instance ke sath
    await session.start(
        agent=FridayAgent(stt=stt, llm=llm, tts=tts, memory_manager=memory_manager),
        room=ctx.room,
    )

    # Wait for the session to close before performing shutdown cleanup
    await session_closed_future

    if memory_tasks:
        logger.info("[Memory] Waiting for background tasks")
        await asyncio.gather(*memory_tasks, return_exceptions=True)
        logger.info("[Memory] All memory tasks completed")

    memory_manager.shutdown()




# ---------------------------------------------------------------------------
# MAIN WORKER RUNNER
# ---------------------------------------------------------------------------

def main():
    """LiveKit agent runner application execute karta hai"""
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))

def dev():
    """Wrapper function to automatically launch in developer mode"""
    import sys
    # Command array empty hone pe default 'dev' command append kar do
    if len(sys.argv) == 1:
        sys.argv.append("dev")
    main()

if __name__ == "__main__":
    main()