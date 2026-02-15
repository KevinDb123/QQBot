"""
打招呼插件 - 基本的问候功能
支持命令: /你好, /hello, /hi
"""
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import Bot, MessageEvent

# 打招呼命令
hello = on_command("hello", aliases={"hi", "你好"}, priority=10, block=True)


@hello.handle()
async def handle_hello(bot: Bot, event: MessageEvent):
    user_name = event.sender.nickname or "朋友"
    await hello.finish(f"你好呀，{user_name}！我是你的QQ小助手，很高兴认识你~ 😊\n发送 /help 可以查看我的功能哦！")
