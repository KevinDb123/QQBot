"""
实用工具插件 - 掷骰子
"""
import random

from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageEvent


# ============== 掷骰子 ==============
roll_cmd = on_command("roll", aliases={"掷骰子", "骰子"}, priority=10, block=True)


@roll_cmd.handle()
async def handle_roll(event: MessageEvent, args: Message = CommandArg()):
    arg = args.extract_plain_text().strip()

    max_num = 6  # 默认 6 面骰子
    if arg:
        try:
            max_num = int(arg)
            if max_num < 1:
                max_num = 6
        except ValueError:
            await roll_cmd.finish("请输入一个有效的数字，例如: /roll 100")

    result = random.randint(1, max_num)
    await roll_cmd.finish(f"🎲 掷骰子 (1-{max_num})\n结果: 【{result}】")
