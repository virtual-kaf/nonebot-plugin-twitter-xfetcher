import asyncio
import time
from pathlib import Path

from nonebot import get_bot, logger
from nonebot_plugin_apscheduler import scheduler

from .config import (
    POLL_CRON_MINUTES, CARD_MAX_AGE_HOURS, CARD_DIR,
    CARD_CLEANUP_CRON_HOUR, CARD_CLEANUP_CRON_MINUTE,
)
from .services import get_all_members, broadcast_to_groups
from .core import run_tweet_pipeline


@scheduler.scheduled_job("cron", minute=POLL_CRON_MINUTES, id="xfetch_monitor")
async def check_xfetch():
    """Poll X feeds."""
    try:
        bot = get_bot()
    except Exception:
        return

    try:
        members = get_all_members()
        convs = await run_tweet_pipeline(members)
        if convs:
            await broadcast_to_groups(bot, convs)
    except Exception as e:
        logger.error(f"[Scheduler] check failed: {e}", exc_info=True)


@scheduler.scheduled_job("cron", hour=CARD_CLEANUP_CRON_HOUR, minute=CARD_CLEANUP_CRON_MINUTE, id="xfetch_card_cleanup")
async def cleanup_cards():
    """清理过期卡片图片。"""
    if not CARD_DIR.exists():
        return

    cutoff = time.time() - CARD_MAX_AGE_HOURS * 3600
    cleaned = 0
    for f in CARD_DIR.iterdir():
        if f.is_file() and f.suffix == ".png":
            if f.stat().st_mtime < cutoff:
                try:
                    f.unlink()
                    cleaned += 1
                except Exception:
                    pass

    if cleaned:
        logger.info(f"[CardCleanup] 清理了 {cleaned} 张过期卡片（>{CARD_MAX_AGE_HOURS}h）")