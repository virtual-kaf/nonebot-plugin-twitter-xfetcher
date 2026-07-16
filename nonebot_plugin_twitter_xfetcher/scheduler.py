import asyncio
import time
from pathlib import Path

from nonebot import get_bot, logger
from nonebot_plugin_apscheduler import scheduler

from .config import (
    CARD_DIR, plugin_config,
)
from .services import get_all_members, broadcast_to_groups
from .core import run_tweet_pipeline


@scheduler.scheduled_job("cron", minute=plugin_config.poll_cron_minutes, id="xfetch_monitor")
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


@scheduler.scheduled_job("cron", hour=plugin_config.card_cleanup_cron_hour, minute=plugin_config.card_cleanup_cron_minute, id="xfetch_card_cleanup")
async def cleanup_cards():
    """清理过期卡片图片。"""
    if not CARD_DIR.exists():
        return

    cutoff = time.time() - plugin_config.card_max_age_hours * 3600
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
        logger.info(f"[CardCleanup] 清理了 {cleaned} 张过期卡片（>{plugin_config.card_max_age_hours}h）")
