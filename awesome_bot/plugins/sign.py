"""
签到系统插件
- /sign - 每日签到
- /rank - 签到排行榜（积分TOP10）
"""
import json
import os
import random
from datetime import date, datetime

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent, GroupMessageEvent


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
SIGN_FILE = os.path.join(DATA_DIR, "sign_data.json")


def _load_data() -> dict:
    """加载签到数据"""
    if os.path.exists(SIGN_FILE):
        try:
            with open(SIGN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_data(data: dict):
    """保存签到数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SIGN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ============== 签到 ==============
sign_cmd = on_command("sign", aliases={"签到", "打卡"}, priority=10, block=True)


@sign_cmd.handle()
async def handle_sign(event: MessageEvent):
    user_id = event.get_user_id()
    today = date.today().isoformat()
    data = _load_data()

    if user_id not in data:
        data[user_id] = {
            "points": 0,
            "streak": 0,
            "total_days": 0,
            "last_sign": "",
        }

    user = data[user_id]

    # 检查是否已签到
    if user["last_sign"] == today:
        await sign_cmd.finish(
            f"📋 今天已经签过到啦~\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💰 当前积分: {user['points']}\n"
            f"🔥 连续签到: {user['streak']} 天\n"
            f"📊 累计签到: {user['total_days']} 天\n"
            f"━━━━━━━━━━━━━━━\n"
            f"明天再来吧！"
        )

    # 计算连续签到
    from datetime import timedelta
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if user["last_sign"] == yesterday:
        user["streak"] += 1
    else:
        user["streak"] = 1

    # 计算积分（基础10 + 连续奖励 + 随机奖励）
    base_points = 10
    streak_bonus = min(user["streak"] * 2, 20)  # 连续签到奖励，最多+20
    random_bonus = random.randint(1, 10)
    total_earned = base_points + streak_bonus + random_bonus

    user["points"] += total_earned
    user["total_days"] += 1
    user["last_sign"] = today

    _save_data(data)

    text = (
        f"✅ 签到成功！\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 获得积分: +{total_earned}\n"
        f"  ├ 基础: +{base_points}\n"
        f"  ├ 连续奖励: +{streak_bonus}\n"
        f"  └ 随机奖励: +{random_bonus}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 总积分: {user['points']}\n"
        f"🔥 连续签到: {user['streak']} 天\n"
        f"📊 累计签到: {user['total_days']} 天"
    )
    await sign_cmd.finish(text)


# ============== 排行榜 ==============
rank_cmd = on_command("rank", aliases={"排行", "排行榜", "积分榜"}, priority=10, block=True)


@rank_cmd.handle()
async def handle_rank(event: MessageEvent):
    data = _load_data()

    if not data:
        await rank_cmd.finish("📊 还没有人签到过哦，快来 /sign 签到吧！")

    # 按积分排序
    sorted_users = sorted(data.items(), key=lambda x: x[1]["points"], reverse=True)[:10]

    lines = [
        "🏆 签到积分排行榜 TOP10",
        "━━━━━━━━━━━━━━━",
    ]

    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, info) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f" {i + 1}."
        lines.append(
            f"{medal} {uid} | 💰{info['points']} | 🔥{info['streak']}天"
        )

    lines.append("━━━━━━━━━━━━━━━")
    lines.append(f"共 {len(data)} 人参与签到")

    await rank_cmd.finish("\n".join(lines))
