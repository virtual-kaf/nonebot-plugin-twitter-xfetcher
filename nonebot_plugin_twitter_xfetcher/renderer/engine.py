"""Jinja2 + Playwright HTML 截图渲染引擎。"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from jinja2 import Environment, FileSystemLoader, select_autoescape

from nonebot import logger

from ..config import CARD_DIR, DISPLAY_TZ
from ..models.tweet import TweetConversation, TweetItem


TEMPLATE_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(TEMPLATE_DIR)),
    autoescape=select_autoescape(["html"]),
)

# Playwright browser
_browser = None
_lock = asyncio.Lock()


async def _get_browser():
    global _browser
    if _browser is None:
        async with _lock:
            if _browser is None:
                from playwright.async_api import async_playwright
                pw = await async_playwright().start()
                _browser = await pw.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox"],
                )
    return _browser


async def _html_to_png(html: str, output_path: Path, width: int = 600):
    browser = await _get_browser()
    page = await browser.new_page(viewport={"width": width, "height": 100})
    await page.set_content(html, wait_until="networkidle", timeout=30000)
    body_height = await page.evaluate("document.body.scrollHeight")
    await page.set_viewport_size({"width": width, "height": body_height + 20})
    await page.screenshot(path=str(output_path), full_page=True, type="png")
    await page.close()


def _format_time(iso_str: str) -> str:
    """Convert ISO/UTC time string to DISPLAY_TZ formatted string."""
    if not iso_str:
        return ""
    try:
        # Handle "Sun Jul 12 11:00:17 +0000 2026" format
        dt = datetime.strptime(iso_str, "%a %b %d %H:%M:%S %z %Y")
    except ValueError:
        try:
            # Handle ISO format
            s = iso_str.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
        except ValueError:
            return iso_str[:16]
    local_dt = dt.astimezone(DISPLAY_TZ)
    tz_name = local_dt.strftime("%Z")
    return local_dt.strftime(f"%Y-%m-%d %H:%M {tz_name}")


def _render_conversation_html(conv: TweetConversation) -> str:
    template = _env.get_template("conversation.html")
    return template.render(
        target=conv.target,
        ancestors=conv.ancestors,
        quote=conv.quote,
        format_time=_format_time,
    )


async def render_conversation_card(conv: TweetConversation) -> List[Path]:
    CARD_DIR.mkdir(parents=True, exist_ok=True)

    if not conv.target:
        logger.warning("render_conversation_card: 无 target 推文")
        return []

    try:
        html = _render_conversation_html(conv)
        target_id = conv.target.id
        path = CARD_DIR / f"{target_id}.png"
        await _html_to_png(html, path, width=650)
        logger.info(f"推文渲染完成: {path}")
        return [path]
    except Exception as e:
        logger.error(f"渲染卡片失败: {e}", exc_info=True)
        return []


async def shutdown():
    global _browser
    if _browser:
        await _browser.close()
        _browser = None
