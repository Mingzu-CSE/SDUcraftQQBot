from nonebot.plugin import PluginMetadata

from .bot import *

__version__ = '0.1.0'
__plugin_meta__ = PluginMetadata(
    name="group_request_auto_check",
    description="自动核验加群信息",
    usage="被动触发",
    type="application",
    supported_adapters={"~onebot.v11"},
    extra={
      "version": __version__,
      "author": "Mingzu_ <mingzuliu@outlook.com>",
    },
)

