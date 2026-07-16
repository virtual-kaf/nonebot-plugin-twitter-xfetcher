import asyncio
import json
from typing import List, Optional

import httpx
from nonebot import logger

from ..config import plugin_config


GROK_URL_SYSTEM_PROMPT = """\
You are a strict X post URL extractor.
For each target account, find the LATEST post URLs from the provided input.
Return ONLY a JSON object, no markdown, no commentary.

Output schema:
{
  "members": [
    {"handle": "string", "urls": ["https://x.com/user/status/123", ...]}
  ]
}
"""


def _build_grok_prompt(members: List[str]) -> str:
    joined = ", ".join(members)
    return f"""Target accounts: {joined}

Search the latest posts for each account. Return ONLY the JSON with post URLs.
For each account, return up to {plugin_config.max_urls_per_member} most recent post URLs."""


async def grok_fetch_urls(members: List[str]) -> List[dict]:
    """Fetch latest tweet URLs for each member via Grok."""
    payload = {
        "model": "grok-4.20-0309-non-reasoning",
        "temperature": 0,
        "top_p": 1,
        "stream": False,
        "messages": [
            {"role": "system", "content": GROK_URL_SYSTEM_PROMPT},
            {"role": "user", "content": _build_grok_prompt(members)},
        ],
    }

    async with httpx.AsyncClient(timeout=plugin_config.request_timeout, trust_env=False) as client:
        r = await client.post(plugin_config.grok_api_url, headers={"Authorization": plugin_config.grok_api_key}, json=payload)
        if r.status_code != 200:
            logger.error(f"Grok HTTP {r.status_code}: {r.text[:300]}")
            return []

        try:
            body = r.json()
            content = body["choices"][0]["message"]["content"]
        except Exception:
            logger.warning(f"Grok parse failed: {r.text[:400]}")
            return []

        # Extract JSON from response
        try:
            data = json.loads(content)
        except json.JSONDecodeError:
            s = content.find("{")
            e = content.rfind("}")
            if s != -1 and e > s:
                data = json.loads(content[s:e+1])
            else:
                return []

        result = []
        for m in data.get("members", []):
            handle = m.get("handle", "")
            urls = m.get("urls", [])
            if handle and urls:
                result.extend([{"member": handle, "url": u} for u in urls])

        logger.info(f"[Grok] got {len(result)} URLs across {len(members)} members")
        return result
