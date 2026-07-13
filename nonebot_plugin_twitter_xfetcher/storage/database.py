import json
from pathlib import Path
from typing import List, Dict, Any

from nonebot import logger

from ..config import DATA_DIR, HISTORY_LIMIT
from ..models.group import GroupConfig


# 文件路径
SUBS_FILE = DATA_DIR / "group_subs.json"
STATUS_FILE = DATA_DIR / "last_status.json"
CONFIG_FILE = DATA_DIR / "config.json"


def _load_json(path: Path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def _save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ===== 推文去重 =====

def is_duplicate(member: str, tweet_id: str) -> bool:
    status = _load_json(STATUS_FILE, {})
    ids = status.get(member, [])
    return tweet_id in ids


def mark_sent(member: str, tweet_id: str):
    status = _load_json(STATUS_FILE, {})
    ids = status.setdefault(member, [])
    if tweet_id not in ids:
        ids.append(tweet_id)
    if len(ids) > HISTORY_LIMIT:
        status[member] = ids[-HISTORY_LIMIT:]
    _save_json(STATUS_FILE, status)


# ===== 群配置 =====

def get_group_config(group_id: str) -> GroupConfig:
    subs = _load_json(SUBS_FILE, {})
    config_raw = _load_json(CONFIG_FILE, {})
    group_data = subs.get(group_id, {})

    master = config_raw.get("master_switch", {}).get(group_id, False)
    radio = config_raw.get("radio_switch", {}).get(group_id, False)

    return GroupConfig(
        group_id=group_id,
        subs=group_data.get("subs", []),
        unsubs=group_data.get("unsubs", []),
        filter_water=group_data.get("filter_water", True),
        master_on=bool(master),
        radio_on=bool(radio),
    )


def save_group_config(cfg: GroupConfig):
    subs = _load_json(SUBS_FILE, {})
    subs[cfg.group_id] = {
        "subs": cfg.subs,
        "unsubs": cfg.unsubs,
        "filter_water": cfg.filter_water,
    }
    _save_json(SUBS_FILE, subs)

    config_raw = _load_json(CONFIG_FILE, {})
    config_raw.setdefault("master_switch", {})[cfg.group_id] = cfg.master_on
    config_raw.setdefault("radio_switch", {})[cfg.group_id] = cfg.radio_on
    _save_json(CONFIG_FILE, config_raw)


def get_all_group_configs() -> List[GroupConfig]:
    subs = _load_json(SUBS_FILE, {})
    config_raw = _load_json(CONFIG_FILE, {})
    result = []
    all_ids = set(subs.keys()) | set(config_raw.get("master_switch", {}).keys())
    for gid in all_ids:
        group_data = subs.get(gid, {})
        master = config_raw.get("master_switch", {}).get(gid, False)
        radio = config_raw.get("radio_switch", {}).get(gid, False)
        result.append(GroupConfig(
            group_id=gid,
            subs=group_data.get("subs", []),
            unsubs=group_data.get("unsubs", []),
            filter_water=group_data.get("filter_water", True),
            master_on=bool(master),
            radio_on=bool(radio),
        ))
    return result