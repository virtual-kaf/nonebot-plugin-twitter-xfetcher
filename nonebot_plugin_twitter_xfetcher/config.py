import pathlib
from datetime import timedelta, timezone

# 时区
try:
    from zoneinfo import ZoneInfo
    JST = ZoneInfo("Asia/Tokyo")
except Exception:
    JST = timezone(timedelta(hours=9))
CST = timezone(timedelta(hours=8))

# 推文卡片显示时区
try:
    from zoneinfo import ZoneInfo
    DISPLAY_TZ = ZoneInfo("Asia/Shanghai")
except Exception:
    DISPLAY_TZ = timezone(timedelta(hours=8))

# API
GROK_API_URL: str = "http://127.0.0.1:8000/v1/chat/completions"
GROK_API_KEY: str = "Bearer 1145141919810"

DEEPSEEK_API_URL: str = "https://api.deepseek.com/chat/completions"
DEEPSEEK_API_KEY: str = "sk-1145141919810"

FXTWITTER_API_BASE: str = "https://api.fxtwitter.com"

# 成员
CORE_MEMBERS: list[str] = [
    "virtual_kaf", "RIM_virtual"
]

OPTIONAL_MEMBERS: list[str] = [
    "CIEL_VanillaSky", "Sooda_oda"
]

# 路径：插件所在目录的父目录下的 data 文件夹
PLUGIN_DIR: pathlib.Path = pathlib.Path(__file__).parent
DATA_DIR: pathlib.Path = PLUGIN_DIR / "data"
CARD_DIR: pathlib.Path = PLUGIN_DIR / "data" / "cards"

# 运行参数
MAX_POST_AGE: timedelta = timedelta(hours=6)
REQUEST_TIMEOUT: float = 120.0
HISTORY_LIMIT: int = 10
GLOBAL_MEMBER_LIMIT: int = 18
POLL_CRON_MINUTES: str = "2,32"  # 轮询分钟（cron 表达式）

# 请在这里填入你的代理PROXY（或代理PORT）
IMAGE_PROXY: str = "http://127.0.0.1:114514"

MAX_URLS_PER_MEMBER: int = 3  # Grok 每个成员最多获取的推文数
CARD_MAX_AGE_HOURS: int = 24  # 卡片图片保留时长（小时）
CARD_CLEANUP_CRON_HOUR: str = "4"   # 卡片清理 cron 小时
CARD_CLEANUP_CRON_MINUTE: str = "0"  # 卡片清理 cron 分钟

# 管理员 QQ 号（可以使用 update/reset 指令）
ADMIN_LIST: list[str] = []

# 卡片
CARD_WIDTH: int = 800
CARD_FONT_PATHS: list[str] = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\NotoSansSC-VF.ttf",
    r"C:\Windows\Fonts\msgothic.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
]

# 自定义指令参数
COMMAND_NAME: str = "xfetch"
HELP_MESSAGE: str = f"""
用法：

/{COMMAND_NAME} on | off — 主开关
/{COMMAND_NAME} subscribe @id — 订阅
/{COMMAND_NAME} unsubscribe @id — 取消订阅
/{COMMAND_NAME} waterfilter on | off — 水帖过滤（关闭时不推送 reply/quote）
/{COMMAND_NAME} update — 手动更新（管理员）
/{COMMAND_NAME} reset — 清空去重记录（管理员）
"""