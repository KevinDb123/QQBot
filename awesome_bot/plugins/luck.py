"""
今日运势插件
- /luck - 查看今日运势（每天每人固定结果）
"""
import hashlib
from datetime import date

from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent


luck_cmd = on_command("luck", aliases={"运势", "今日运势", "每日运势"}, priority=10, block=True)

# 运势等级
FORTUNE_LEVELS = [
    ("大吉", "🌟🌟🌟🌟🌟", "今天运气爆棚！做什么都顺利~"),
    ("中吉", "🌟🌟🌟🌟", "运气不错，适合尝试新事物！"),
    ("小吉", "🌟🌟🌟", "平稳的一天，稳中有进~"),
    ("吉", "🌟🌟", "还不错，保持好心情就好！"),
    ("末吉", "🌟", "运气一般，但也没什么坏事~"),
    ("凶", "💀", "小心谨慎，注意避坑！"),
    ("大凶", "💀💀", "今天还是躺平吧...明天会更好的！"),
]

LUCKY_COLORS = [
    "红色 🔴", "橙色 🟠", "黄色 🟡", "绿色 🟢",
    "青色 🩵", "蓝色 🔵", "紫色 🟣", "粉色 🩷",
    "白色 ⚪", "黑色 ⚫", "金色 ✨",
]

LUCKY_DIRECTIONS = ["东", "南", "西", "北", "东南", "东北", "西南", "西北"]

ACTIVITIES = [
    ("宜", [
        "写代码", "打游戏", "看番", "散步", "吃火锅",
        "摸鱼", "学习", "早睡", "运动", "听音乐",
        "逛街", "看电影", "画画", "发呆", "整理房间",
    ]),
    ("忌", [
        "熬夜", "吃外卖", "迟到", "说谎", "冲动消费",
        "翘课", "拖延", "生气", "暴饮暴食", "刷手机",
        "赖床", "抱怨", "久坐", "喝冰水", "忘带伞",
    ]),
]


def _daily_hash(user_id: str, salt: str = "") -> int:
    """根据用户ID和日期生成当日固定的哈希值"""
    today = date.today().isoformat()
    raw = f"{user_id}:{today}:{salt}"
    return int(hashlib.md5(raw.encode()).hexdigest(), 16)


@luck_cmd.handle()
async def handle_luck(event: MessageEvent):
    user_id = event.get_user_id()

    # 用不同 salt 生成各项数据，保证每项独立随机但当日固定
    h_fortune = _daily_hash(user_id, "fortune")
    h_color = _daily_hash(user_id, "color")
    h_dir = _daily_hash(user_id, "direction")
    h_num = _daily_hash(user_id, "number")
    h_act1 = _daily_hash(user_id, "act_good")
    h_act2 = _daily_hash(user_id, "act_bad")

    fortune = FORTUNE_LEVELS[h_fortune % len(FORTUNE_LEVELS)]
    color = LUCKY_COLORS[h_color % len(LUCKY_COLORS)]
    direction = LUCKY_DIRECTIONS[h_dir % len(LUCKY_DIRECTIONS)]
    lucky_num = (h_num % 99) + 1

    good_activities = ACTIVITIES[0][1]
    bad_activities = ACTIVITIES[1][1]
    good = good_activities[h_act1 % len(good_activities)]
    bad = bad_activities[h_act2 % len(bad_activities)]

    text = (
        f"🔮 今日运势\n"
        f"━━━━━━━━━━━━━━━\n"
        f"运势: {fortune[0]} {fortune[1]}\n"
        f"💬 {fortune[2]}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🎨 幸运色: {color}\n"
        f"🔢 幸运数字: {lucky_num}\n"
        f"🧭 幸运方位: {direction}\n"
        f"✅ 宜: {good}\n"
        f"❌ 忌: {bad}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📅 {date.today().strftime('%Y年%m月%d日')}"
    )
    await luck_cmd.finish(text)
