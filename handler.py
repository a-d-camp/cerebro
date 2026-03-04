import asyncio
import logging

from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ContextTypes

from config import Config
import db.history as history
import memory.store as store
import memory.profile as profile
import memory.synthesis as synthesis
from llm import client as llm_client
from llm import router
from llm.prompts import MEMORY_WRITE_PROMPT, MEMORY_MERGE_PROMPT, PROFILE_UPDATE_PROMPT, SYNTHESIS_PROMPT, build_system
import stt
import tts

logger = logging.getLogger(__name__)

THINK_PREFIX = "/think"


async def _run_pipeline(update: Update, cfg: Config, text: str, force_sonnet: bool) -> str:
    # 3. TYPING INDICATOR
    await update.message.chat.send_action(ChatAction.TYPING)

    # 4. SAVE USER MSG
    user_msg_id = history.insert(cfg.sqlite_path, role="user", content=text)

    # 5. FETCH HISTORY WINDOW
    window = history.get_window(cfg.sqlite_path, token_budget=cfg.history_token_budget)

    # 6. RETRIEVE MEMORIES
    memories = store.retrieve(
        query=text,
        top_k=cfg.memory_top_k_fetch,
        top_n=cfg.memory_top_n_return,
        half_life_days=cfg.memory_recency_half_life_days,
    )

    # 7. MODEL ROUTING
    model = router.select_model(text, force_sonnet=force_sonnet)

    # 8. BUILD PROMPT
    user_profile = profile.load(cfg.profile_path)
    user_synthesis = synthesis.load(cfg.synthesis_path)
    system_prompt = build_system(memories, profile=user_profile, synthesis=user_synthesis)

    # 9. CALL LLM
    response_text = llm_client.chat(
        messages=window,
        system=system_prompt,
        model=model,
    )

    # 10. SAVE ASSISTANT MSG
    assistant_msg_id = history.insert(cfg.sqlite_path, role="assistant", content=response_text)

    # 11. ASYNC MEMORY WRITE — fire and forget
    asyncio.create_task(
        _memory_write_task(
            cfg=cfg,
            user_message=text,
            assistant_response=response_text,
            message_ids=[user_msg_id, assistant_msg_id],
        )
    )

    return response_text


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE, cfg: Config) -> None:
    # 1. WHITELIST GATE
    user_id = update.effective_user.id
    if user_id != cfg.allowed_user_id:
        logger.debug("Dropped message from unauthorised user %d", user_id)
        return

    # 2. EXTRACT MESSAGE
    text = update.message.text or ""
    force_sonnet = False
    if text.startswith(THINK_PREFIX):
        force_sonnet = True
        text = text[len(THINK_PREFIX):].lstrip()
        logger.debug("/think prefix detected — forcing Sonnet")

    if not text:
        return

    response_text = await _run_pipeline(update, cfg, text, force_sonnet)
    await update.message.reply_text(response_text)


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE, cfg: Config) -> None:
    # 1. WHITELIST GATE
    user_id = update.effective_user.id
    if user_id != cfg.allowed_user_id:
        logger.debug("Dropped voice message from unauthorised user %d", user_id)
        return

    # 2. GUARD: openai_api_key required
    if not cfg.openai_api_key:
        await update.message.reply_text("Voice not configured (OPENAI_API_KEY missing).")
        return

    # 3. DOWNLOAD VOICE BYTES
    voice_file = await update.message.voice.get_file()
    ogg_bytes = bytes(await voice_file.download_as_bytearray())

    # 4. TRANSCRIBE
    text = stt.transcribe(ogg_bytes, cfg.openai_api_key)
    logger.info("Transcribed: %r", text)

    if not text:
        await update.message.reply_text("Could not transcribe audio.")
        return

    # 5. RUN SHARED PIPELINE
    response_text = await _run_pipeline(update, cfg, text, force_sonnet=False)

    # 6. SYNTHESIZE AND SEND VOICE REPLY
    audio_bytes = tts.synthesize(response_text, cfg.openai_api_key)
    await update.message.reply_voice(voice=audio_bytes)


async def _memory_write_task(
    cfg: Config,
    user_message: str,
    assistant_response: str,
    message_ids: list[int],
) -> None:
    try:
        prompt = MEMORY_WRITE_PROMPT.format(
            user_message=user_message,
            assistant_response=assistant_response,
        )
        extracted = llm_client.quick(
            prompt,
            model=router.HAIKU_MODEL,
            max_tokens=200,
        )
        if extracted.strip().upper() == "NOTHING":
            logger.debug("Memory write: nothing to save")
        else:
            # UPSERT: merge if similar memory exists, else store new
            similar = store.find_similar(extracted)
            if similar:
                merged = llm_client.quick(
                    MEMORY_MERGE_PROMPT.format(existing=similar["document"], new=extracted),
                    model=router.HAIKU_MODEL,
                    max_tokens=150,
                )
                store.update_memory(similar["id"], merged)
                history.log_memory(cfg.sqlite_path, memory_text=merged, chroma_id=similar["id"])
                logger.info("Memory merged id=%s text=%r", similar["id"], merged[:80])
            else:
                chroma_id = store.embed_and_store(
                    memory_text=extracted,
                    source_role="assistant",
                    message_ids=message_ids,
                )
                history.log_memory(cfg.sqlite_path, memory_text=extracted, chroma_id=chroma_id)
                logger.info("Memory saved id=%s text=%r", chroma_id, extracted[:80])

        # PROFILE UPDATE
        current_profile = profile.load(cfg.profile_path)
        updated_profile = llm_client.quick(
            PROFILE_UPDATE_PROMPT.format(
                current_profile=current_profile or "(empty — this is the first exchange)",
                user_message=user_message,
                assistant_response=assistant_response,
            ),
            model=router.HAIKU_MODEL,
            max_tokens=400,
        )
        profile.save(cfg.profile_path, updated_profile)
        logger.info("Profile updated (%d chars)", len(updated_profile))

        # PERIODIC SYNTHESIS
        msg_count = history.count_user_messages(cfg.sqlite_path)
        if msg_count % cfg.synthesis_interval == 0:
            all_memories = store.get_all()
            if all_memories:
                current_profile = profile.load(cfg.profile_path)
                memories_text = "\n".join(f"- {m}" for m in all_memories)
                updated_synthesis = llm_client.quick(
                    SYNTHESIS_PROMPT.format(
                        profile=current_profile or "(none yet)",
                        memories=memories_text,
                    ),
                    model=router.SONNET_MODEL,
                    max_tokens=600,
                )
                synthesis.save(cfg.synthesis_path, updated_synthesis)
                logger.info("Synthesis updated (%d chars)", len(updated_synthesis))
    except Exception as e:
        logger.error("Memory write task failed: %s", e, exc_info=True)
