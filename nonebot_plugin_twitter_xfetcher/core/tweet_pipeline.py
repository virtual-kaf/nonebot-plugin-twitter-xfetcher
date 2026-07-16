import re
import asyncio
from typing import List, Dict, Any, Optional

from nonebot import logger

from ..config import MAX_POST_AGE, plugin_config
from ..models.tweet import TweetConversation, TweetItem
from ..clients.fxtwitter import fetch_conversation
from ..clients.grok import grok_fetch_urls
from ..clients.deepseek import translate_batch
from ..storage import is_duplicate, mark_sent


def _parse_tweet_id(url: str) -> Optional[str]:
    m = re.search(r"(?:twitter\.com|x\.com|fxtwitter\.com|fixupx\.com|twittpr\.com)/\w+/status/(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"/status/(\d+)", url)
    return m.group(1) if m else None


async def run_tweet_pipeline(members: List[str]) -> List[TweetConversation]:
    """核心流程：Grok 发现 URL → FxEmbed 并发抓取 → DeepSeek 翻译。"""
    results: List[TweetConversation] = []

    # Step 1: Grok 获取 URL
    url_entries = await grok_fetch_urls(members)
    if not url_entries:
        logger.warning("[Pipeline] Grok 无返回")
        return []

    # 去重
    seen_ids = set()
    tasks = {}
    skipped_duplicate = 0
    skipped_bad_url = 0
    for entry in url_entries:
        tid = _parse_tweet_id(entry["url"])
        if not tid:
            logger.debug(f"[Pipeline] 无法解析 URL: {entry['url'][:100]}")
            skipped_bad_url += 1
            continue
        if tid in seen_ids:
            continue
        if is_duplicate(entry["member"], tid):
            skipped_duplicate += 1
            continue
        seen_ids.add(tid)
        tasks[tid] = entry["member"]

    logger.info(
        f"[Pipeline] Grok 返回 {len(url_entries)} 条, "
        f"解析失败 {skipped_bad_url}, 去重 {skipped_duplicate}, "
        f"实际待抓取 {len(tasks)}"
    )

    if not tasks:
        return []

    # Step 2: FxEmbed 并发抓取
    async def fetch_one(tid: str):
        try:
            return tid, await asyncio.to_thread(fetch_conversation, tid)
        except Exception as e:
            logger.warning(f"[Pipeline] FxEmbed 抓取失败 {tid}: {e}")
            return tid, None

    fetched = await asyncio.gather(*[fetch_one(tid) for tid in tasks])
    convs = {tid: conv for tid, conv in fetched if conv is not None}

    # Step 3: 收集翻译文本
    translate_jobs: List[tuple[str, str]] = []
    for tid, conv in convs.items():
        if conv.target:
            translate_jobs.append((f"{tid}:target", conv.target.text))
        if conv.root and conv.root.id != (conv.target.id if conv.target else ""):
            translate_jobs.append((f"{tid}:root", conv.root.text))
        if conv.quote:
            translate_jobs.append((f"{tid}:quote", conv.quote.text))

    # Step 4: 批量翻译
    translations = {}
    if translate_jobs:
        try:
            translations = await translate_batch(translate_jobs)
        except Exception as e:
            logger.warning(f"[Pipeline] DeepSeek 翻译失败: {e}")

    # Step 5: 组装结果
    for tid, conv in convs.items():
        member = tasks.get(tid, "")
        if conv.target:
            conv.target.translated_text = translations.get(f"{tid}:target", "")
            mark_sent(member, tid)
        if conv.root:
            conv.root.translated_text = translations.get(f"{tid}:root", "")
        if conv.quote:
            conv.quote.translated_text = translations.get(f"{tid}:quote", "")
        results.append(conv)

    return results
