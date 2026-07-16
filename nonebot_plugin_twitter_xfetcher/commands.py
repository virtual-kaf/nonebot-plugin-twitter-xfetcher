import re
import asyncio
from datetime import datetime, timedelta, timezone

from nonebot import logger, on_command, on_message
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, Message
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me

from .config import CST, HELP_MESSAGE, plugin_config
from .services import get_all_members, subscribe, unsubscribe, broadcast_to_groups
from .core import run_tweet_pipeline
from .core.tweet_pipeline import _parse_tweet_id
from .clients.fxtwitter import fetch_conversation
from .clients.deepseek import translate_batch
from .renderer import render_conversation_card
from .storage import get_group_config, save_group_config, STATUS_FILE


# ===== 主开关 =====

master_cmd = on_command(plugin_config.command_name, aliases={f"/{plugin_config.command_name}"}, priority=1, block=True)


@master_cmd.handle()
async def handle_master(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    action = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)
    cfg = get_group_config(gid)

    if action in ("on", "开启"):
        cfg.master_on = True
        save_group_config(cfg)
        await master_cmd.finish("已启用 xfetch")
    elif action in ("off", "关闭"):
        cfg.master_on = False
        save_group_config(cfg)
        await master_cmd.finish("已关闭 xfetch")
    else:
        await master_cmd.finish(HELP_MESSAGE)


# ===== 订阅 =====

sub_cmd = on_command(f"{plugin_config.command_name} subscribe",
                     aliases={f"/{plugin_config.command_name} subscribe", f"{plugin_config.command_name} 订阅", "订阅"},
                     priority=1, block=True)


@sub_cmd.handle()
async def handle_sub(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    target = args.extract_plain_text().strip().lstrip("@")
    if not target:
        allowed = "、".join(plugin_config.optional_members)
        await sub_cmd.finish(f"请提供要订阅的 ID，例如：/{plugin_config.command_name} subscribe @id\n可选：{allowed}")
    msg = subscribe(str(event.group_id), target)
    await sub_cmd.finish(msg)


# ===== 取消订阅 =====

unsub_cmd = on_command(f"{plugin_config.command_name} unsubscribe",
                       aliases={f"/{plugin_config.command_name} unsubscribe", f"{plugin_config.command_name} 取消订阅", "取消订阅"},
                       priority=1, block=True)


@unsub_cmd.handle()
async def handle_unsub(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    target = args.extract_plain_text().strip().lstrip("@")
    if not target:
        await unsub_cmd.finish("请提供要取消订阅的 ID")
    msg = unsubscribe(str(event.group_id), target)
    await unsub_cmd.finish(msg)


# ===== 水帖过滤 =====

waterfilter_cmd = on_command(f"{plugin_config.command_name} waterfilter",
                             aliases={f"/{plugin_config.command_name} waterfilter", f"{plugin_config.command_name} 水帖过滤"},
                             priority=1, block=True)


@waterfilter_cmd.handle()
async def handle_waterfilter(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    action = args.extract_plain_text().strip().lower()
    gid = str(event.group_id)
    cfg = get_group_config(gid)

    if action in ("on", "开启"):
        cfg.filter_water = True
        save_group_config(cfg)
        await waterfilter_cmd.finish("水帖过滤已开启（不再推送reply/quote 推文）")
    elif action in ("off", "关闭"):
        cfg.filter_water = False
        save_group_config(cfg)
        await waterfilter_cmd.finish("水帖过滤已关闭")
    else:
        await waterfilter_cmd.finish(
            f"用法：/{plugin_config.command_name} waterfilter on | off\n"
            f"当前状态：{'开启' if cfg.filter_water else '关闭'}"
        )


# ===== 手动更新（SUPERUSER） =====

update_cmd = on_command(f"{plugin_config.command_name} update",
                        aliases={f"/{plugin_config.command_name} update", "updatex", "/updatex"},
                        permission=SUPERUSER,
                        priority=1, block=True)


@update_cmd.handle()
async def handle_update(bot: Bot, event: Event):
    gid = getattr(event, "group_id", None)
    if gid:
        cfg = get_group_config(str(gid))
        if not cfg.master_on:
            await update_cmd.finish(f"本群未开启 xfetch，请先使用 /{plugin_config.command_name} on")

    try:
        members = get_all_members()
        await update_cmd.send(f"正在检查 {len(members)} 个账号的动态...")
        convs = await run_tweet_pipeline(members)
        if convs:
            await broadcast_to_groups(bot, convs)
            await update_cmd.finish(f"检查完成，推送了 {len(convs)} 条动态")
        else:
            await update_cmd.finish("检查完成，暂无新动态")
    except Exception as e:
        logger.error(f"手动更新失败: {e}", exc_info=True)
        await update_cmd.finish(f"更新失败")


# ===== 清空去重（SUPERUSER） =====

reset_cmd = on_command(f"{plugin_config.command_name} reset",
                       aliases={f"/{plugin_config.command_name} reset"},
                       permission=SUPERUSER,
                       priority=1, block=True)


@reset_cmd.handle()
async def handle_reset(bot: Bot, event: Event):
    try:
        STATUS_FILE.write_text("{}", encoding="utf-8")
        await reset_cmd.finish(f"已清空去重记录，下次 /{plugin_config.command_name} update 会重新推送所有推文")
    except Exception as e:
        logger.error(f"清空失败：{e}")
        await reset_cmd.finish(f"清空失败")
