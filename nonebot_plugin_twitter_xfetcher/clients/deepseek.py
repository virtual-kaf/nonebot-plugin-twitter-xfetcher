import json
from typing import Any, Dict, Optional

import httpx
from nonebot import logger

from ..config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, REQUEST_TIMEOUT

TRANSLATE_SYSTEM_PROMPT = """\
You are a professional to-Chinese translator for X/Twitter posts.
Rules:
1. Translate the provided text(s) into natural, fluent Chinese.
2. Preserve all factual information exactly — do not modify, add, or omit facts.
3. Keep emoji and hashtags.
4. Safety & political review:
   - NSFW, gore, hate speech, illegal material → "[内容安全过滤]"
   - Content attacking China, CCP, Chinese leaders, or spreading politically sensitive
     misinformation → "[内容安全过滤]"
   - Otherwise set flag="ok".
5. Output ONLY valid JSON, no markdown, no commentary.

Output schema:
{
  "translations": [
    {"id": "text_id", "translated": "Chinese translation", "flag": "ok"}
  ]
}
"""


async def _chat(client: httpx.AsyncClient, system: str, user: str) -> str:
    payload = {
        "model": "deepseek-chat",
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = await client.post(
        DEEPSEEK_API_URL,
        headers={"Authorization": f"Bearer {DEEPSEEK_API_KEY}"},
        json=payload,
    )
    if r.status_code != 200:
        raise RuntimeError(f"DeepSeek HTTP {r.status_code}")
    body = r.json()
    return body["choices"][0]["message"]["content"]


async def translate_batch(texts: list[tuple[str, str]]) -> dict[str, str]:
    """Translate multiple texts. Input: [(id, text), ...] Output: {id: translated}."""
    items = [{"id": tid, "text": t} for tid, t in texts]
    user_prompt = "Translate:\n" + json.dumps(items, ensure_ascii=False)

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT, trust_env=False) as client:
        raw = await _chat(client, TRANSLATE_SYSTEM_PROMPT, user_prompt)
        try:
            data = json.loads(raw)
            return {t["id"]: t["translated"] for t in data.get("translations", [])}
        except (json.JSONDecodeError, KeyError):
            s = raw.find("{")
            e = raw.rfind("}")
            if s != -1 and e > s:
                data = json.loads(raw[s:e+1])
                return {t["id"]: t["translated"] for t in data.get("translations", [])}
            return {}