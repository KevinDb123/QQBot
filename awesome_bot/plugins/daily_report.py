"""
群聊江湖日报插件
- 自动在每晚 22:00 生成《本群江湖日报》
- /report - 手动触发生成日报
- 用 AI 以毒舌/武侠风格总结群聊
"""
import os
import asyncio
from datetime import datetime, time as dtime
from collections import Counter, defaultdict

import httpx
from nonebot import on_command, get_driver, get_bot
from nonebot.adapters.onebot.v11 import Bot, MessageEvent, GroupMessageEvent
from nonebot.log import logger

driver = get_driver()

# 复用 AI 配置
_AI_PROVIDER = "doubao"
_ARK_API_KEY = ""
_DOUBAO_MODEL = "doubao-seed-2-0-mini-260215"
_DEEPSEEK_API_KEY = ""
_DEEPSEEK_MODEL = "deepseek-chat"

# 自动日报时间（24小时制）
REPORT_HOUR = 22
REPORT_MINUTE = 0

# 已发送日报的群（防止重复）
_reported_today: set[int] = set()


@driver.on_startup
async def _load_report_config():
    global _AI_PROVIDER, _ARK_API_KEY, _DOUBAO_MODEL, _DEEPSEEK_API_KEY, _DEEPSEEK_MODEL
    config = driver.config
    _AI_PROVIDER = getattr(config, "ai_provider", "") or _AI_PROVIDER
    _ARK_API_KEY = getattr(config, "ark_api_key", "") or os.environ.get("ARK_API_KEY", "")
    _DOUBAO_MODEL = getattr(config, "doubao_model", "") or _DOUBAO_MODEL
    _DEEPSEEK_API_KEY = getattr(config, "deepseek_api_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    _DEEPSEEK_MODEL = getattr(config, "deepseek_model", "") or _DEEPSEEK_MODEL

    # 启动定时任务
    asyncio.create_task(_daily_report_scheduler())
    logger.info(f"江湖日报定时任务已启动，每天 {REPORT_HOUR}:{REPORT_MINUTE:02d} 自动发送")


async def _daily_report_scheduler():
    """定时任务：每天定点发送日报"""
    while True:
        now = datetime.now()
        # 计算下次触发时间
        target = now.replace(hour=REPORT_HOUR, minute=REPORT_MINUTE, second=0, microsecond=0)
        if now >= target:
            # 今天的时间已过，等明天
            from datetime import timedelta
            target += timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        logger.info(f"江湖日报将在 {wait_seconds:.0f} 秒后发送")
        await asyncio.sleep(wait_seconds)

        # 到点了，发送日报
        try:
            await _send_all_group_reports()
        except Exception as e:
            logger.error(f"自动日报发送失败: {e}")

        # 重置标记
        _reported_today.clear()
        # 等1分钟避免重复触发
        await asyncio.sleep(61)


async def _send_all_group_reports():
    """向所有有消息记录的群发送日报"""
    try:
        bot = get_bot()
    except Exception:
        logger.warning("日报发送失败：没有可用的 Bot")
        return

    # 从 wordcloud_plugin 获取群消息
    from awesome_bot.plugins.wordcloud_plugin import group_messages

    for group_id, messages in group_messages.items():
        if group_id in _reported_today:
            continue
        if len(messages) < 5:
            continue

        try:
            report = await _generate_report(group_id, messages)
            await bot.send_group_msg(group_id=group_id, message=report)
            _reported_today.add(group_id)
            await asyncio.sleep(2)  # 避免发送过快
        except Exception as e:
            logger.error(f"群 {group_id} 日报发送失败: {e}")


def _analyze_stats(messages: list[tuple[float, str, str]]) -> dict:
    """分析群聊统计数据"""
    user_msg_count: Counter = Counter()
    user_char_count: Counter = Counter()
    user_messages: dict[str, list[str]] = defaultdict(list)

    for _, user_id, text in messages:
        user_msg_count[user_id] += 1
        user_char_count[user_id] += len(text)
        user_messages[user_id].append(text)

    # 水群王（消息最多）
    top_talker = user_msg_count.most_common(1)[0] if user_msg_count else ("未知", 0)
    # 话痨王（字数最多）
    top_writer = user_char_count.most_common(1)[0] if user_char_count else ("未知", 0)
    # 潜水王（消息最少）
    if len(user_msg_count) > 1:
        least_talker = user_msg_count.most_common()[-1]
    else:
        least_talker = ("未知", 0)

    # 最短消息
    shortest = min(messages, key=lambda x: len(x[2]))
    # 最长消息
    longest = max(messages, key=lambda x: len(x[2]))

    return {
        "total_msgs": len(messages),
        "total_users": len(user_msg_count),
        "top_talker_id": top_talker[0],
        "top_talker_count": top_talker[1],
        "top_writer_id": top_writer[0],
        "top_writer_chars": top_writer[1],
        "least_talker_id": least_talker[0],
        "least_talker_count": least_talker[1],
        "shortest_msg": shortest[2][:50],
        "shortest_user": shortest[1],
        "longest_msg": longest[2][:100],
        "longest_user": longest[1],
        "sample_messages": [text for _, _, text in messages[-50:]],  # 最近50条
    }


async def _generate_report(group_id: int, messages: list[tuple[float, str, str]]) -> str:
    """使用 AI 生成江湖日报"""
    stats = _analyze_stats(messages)

    # 构建 prompt
    report_prompt = (
        "你是一个幽默毒舌的武侠风格群聊总结大师。请根据以下群聊统计数据，"
        "写一份《本群江湖日报》。要求：\n"
        "1. 用武侠/江湖风格的幽默口吻\n"
        "2. 点评'水群王'（发言最多的人）\n"
        "3. 挖掘有趣的聊天内容\n"
        "4. 给出今日群聊评价\n"
        "5. 控制在300字以内\n"
        "6. 用户ID用格式 @用户XXXXX 表示\n\n"
        f"📊 今日统计:\n"
        f"- 总消息数: {stats['total_msgs']} 条\n"
        f"- 参与人数: {stats['total_users']} 人\n"
        f"- 水群王: 用户{stats['top_talker_id']}（{stats['top_talker_count']}条消息）\n"
        f"- 话痨王: 用户{stats['top_writer_id']}（{stats['top_writer_chars']}字）\n"
        f"- 潜水冠军: 用户{stats['least_talker_id']}（仅{stats['least_talker_count']}条）\n"
        f"- 最短消息: '{stats['shortest_msg']}' by 用户{stats['shortest_user']}\n"
        f"- 最长消息: '{stats['longest_msg']}...' by 用户{stats['longest_user']}\n\n"
        f"最近聊天内容摘要:\n"
    )

    # 添加部分聊天内容
    for msg in stats["sample_messages"][-30:]:
        report_prompt += f"- {msg[:80]}\n"

    ai_messages = [
        {"role": "system", "content": report_prompt},
        {"role": "user", "content": "请生成今日的《本群江湖日报》"},
    ]

    try:
        result = await _call_ai(ai_messages)
        today = datetime.now().strftime("%Y年%m月%d日")
        return f"📜 《本群江湖日报》\n📅 {today}\n━━━━━━━━━━━━━━━\n{result}\n━━━━━━━━━━━━━━━\n🤖 由AI自动生成"
    except Exception as e:
        return f"⚠️ 日报生成失败: {e}"


async def _call_ai(messages: list[dict]) -> str:
    """调用 AI 生成内容"""
    if _AI_PROVIDER == "deepseek":
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {_DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": 0.9,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    else:
        from volcenginesdkarkruntime import Ark
        client = Ark(api_key=_ARK_API_KEY)
        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=_DOUBAO_MODEL,
                messages=messages,
            ),
        )
        return completion.choices[0].message.content


# ============== 手动触发日报 ==============
report_cmd = on_command("report", aliases={"日报", "江湖日报", "群报"}, priority=10, block=True)


@report_cmd.handle()
async def handle_report(bot: Bot, event: GroupMessageEvent):
    from awesome_bot.plugins.wordcloud_plugin import group_messages

    group_id = event.group_id
    messages = group_messages.get(group_id, [])

    if len(messages) < 5:
        await report_cmd.finish(
            "📜 消息太少了，还不够写一份日报\n"
            "至少需要5条消息，再聊聊吧~"
        )

    await report_cmd.send("📝 正在撰写《本群江湖日报》，请稍候...")

    try:
        report = await _generate_report(group_id, messages)
        await report_cmd.finish(report)
    except Exception as e:
        await report_cmd.finish(f"⚠️ 日报生成失败: {e}")
