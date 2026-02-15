"""
今日热搜插件
- /hot - 查看微博热搜 TOP20
- /hotsearch - 同上
"""
import httpx
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent


hot_cmd = on_command("hot", aliases={"热搜", "hotsearch", "微博热搜", "今日热搜"}, priority=10, block=True)


@hot_cmd.handle()
async def handle_hot(event: MessageEvent):
    await hot_cmd.send("🔍 正在获取热搜...")

    # 先尝试微博热搜
    data = await _fetch_weibo_hot()
    if data:
        await bot_send_and_stop(hot_cmd, data)
        return

    # 备用：百度热搜
    data = await _fetch_baidu_hot()
    if data:
        await bot_send_and_stop(hot_cmd, data)
        return

    await bot_send_and_stop(hot_cmd, "⚠️ 热搜获取失败，请稍后再试~")


async def bot_send_and_stop(matcher, msg: str):
    """发送消息（不抛 FinishedException）"""
    try:
        await matcher.finish(msg)
    except Exception:
        pass


async def _fetch_weibo_hot() -> str | None:
    """获取微博热搜"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://weibo.com/ajax/side/hotSearch",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    "Referer": "https://weibo.com/",
                },
            )
            resp.raise_for_status()
            result = resp.json()

        realtime = result.get("data", {}).get("realtime", [])
        if not realtime:
            return None

        lines = [
            "🔥 微博热搜 TOP20",
            "━━━━━━━━━━━━━━━",
        ]

        for i, item in enumerate(realtime[:20], 1):
            word = item.get("word", "")
            hot_num = item.get("num", 0)
            label = item.get("label_name", "")

            # 标签图标
            label_icon = ""
            if label == "新":
                label_icon = "🆕"
            elif label == "热":
                label_icon = "🔥"
            elif label == "沸":
                label_icon = "💥"
            elif label == "爆":
                label_icon = "💣"

            # 热度格式化
            if hot_num > 10000:
                hot_str = f"{hot_num / 10000:.1f}万"
            else:
                hot_str = str(hot_num)

            if i <= 3:
                rank_icon = ["1️⃣", "2️⃣", "3️⃣"][i - 1]
            else:
                rank_icon = f"{i:2d}."

            lines.append(f"{rank_icon} {label_icon}{word}  ({hot_str})")

        lines.append("━━━━━━━━━━━━━━━")

        from datetime import datetime
        lines.append(f"📅 更新时间: {datetime.now().strftime('%H:%M:%S')}")

        return "\n".join(lines)

    except Exception:
        return None


async def _fetch_baidu_hot() -> str | None:
    """备用：获取百度热搜"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                "https://top.baidu.com/api/board?platform=wise&tab=realtime",
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
            )
            resp.raise_for_status()
            result = resp.json()

        cards = result.get("data", {}).get("cards", [])
        if not cards:
            return None

        items = cards[0].get("content", [])
        if not items:
            return None

        lines = [
            "🔍 百度热搜 TOP20",
            "━━━━━━━━━━━━━━━",
        ]

        for i, item in enumerate(items[:20], 1):
            word = item.get("word", "") or item.get("query", "")
            hot_score = item.get("hotScore", "")

            if i <= 3:
                rank_icon = ["1️⃣", "2️⃣", "3️⃣"][i - 1]
            else:
                rank_icon = f"{i:2d}."

            lines.append(f"{rank_icon} {word}  ({hot_score})")

        lines.append("━━━━━━━━━━━━━━━")

        from datetime import datetime
        lines.append(f"📅 更新时间: {datetime.now().strftime('%H:%M:%S')}")

        return "\n".join(lines)

    except Exception:
        return None
