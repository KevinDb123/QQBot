"""
机器人状态插件 - 查看运行状态
支持命令: /状态, /status
"""
import time
import platform
from datetime import datetime

from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import MessageEvent

status_cmd = on_command("status", aliases={"状态", "运行状态"}, priority=10, block=True)

# 记录启动时间
start_time = time.time()


@status_cmd.handle()
async def handle_status(event: MessageEvent):
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)

    # 计算运行时长
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60

    uptime_str = ""
    if days > 0:
        uptime_str += f"{days}天"
    if hours > 0:
        uptime_str += f"{hours}小时"
    if minutes > 0:
        uptime_str += f"{minutes}分钟"
    uptime_str += f"{seconds}秒"

    status_text = (
        "📊 机器人运行状态\n"
        "━━━━━━━━━━━━━━━\n"
        f"🤖 名称: QQ小助手\n"
        f"📌 框架: NoneBot2\n"
        f"🐍 Python: {platform.python_version()}\n"
        f"💻 系统: {platform.system()} {platform.release()}\n"
        f"⏱ 已运行: {uptime_str}\n"
        f"📅 启动于: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}\n"
        "━━━━━━━━━━━━━━━\n"
        "✅ 状态: 运行正常"
    )
    await status_cmd.finish(status_text)
