import logging
import functools

from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters

from config import load_config
import db.history as history
import memory.store as store
from llm import client as llm_client
from handler import handle_message, handle_voice


def main() -> None:
    cfg = load_config()

    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s — %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting Cerebro bot")

    # Initialise subsystems
    history.init(cfg.sqlite_path)
    store.init(cfg.chroma_path)
    llm_client.init(cfg.anthropic_api_key)

    # Build Telegram app
    app = ApplicationBuilder().token(cfg.telegram_bot_token).build()

    # Bind handler with config injected via partial
    # Use filters.ALL for text so /think (parsed as a command) is also captured
    bound_handler = functools.partial(handle_message, cfg=cfg)
    app.add_handler(MessageHandler(filters.TEXT, bound_handler))

    bound_voice = functools.partial(handle_voice, cfg=cfg)
    app.add_handler(MessageHandler(filters.VOICE, bound_voice))

    logger.info("Bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
