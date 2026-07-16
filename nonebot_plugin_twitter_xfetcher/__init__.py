"""nonebot_plugin_twitter_xfetcher V2 - X/Twitter feed monitor with FxEmbed API."""

from nonebot.plugin import PluginMetadata

from .commands import master_cmd, sub_cmd, unsub_cmd, update_cmd, waterfilter_cmd, debug_cmd
from .config import Config
from .scheduler import check_xfetch, cleanup_cards  # noqa: F401

__plugin_meta__ = PluginMetadata(
    name="xfetch",
    description="X/Twitter feed monitor with FxEmbed API and translation",
    usage=(
        "/xfetch on | off\n"
        "/xfetch subscribe @id\n"
        "/xfetch unsubscribe @id\n"
        "/xfetch waterfilter on | off\n"
        "/xfetch update\n"
        "/xfetch reset"
    ),
    type="application",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

__all__ = [
    "master_cmd", "sub_cmd", "unsub_cmd", "update_cmd", "waterfilter_cmd", "debug_cmd",
    "check_xfetch", "cleanup_cards",
]
