from ..config import plugin_config
from ..models.group import GroupConfig
from ..storage import get_group_config, save_group_config, get_all_group_configs


def get_all_members() -> list[str]:
    """获取所有需要监控的成员：核心成员 + 任意群额外订阅。"""
    all_cfgs = get_all_group_configs()
    tracked = set(plugin_config.core_members)
    for cfg in all_cfgs:
        tracked.update(cfg.subs)
    return list(tracked)


def subscribe(group_id: str, handle: str) -> str:
    """群订阅成员，返回结果消息。"""
    cfg = get_group_config(group_id)

    if handle in plugin_config.core_members:
        if handle in cfg.unsubs:
            cfg.unsubs.remove(handle)
            save_group_config(cfg)
            return f"已开启核心成员 @{handle} 的推送。"
        return f"@{handle} 是核心成员，默认已推送。"

    if handle not in plugin_config.optional_members:
        return f"拒绝订阅：@{handle} 不在白名单内。"

    if handle in cfg.subs:
        return f"本群已订阅 @{handle}"

    cfg.subs.append(handle)
    save_group_config(cfg)
    return f"已为本群订阅 @{handle}"


def unsubscribe(group_id: str, handle: str) -> str:
    """群取消订阅成员，返回结果消息。"""
    cfg = get_group_config(group_id)

    if handle in plugin_config.core_members:
        if handle in cfg.unsubs:
            return f"本群已屏蔽核心成员 @{handle}"
        cfg.unsubs.append(handle)
        save_group_config(cfg)
        return f"已取消核心成员 @{handle} 的推送"

    if handle in cfg.subs:
        cfg.subs.remove(handle)
        save_group_config(cfg)
        return f"已取消订阅 @{handle}"

    return f"本群未订阅 @{handle}"
