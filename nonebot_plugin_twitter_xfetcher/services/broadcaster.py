import asyncio
from typing import List

from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot

from ..config import CORE_MEMBERS
from ..models.tweet import TweetConversation, TweetItem
from ..storage import get_all_group_configs
from ..renderer import render_conversation_card


async def broadcast_to_groups(bot: Bot, conversations: List[TweetConversation]):
    """渲染卡片并广播到所有订阅群。"""
    if not conversations:
        return

    try:
        group_list = await bot.get_group_list()
        all_groups = [g["group_id"] for g in group_list]
    except Exception as e:
        logger.error(f"获取群列表失败: {e}")
        return

    # 并发渲染所有卡片
    async def render_one(conv):
        try:
            return await render_conversation_card(conv)
        except Exception as e:
            logger.error(f"渲染卡片失败: {e}")
            return []

    all_card_paths = await asyncio.gather(*[render_one(conv) for conv in conversations])

    for conv_idx, conv in enumerate(conversations):
        card_paths = all_card_paths[conv_idx]
        if not card_paths:
            continue

        target = conv.target
        member_handle = target.author.screen_name if target else "unknown"

        is_reply = target.is_reply if target else False
        has_quote = conv.quote is not None

        for group_id in all_groups:
            gid = str(group_id)
            cfg = get_all_group_configs()
            group_cfg = next((g for g in cfg if g.group_id == gid), None)

            if not group_cfg or not group_cfg.master_on:
                continue

            if not ((member_handle in CORE_MEMBERS and member_handle not in group_cfg.unsubs)
                    or member_handle in group_cfg.subs):
                continue

            # 水帖过滤：关闭时不推送 reply/quote
            if not group_cfg.filter_water:
                if is_reply or has_quote:
                    continue

            for path in card_paths:
                try:
                    await bot.call_api("send_group_msg", group_id=group_id,
                                       message=f"[CQ:image,file=file:///{path}]")
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.warning(f"发送到群 {group_id} 失败: {e}")
                    break