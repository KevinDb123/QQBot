"""
自动+1 插件
- 当群里连续3条相同消息时（可以是同一个人），机器人自动跟一句 +1
"""
import time
from collections import defaultdict

from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent


# 触发 +1 所需的相同消息次数
PLUS_ONE_THRESHOLD = 3
# 消息时效（秒），超过这个时间的连续消息不算
MSG_TIMEOUT = 120
# 冷却时间（秒），同一个群同一条内容在这段时间内不会再次 +1
COOLDOWN = 300

# 记录每个群最近的连续消息 {group_id: {"text": str, "count": int, "time": float}}
_group_chain: dict[int, dict] = defaultdict(lambda: {"text": "", "count": 0, "time": 0.0})
# 冷却记录 {(group_id, text): timestamp}
_cooldowns: dict[tuple[int, str], float] = {}


plus_one = on_message(priority=998, block=False)


@plus_one.handle()
async def handle_plus_one(bot: Bot, event: GroupMessageEvent):
    text = event.get_plaintext().strip()
    if not text or text.startswith("/"):
        return

    group_id = event.group_id
    user_id = event.get_user_id()
    bot_id = bot.self_id
    now = time.time()

    # 跳过机器人自己发的消息
    if user_id == bot_id:
        return

    chain = _group_chain[group_id]

    # 检查是否与上一条相同且在时效内
    if text == chain["text"] and (now - chain["time"]) < MSG_TIMEOUT:
        chain["count"] += 1
        chain["time"] = now
    else:
        # 新消息，重置链
        _group_chain[group_id] = {
            "text": text,
            "count": 1,
            "time": now,
        }
        chain = _group_chain[group_id]

    # 检查是否达到阈值
    if chain["count"] >= PLUS_ONE_THRESHOLD:
        # 检查冷却
        cd_key = (group_id, text)
        if cd_key in _cooldowns and (now - _cooldowns[cd_key]) < COOLDOWN:
            return

        _cooldowns[cd_key] = now
        # 重置链，防止重复触发
        _group_chain[group_id] = {"text": "", "count": 0, "time": 0.0}

        await bot.send(event, text)

        # 清理过期冷却记录
        expired = [k for k, t in _cooldowns.items() if now - t > COOLDOWN]
        for k in expired:
            del _cooldowns[k]
