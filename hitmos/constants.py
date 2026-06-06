from pathlib import Path

VERSION = "0.0.4"
APP_NAME = "hitmos"
APP_TITLE = "Hitmos"

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_CHAT_URL = f"{OPENROUTER_BASE_URL}/chat/completions"
HTTP_REFERER = "https://github.com/ndugram/hitmos"

DEFAULT_MODEL = "deepseek/deepseek-chat"

CONFIG_DIR = Path.home() / ".hitmos"
CONFIG_FILE = CONFIG_DIR / "config.toml"

SYSTEM_PROMPT = (
    "You are Hitmos, a helpful AI coding assistant. "
    "Be concise, accurate, and developer-focused."
)

COMMANDS: dict[str, str] = {
    "/help": "Show available commands",
    "/clear": "Clear conversation history",
    "/reset": "Reset context",
    "/model": "Switch AI model (interactive picker)",
    "/model <name>": "Switch AI model directly",
    "/exit": "Exit Hitmos",
}

AVAILABLE_MODELS: list[tuple[str, str]] = [
    # ── free ──────────────────────────────────────────────────────────────────
    ("nvidia/nemotron-3-ultra-550b-a55b:free",           "Nemotron Ultra 550B · FREE · powerful"),
    ("nvidia/nemotron-3-super-120b-a12b:free",           "Nemotron Super 120B · FREE · fast"),
    ("meta-llama/llama-3.3-70b-instruct:free",           "Llama 3.3 70B · FREE · open source"),
    ("openai/gpt-oss-120b:free",                         "GPT OSS 120B · FREE · OpenAI"),
    ("openai/gpt-oss-20b:free",                          "GPT OSS 20B · FREE · OpenAI fast"),
    ("google/gemma-4-31b-it:free",                       "Gemma 4 31B · FREE · Google"),
    ("moonshotai/kimi-k2.6:free",                        "Kimi K2 · FREE · MoonshotAI"),
    ("nousresearch/hermes-3-llama-3.1-405b:free",        "Hermes 3 405B · FREE · large"),
    # ── paid ──────────────────────────────────────────────────────────────────
    ("deepseek/deepseek-chat",                           "DeepSeek Chat · fast, cheap, great for code"),
    ("deepseek/deepseek-r1",                             "DeepSeek R1 · reasoning model"),
    ("google/gemini-2.5-flash",                          "Gemini 2.5 Flash · fast multimodal"),
    ("google/gemini-2.5-pro",                            "Gemini 2.5 Pro · powerful multimodal"),
    ("anthropic/claude-3.5-haiku",                       "Claude 3.5 Haiku · fast Anthropic"),
    ("anthropic/claude-sonnet-4-5",                      "Claude Sonnet 4.5 · balanced Anthropic"),
    ("openai/gpt-4o-mini",                               "GPT-4o Mini · OpenAI fast"),
    ("openai/o4-mini",                                   "o4-mini · OpenAI reasoning"),
    ("meta-llama/llama-3.3-70b-instruct",                "Llama 3.3 70B · open source"),
    ("mistralai/mistral-small-3.2-24b-instruct",         "Mistral Small 3.2 · lightweight"),
]
