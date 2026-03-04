from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    value = os.getenv(key)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


@dataclass
class Config:
    telegram_bot_token: str
    allowed_user_id: int
    anthropic_api_key: str
    default_model: str
    history_token_budget: int
    memory_top_k_fetch: int
    memory_top_n_return: int
    memory_recency_half_life_days: float
    chroma_path: str
    sqlite_path: str
    log_level: str
    openai_api_key: str | None
    profile_path: str
    synthesis_path: str
    synthesis_interval: int


def load_config() -> Config:
    return Config(
        telegram_bot_token=_require("TELEGRAM_BOT_TOKEN"),
        allowed_user_id=int(_require("ALLOWED_USER_ID")),
        anthropic_api_key=_require("ANTHROPIC_API_KEY"),
        default_model=os.getenv("DEFAULT_MODEL", "claude-haiku-4-5"),
        history_token_budget=int(os.getenv("HISTORY_TOKEN_BUDGET", "4000")),
        memory_top_k_fetch=int(os.getenv("MEMORY_TOP_K_FETCH", "20")),
        memory_top_n_return=int(os.getenv("MEMORY_TOP_N_RETURN", "5")),
        memory_recency_half_life_days=float(os.getenv("MEMORY_RECENCY_HALF_LIFE_DAYS", "30")),
        chroma_path=os.getenv("CHROMA_PATH", "data/chroma"),
        sqlite_path=os.getenv("SQLITE_PATH", "data/cerebro.db"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        openai_api_key=os.getenv("OPENAI_API_KEY") or None,
        profile_path=os.getenv("PROFILE_PATH", "data/user_profile.md"),
        synthesis_path=os.getenv("SYNTHESIS_PATH", "data/synthesis.md"),
        synthesis_interval=int(os.getenv("SYNTHESIS_INTERVAL", "10")),
    )
