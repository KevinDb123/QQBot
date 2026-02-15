"""
帮助插件 - 显示机器人功能列表
支持命令: /help, /帮助, /菜单
"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent

help_cmd = on_command("help", aliases={"帮助", "菜单", "功能"}, priority=10, block=True)


@help_cmd.handle()
async def handle_help(event: MessageEvent):
    help_text = (
        "🤖 QQ小助手 - 功能菜单\n"
        "━━━━━━━━━━━━━━━\n"
        "📌 基础功能:\n"
        "  /hello - 打个招呼\n"
        "  /help - 查看本帮助信息\n"
        "  /echo <内容> - 复读消息\n"
        "  /roll [n] - 掷骰子(1-n)\n"
        "\n"
        "🎮 趣味互动:\n"
        "  /poke @某人 [次数] - 拍一拍\n"
        "  /luck - 今日运势\n"
        "  /sign - 每日签到\n"
        "  /rank - 签到排行榜\n"
        "  /favor - 查看好感度\n"
        "  /favorrank - 好感度排行榜\n"
        "\n"
        "🤖 AI 对话:\n"
        "  @我 - AI对话 | 引用+@我 - 针对引用回答\n"
        "  /chat <内容> - AI对话\n"
        "  /model - 查看/切换模型\n"
        "  /switchai <引擎> - 切换AI引擎\n"
        "  /clear - 清除对话记录\n"
        "  /prompt <提示词> - 自定义人设\n"
        "\n"
        "🛠 实用工具:\n"
        "  /translate <内容> - AI翻译\n"
        "  /tren /trja /trko - 指定语言翻译\n"
        "  /remind <时间> <内容> - 定时提醒\n"
        "  /myremind - 查看我的提醒\n"
        "\n"
        "📊 群数据:\n"
        "  /wordcloud - 群聊词云\n"
        "  /report - 江湖日报(AI总结群聊)\n"
        "  /hot - 今日热搜\n"
        "  /status - 机器人状态\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 @我即可对话 | 每晚22:00自动日报"
    )
    await help_cmd.finish(help_text)
