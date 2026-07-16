from datetime import timedelta, timezone
from pathlib import Path
from typing import List

from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    """xfetch plugin configuration."""

    # API
    grok_api_url: str = "http://127.0.0.1:8000/v1/chat/completions"
    grok_api_key: str = "Bearer 1145141919810"
    deepseek_api_url: str = "https://api.deepseek.com/chat/completions"
    deepseek_api_key: str = "sk-1145141919810"
    fxtwitter_api_base: str = "https://api.fxtwitter.com"

    # Members
    core_members: List[str] = ["virtual_kaf", "RIM_virtual"]
    optional_members: List[str] = ["CIEL_VanillaSky", "Sooda_oda"]

    # Display timezone
    display_timezone: str = "Asia/Shanghai"

    # Runtime
    max_post_age_hours: float = 6.0
    request_timeout: float = 120.0
    history_limit: int = 10
    global_member_limit: int = 18
    poll_cron_minutes: str = "2,32"

    # Proxy
    image_proxy: str = "http://127.0.0.1:58309"

    # URL Provider
    max_urls_per_member: int = 3

    # Card
    card_max_age_hours: int = 24
    card_cleanup_cron_hour: str = "4"
    card_cleanup_cron_minute: str = "0"
    card_width: int = 800
    card_font_paths: List[str] = [
        r"C:\Windows\Fonts\msyh.ttc",
        r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
        r"C:\Windows\Fonts\msgothic.ttc",
        r"C:\Windows\Fonts\simsun.ttc",
    ]

    # Command
    command_name: str = "xfetch"


# Parse config from nonebot driver
plugin_config = Config.parse_obj(get_driver().config.dict())

# Timezone constants
try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo("Asia/Tokyo")
except Exception:
    JST = timezone(timedelta(hours=9))
CST = timezone(timedelta(hours=8))

try:
    DISPLAY_TZ = ZoneInfo(plugin_config.display_timezone)
except Exception:
    DISPLAY_TZ = timezone(timedelta(hours=8))

# Path constants
PLUGIN_DIR: Path = Path(__file__).parent
DATA_DIR: Path = PLUGIN_DIR / "data"
CARD_DIR: Path = PLUGIN_DIR / "data" / "cards"

# Derived runtime values
MAX_POST_AGE: timedelta = timedelta(hours=plugin_config.max_post_age_hours)

# Help message
HELP_MESSAGE: str = f"""
用法：

/{plugin_config.command_name} on | off — 主开关
/{plugin_config.command_name} subscribe @id — 订阅
/{plugin_config.command_name} unsubscribe @id — 取消订阅
/{plugin_config.command_name} waterfilter on | off — 水帖过滤（关闭时不推送 reply/quote）
/{plugin_config.command_name} update — 手动更新（仅 SUPERUSER）
/{plugin_config.command_name} reset — 清空去重记录（仅 SUPERUSER）
"""
