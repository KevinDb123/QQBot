"""
拍一拍插件
- /拍 @某人 [次数] - 让机器人拍某人（最多5次）
- 被拍时自动反击拍回去
"""
import asyncio

from nonebot import on_command, on_notice
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    PokeNotifyEvent,
    MessageSegment,
)


# ============== 主动拍一拍 ==============
poke_cmd = on_command("poke", aliases={"拍", "戳"}, priority=10, block=True)


@poke_cmd.handle()
async def handle_poke(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 提取被 @ 的目标用户
    target_id = None
    for seg in args:
        if seg.type == "at":
            target_id = seg.data.get("qq")
            break

    if not target_id:
        await poke_cmd.finish("请 @ 你要拍的人，例如: /拍 @某人 3")

    # 提取次数
    text = args.extract_plain_text().strip()
    times = 1
    if text:
        try:
            times = int(text)
        except ValueError:
            pass

    # 限制最多5次
    if times < 1:
        times = 1
    if times > 5:
        times = 5

    group_id = event.group_id

    # 执行拍一拍
    success_count = 0
    for i in range(times):
        try:
            # NapCat 使用 group_poke API
            await bot.call_api(
                "group_poke",
                group_id=group_id,
                user_id=int(target_id),
            )
            success_count += 1
            if i < times - 1:
                await asyncio.sleep(0.5)  # 间隔 0.5 秒
        except Exception:
            try:
                # 备用：尝试发送 poke 消息段
                await bot.call_api(
                    "send_group_msg",
                    group_id=group_id,
                    message=[{"type": "poke", "data": {"qq": str(target_id)}}],
                )
                success_count += 1
                if i < times - 1:
                    await asyncio.sleep(0.5)
            except Exception:
                break

    if success_count == 0:
        await poke_cmd.finish("😅 拍一拍失败了，可能不支持此功能")


# ============== 被拍反击 ==============
poke_back = on_notice()


@poke_back.handle()
async def handle_poke_back(bot: Bot, event: PokeNotifyEvent):
    # 只处理群聊中的拍一拍，且目标是机器人自己
    if not hasattr(event, "group_id") or not event.group_id:
        return

    # 获取机器人自身的 QQ 号
    self_id = int(bot.self_id)

    # 检查是否是拍机器人的
    if event.target_id != self_id:
        return

    # 不要对自己反击
    if event.user_id == self_id:
        return

    # 好感度随机变化 -2 ~ +2
    try:
        import random
        from awesome_bot.plugins.affinity import change_favor
        delta = random.randint(-2, 2)
        if delta != 0:
            change_favor(str(event.user_id), delta, "拍机器人")
    except Exception:
        pass

    # 反击！拍回去
    try:
        await bot.call_api(
            "group_poke",
            group_id=event.group_id,
            user_id=event.user_id,
        )
    except Exception:
        try:
            await bot.call_api(
                "send_group_msg",
                group_id=event.group_id,
                message=[{"type": "poke", "data": {"qq": str(event.user_id)}}],
            )
        except Exception:
            # 如果拍不了，发个文字消息
            await bot.send_group_msg(
                group_id=event.group_id,
                message="哼，你竟然拍我！👊",
            )
