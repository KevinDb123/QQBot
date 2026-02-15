"""
NoneBot QQ 机器人入口文件
"""
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

# 初始化 NoneBot
nonebot.init()

# 注册适配器
driver = nonebot.get_driver()
driver.register_adapter(OneBotV11Adapter)

# 加载内置插件
nonebot.load_builtin_plugins("echo", "single_session")

# 加载本地插件
nonebot.load_plugins("awesome_bot/plugins")

if __name__ == "__main__":
    nonebot.run()
