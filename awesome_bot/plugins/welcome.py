"""
入群欢迎插件
- 新成员加入群聊时自动发送欢迎消息
- 成员退群时发送提示
"""
import random

from nonebot import on_notice
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupIncreaseNoticeEvent,
    GroupDecreaseNoticeEvent,
    MessageSegment,
)


WELCOME_MESSAGES = [
    "🎉 欢迎 {name} 加入本群！快来做个自我介绍吧~",
    "👋 {name} 来啦！大家鼓掌欢迎~ 👏👏👏",
    "🌟 欢迎新朋友 {name}！有什么问题可以 @我 哦~",
    "🎊 热烈欢迎 {name}！请先看看群公告了解群规哦~",
    "✨ {name} 加入了我们！快和大家打个招呼吧！",
]

LEAVE_MESSAGES = [
    "👋 {name} 离开了群聊，祝一路顺风~",
    "😢 {name} 走了...希望以后还能再见！",
]


# ============== 入群欢迎 ==============
welcome = on_notice()


@welcome.handle()
async def handle_welcome(bot: Bot, event: GroupIncreaseNoticeEvent):
    # 忽略机器人自己入群
    if event.user_id == int(bot.self_id):
        return

    # 获取新成员信息
    try:
        user_info = await bot.get_group_member_info(
            group_id=event.group_id,
            user_id=event.user_id,
        )
        name = user_info.get("card") or user_info.get("nickname", str(event.user_id))
    except Exception:
        name = str(event.user_id)

    # 随机选择欢迎语
    msg_template = random.choice(WELCOME_MESSAGES)
    text = msg_template.format(name=name)

    # @新成员 + 欢迎语
    at = MessageSegment.at(event.user_id)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=at + f"\n{text}",
    )


# ============== 退群提示 ==============
leave_notice = on_notice()


@leave_notice.handle()
async def handle_leave(bot: Bot, event: GroupDecreaseNoticeEvent):
    # 忽略机器人自己退群 / 被踢
    if event.user_id == int(bot.self_id):
        return

    # 只处理主动退群，不处理被踢
    if event.sub_type == "kick":
        return

    try:
        # 退群后可能拿不到昵称，用缓存
        name = str(event.user_id)
    except Exception:
        name = str(event.user_id)

    msg = random.choice(LEAVE_MESSAGES).format(name=name)
    await bot.send_group_msg(
        group_id=event.group_id,
        message=msg,
    )
