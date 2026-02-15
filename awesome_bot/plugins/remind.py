"""
提醒闹钟插件
- /remind <时间> <内容> - 设定定时提醒
  时间格式: 30s / 5m / 1h / 1h30m
- /myremind - 查看我的提醒列表
"""
import re
import asyncio
from datetime import datetime, timedelta

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment


# 存储用户的提醒任务 {user_id: [(remind_id, end_time, content, task), ...]}
user_reminders: dict[str, list[tuple[int, datetime, str, asyncio.Task]]] = {}
_remind_counter = 0


def _parse_duration(text: str) -> int | None:
    """解析时间字符串，返回总秒数。支持: 30s, 5m, 1h, 1h30m, 90"""
    text = text.strip().lower()

    # 纯数字 → 当作分钟
    if text.isdigit():
        return int(text) * 60

    # 解析 h/m/s 组合
    pattern = r"(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?"
    match = re.fullmatch(pattern, text)
    if not match or not any(match.groups()):
        return None

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    total = hours * 3600 + minutes * 60 + seconds
    return total if total > 0 else None


def _format_duration(seconds: int) -> str:
    """格式化秒数为可读字符串"""
    if seconds < 60:
        return f"{seconds}秒"
    elif seconds < 3600:
        m, s = divmod(seconds, 60)
        return f"{m}分{s}秒" if s else f"{m}分钟"
    else:
        h, rem = divmod(seconds, 3600)
        m = rem // 60
        return f"{h}小时{m}分" if m else f"{h}小时"


# ============== 设置提醒 ==============
remind_cmd = on_command("remind", aliases={"提醒", "闹钟", "定时"}, priority=10, block=True)


@remind_cmd.handle()
async def handle_remind(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    global _remind_counter

    text = args.extract_plain_text().strip()
    if not text:
        await remind_cmd.finish(
            "⏰ 提醒用法:\n"
            "  /remind <时间> <内容>\n"
            "  时间格式: 30s / 5m / 1h / 1h30m\n"
            "  纯数字默认为分钟\n\n"
            "示例:\n"
            "  /remind 5m 该喝水了\n"
            "  /remind 1h30m 开会\n"
            "  /remind 30 吃饭"
        )

    # 分割时间和内容
    parts = text.split(None, 1)
    duration_str = parts[0]
    content = parts[1] if len(parts) > 1 else "时间到了！"

    seconds = _parse_duration(duration_str)
    if seconds is None:
        await remind_cmd.finish(
            "❌ 无法识别时间格式\n"
            "支持: 30s / 5m / 1h / 1h30m / 纯数字(分钟)"
        )

    # 限制最长提醒时间: 24小时
    if seconds > 86400:
        await remind_cmd.finish("❌ 提醒时间不能超过24小时")

    # 限制每人最多5个提醒
    user_id = event.get_user_id()
    if user_id not in user_reminders:
        user_reminders[user_id] = []

    # 清理已完成的提醒
    user_reminders[user_id] = [
        r for r in user_reminders[user_id] if not r[3].done()
    ]

    if len(user_reminders[user_id]) >= 5:
        await remind_cmd.finish("❌ 你已经有5个提醒了，请等待完成或取消")

    _remind_counter += 1
    remind_id = _remind_counter
    end_time = datetime.now() + timedelta(seconds=seconds)

    # 创建异步提醒任务
    async def reminder_task():
        await asyncio.sleep(seconds)
        try:
            at_msg = MessageSegment.at(user_id)
            await bot.send(
                event,
                at_msg + f" ⏰ 提醒: {content}",
            )
        except Exception:
            pass  # 发送失败就算了

    task = asyncio.create_task(reminder_task())
    user_reminders[user_id].append((remind_id, end_time, content, task))

    duration_text = _format_duration(seconds)
    await remind_cmd.finish(
        f"✅ 提醒已设置！\n"
        f"⏰ {duration_text}后 提醒你: {content}\n"
        f"🕐 预计时间: {end_time.strftime('%H:%M:%S')}"
    )


# ============== 查看我的提醒 ==============
my_remind = on_command("myremind", aliases={"我的提醒", "提醒列表"}, priority=10, block=True)


@my_remind.handle()
async def handle_my_remind(event: MessageEvent):
    user_id = event.get_user_id()
    reminders = user_reminders.get(user_id, [])

    # 清理已完成的
    active = [r for r in reminders if not r[3].done()]
    user_reminders[user_id] = active

    if not active:
        await my_remind.finish("📋 你当前没有待触发的提醒")

    lines = ["📋 你的提醒列表:", "━━━━━━━━━━━━━━━"]
    now = datetime.now()
    for rid, end_time, content, _ in active:
        remaining = max(0, int((end_time - now).total_seconds()))
        lines.append(
            f"  #{rid} | {_format_duration(remaining)}后 | {content}"
        )
    lines.append("━━━━━━━━━━━━━━━")

    await my_remind.finish("\n".join(lines))
