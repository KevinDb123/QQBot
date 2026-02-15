""" 
AI 对话插件 - 支持 DeepSeek 和 豆包(Doubao) 双引擎
- 私聊直接对话
- 群聊 @机器人 或引用机器人消息 触发对话
- 支持上下文记忆（每个用户最近25轮对话）
- /切换ai 可在 deepseek/doubao 之间切换
- /模型 可切换具体模型
"""
import os
import re
import time
import asyncio
from collections import defaultdict

import httpx
from nonebot import on_command, on_message, get_driver
from nonebot.params import CommandArg
from nonebot.rule import to_me
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    PrivateMessageEvent,
    MessageSegment,
)

# ============== 配置 ==============
driver = get_driver()

# AI 提供商配置
AI_PROVIDER: str = "doubao"  # deepseek 或 doubao

# DeepSeek 配置
DEEPSEEK_API_KEY: str = ""
DEEPSEEK_MODEL: str = "deepseek-chat"
DEEPSEEK_API_URL: str = "https://api.deepseek.com/chat/completions"

# 豆包配置
ARK_API_KEY: str = ""
DOUBAO_MODEL: str = "doubao-seed-2-0-mini-260215"

# 可用模型列表
AVAILABLE_MODELS = {
    # 豆包模型
    "doubao-seed-2-0-mini-260215": {"provider": "doubao", "name": "豆包 Seed 2.0 Mini", "desc": "轻量快速"},
    "doubao-1-5-pro-32k-250115": {"provider": "doubao", "name": "豆包 1.5 Pro 32K", "desc": "均衡性能"},
    "doubao-1-5-lite-32k-250115": {"provider": "doubao", "name": "豆包 1.5 Lite 32K", "desc": "轻量经济"},
    "doubao-pro-32k": {"provider": "doubao", "name": "豆包 Pro 32K", "desc": "专业版"},
    "doubao-pro-128k": {"provider": "doubao", "name": "豆包 Pro 128K", "desc": "超长上下文"},
    "doubao-lite-32k": {"provider": "doubao", "name": "豆包 Lite 32K", "desc": "轻量版"},
    "doubao-lite-128k": {"provider": "doubao", "name": "豆包 Lite 128K", "desc": "轻量长文本"},
    # DeepSeek 模型
    "deepseek-chat": {"provider": "deepseek", "name": "DeepSeek Chat", "desc": "通用对话，不用推理"},
    "deepseek-reasoner": {"provider": "deepseek", "name": "DeepSeek Reasoner", "desc": "深度推理"},
}

# 系统提示词，定义机器人的性格
SYSTEM_PROMPT = (
    "你是一个友善、活泼的QQ群聊助手，名字叫小助手。"
    "请用简洁自然的中文回复，适当使用表情让对话更生动。"
    "回复尽量控制在200字以内，避免过长。"
)

# 用户自定义 prompt（每个用户可定制）
custom_prompts: dict[str, str] = {}

# 最大回复字数限制（超过则截断）
MAX_RESPONSE_LENGTH = 100

# 违禁词列表（匹配到则拒绝回答并拍一拍）
BANNED_WORDS: list[str] = [
    "色情", "裸体", "做爱", "性爱", "约炮",
    "毒品", "大麻", "冰毒", "海洛因",
    "自杀", "自残",
    "炸弹", "恐怖袭击", "制造武器",
    "赌博", "洗钱",
]


def _check_banned(text: str) -> bool:
    """检查文本是否包含违禁词"""
    text_lower = text.lower()
    for word in BANNED_WORDS:
        if word in text_lower:
            return True
    return False


async def _poke_user(bot: Bot, event: MessageEvent):
    """拍一拍用户（违禁内容时调用）"""
    if isinstance(event, GroupMessageEvent):
        try:
            await bot.call_api(
                "group_poke",
                group_id=event.group_id,
                user_id=event.user_id,
            )
        except Exception:
            await bot.send(event, "👊 不许问这种问题！")
    else:
        # 私聊无法拍一拍，发文字提醒
        await bot.send(event, "👊 不许问这种问题！")


# 用户对话历史（每个用户最多保存25轮）
MAX_HISTORY = 25
chat_histories: dict[str, list[dict]] = defaultdict(list)

# 历史记录过期时间（30分钟）
chat_timestamps: dict[str, float] = {}
HISTORY_EXPIRE = 30 * 60


@driver.on_startup
async def _load_config():
    global AI_PROVIDER, DEEPSEEK_API_KEY, DEEPSEEK_MODEL, ARK_API_KEY, DOUBAO_MODEL
    config = driver.config

    AI_PROVIDER = getattr(config, "ai_provider", "") or AI_PROVIDER
    DEEPSEEK_API_KEY = getattr(config, "deepseek_api_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    DEEPSEEK_MODEL = getattr(config, "deepseek_model", "") or DEEPSEEK_MODEL
    ARK_API_KEY = getattr(config, "ark_api_key", "") or os.environ.get("ARK_API_KEY", "")
    DOUBAO_MODEL = getattr(config, "doubao_model", "") or DOUBAO_MODEL

    from nonebot.log import logger
    logger.info(f"AI 对话插件已加载，当前提供商: {AI_PROVIDER}")
    if AI_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        logger.warning("未配置 DEEPSEEK_API_KEY！请在 .env 中设置")
    if AI_PROVIDER == "doubao" and not ARK_API_KEY:
        logger.warning("未配置 ARK_API_KEY！请在 .env 中设置")


# ============== 自定义 Prompt ==============
prompt_cmd = on_command("prompt", aliases={"设置提示词", "人设"}, priority=10, block=True)


@prompt_cmd.handle()
async def handle_prompt(event: MessageEvent, args: Message = CommandArg()):
    user_id = event.get_user_id()
    text = args.extract_plain_text().strip()

    if not text:
        # 没有参数 -> 显示当前 prompt
        current = custom_prompts.get(user_id)
        if current:
            await prompt_cmd.finish(
                f"📝 你当前的自定义 Prompt:\n{current}\n\n"
                f"发送 /prompt reset 可恢复默认"
            )
        else:
            await prompt_cmd.finish(
                f"📝 当前使用默认 Prompt\n\n"
                f"用法:\n"
                f"  /prompt <你的提示词> - 设置自定义人设\n"
                f"  /prompt reset - 恢复默认\n\n"
                f"示例: /prompt 你是一只可爱的猫娘，每句话结尾都要加'喵~'"
            )
        return

    if text.lower() in ("reset", "默认", "清除"):
        custom_prompts.pop(user_id, None)
        await prompt_cmd.finish("✅ 已恢复默认 Prompt")
        return

    # 设置自定义 prompt
    custom_prompts[user_id] = text
    await prompt_cmd.finish(
        f"✅ 自定义 Prompt 已设置:\n{text}\n\n"
        f"发送 /prompt reset 可恢复默认"
    )


# ============== 切换 AI 提供商 ==============
switch_cmd = on_command("switchai", aliases={"切换ai", "切换AI"}, priority=10, block=True)


@switch_cmd.handle()
async def handle_switch(event: MessageEvent, args: Message = CommandArg()):
    global AI_PROVIDER
    target = args.extract_plain_text().strip().lower()

    if target in ("deepseek", "ds"):
        AI_PROVIDER = "deepseek"
        current_model = DEEPSEEK_MODEL
        await switch_cmd.finish(f"✅ 已切换到 DeepSeek\n当前模型: {current_model}")
    elif target in ("doubao", "豆包"):
        AI_PROVIDER = "doubao"
        current_model = DOUBAO_MODEL
        await switch_cmd.finish(f"✅ 已切换到 豆包(Doubao)\n当前模型: {current_model}")
    else:
        current_model = DOUBAO_MODEL if AI_PROVIDER == "doubao" else DEEPSEEK_MODEL
        await switch_cmd.finish(
            f"🔄 当前 AI: {AI_PROVIDER} | 模型: {current_model}\n"
            f"用法: /切换ai deepseek 或 /切换ai doubao"
        )


# ============== 切换/查看模型 ==============
model_cmd = on_command("model", aliases={"模型", "切换模型"}, priority=10, block=True)


@model_cmd.handle()
async def handle_model(event: MessageEvent, args: Message = CommandArg()):
    global AI_PROVIDER, DEEPSEEK_MODEL, DOUBAO_MODEL
    target = args.extract_plain_text().strip()

    if not target:
        # 显示可用模型列表
        current_model = DOUBAO_MODEL if AI_PROVIDER == "doubao" else DEEPSEEK_MODEL
        lines = [
            f"🤖 当前: {AI_PROVIDER} | {current_model}",
            "━━━━━━━━━━━━━━━",
            "🌟 豆包模型:",
        ]
        for mid, info in AVAILABLE_MODELS.items():
            if info["provider"] == "doubao":
                mark = " ◀" if mid == current_model else ""
                lines.append(f"  {mid}\n    {info['desc']}{mark}")
        lines.append("\n🔵 DeepSeek 模型:")
        for mid, info in AVAILABLE_MODELS.items():
            if info["provider"] == "deepseek":
                mark = " ◀" if mid == current_model else ""
                lines.append(f"  {mid}\n    {info['desc']}{mark}")
        lines.append("━━━━━━━━━━━━━━━")
        lines.append("用法: /模型 <模型名>")
        await model_cmd.finish("\n".join(lines))
    else:
        # 切换模型
        if target in AVAILABLE_MODELS:
            info = AVAILABLE_MODELS[target]
            if info["provider"] == "doubao":
                DOUBAO_MODEL = target
                AI_PROVIDER = "doubao"
            else:
                DEEPSEEK_MODEL = target
                AI_PROVIDER = "deepseek"
            await model_cmd.finish(
                f"✅ 已切换模型\n"
                f"提供商: {info['provider']}\n"
                f"模型: {target}\n"
                f"说明: {info['desc']}"
            )
        else:
            # 允许直接输入任意模型名
            if target.startswith("deepseek"):
                DEEPSEEK_MODEL = target
                AI_PROVIDER = "deepseek"
                await model_cmd.finish(f"✅ 已切换到 DeepSeek 模型: {target}")
            elif target.startswith("doubao"):
                DOUBAO_MODEL = target
                AI_PROVIDER = "doubao"
                await model_cmd.finish(f"✅ 已切换到豆包模型: {target}")
            else:
                await model_cmd.finish(
                    f"❌ 未识别的模型: {target}\n"
                    f"请使用 /模型 查看可用列表\n"
                    f"或输入以 doubao/deepseek 开头的模型名"
                )


# ============== AI 对话（@机器人 或 引用机器人消息 或 私聊）==============
ai_chat = on_message(rule=to_me(), priority=99, block=False)


@ai_chat.handle()
async def handle_ai_chat(bot: Bot, event: MessageEvent):
    # 提取纯文本（去除 @和回复段）
    user_input = event.get_plaintext().strip()

    # 检查是否有引用/回复消息，拼入上下文
    quoted_text = _extract_reply_text(event)
    if quoted_text:
        if user_input:
            user_input = f"[引用消息: 「{quoted_text}」]\n{user_input}"
        else:
            user_input = f"[引用消息: 「{quoted_text}」]\n请针对上面这条引用消息进行回复"

    # 空消息（只@机器人没说话且没引用）-> 发送帮助菜单
    if not user_input:
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
        await ai_chat.finish(help_text)

    # 忽略命令消息
    if user_input.startswith("/"):
        return

    # 违禁词检测 -> 拍一拍 + 好感度-10
    if _check_banned(user_input):
        try:
            from awesome_bot.plugins.affinity import change_favor
            change_favor(event.get_user_id(), -10, "违禁词")
        except Exception:
            pass
        await _poke_user(bot, event)
        return

    # 检查当前提供商的 API Key
    if AI_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        await ai_chat.finish("⚠️ 未配置 DEEPSEEK_API_KEY，请联系管理员")
    if AI_PROVIDER == "doubao" and not ARK_API_KEY:
        await ai_chat.finish("⚠️ 未配置 ARK_API_KEY，请联系管理员")

    user_id = event.get_user_id()

    # 好感度: 用 BERT 情感分析自动调整
    try:
        from awesome_bot.plugins.affinity import change_favor, check_favor_by_sentiment
        delta = await check_favor_by_sentiment(user_input)
        if delta != 0:
            change_favor(user_id, delta, "情感分析")
    except Exception:
        pass

    # 检查历史是否过期
    now = time.time()
    if user_id in chat_timestamps and now - chat_timestamps[user_id] > HISTORY_EXPIRE:
        chat_histories[user_id].clear()
    chat_timestamps[user_id] = now

    # 检查是否达到上下文上限
    history = chat_histories[user_id]
    current_rounds = len(history) // 2
    if current_rounds >= MAX_HISTORY:
        await ai_chat.send(
            f"📝 当前对话已达 {MAX_HISTORY} 轮上限，已自动清除早期记录。\n"
            f"发送 /清空上下文 可完全重置对话"
        )

    reply = await call_ai_api(user_id, user_input)
    await ai_chat.finish(reply)


def _extract_reply_text(event: MessageEvent) -> str:
    """提取回复/引用消息中的文本内容"""
    for seg in event.message:
        if seg.type == "reply":
            # reply 段本身不包含文本，但我们可以通过 event.reply 获取
            if hasattr(event, "reply") and event.reply:
                return event.reply.message.extract_plain_text().strip()
    return ""


# ============== 手动命令方式触发 ==============
chat_cmd = on_command("chat", aliases={"聊天", "问", "ai"}, priority=10, block=True)


@chat_cmd.handle()
async def handle_chat_cmd(bot: Bot, event: MessageEvent, args: Message = CommandArg()):
    user_input = args.extract_plain_text().strip()

    if not user_input:
        await chat_cmd.finish("请输入你想问的内容，例如: /chat 今天天气怎么样")

    # 违禁词检测 -> 拍一拍
    if _check_banned(user_input):
        await _poke_user(bot, event)
        return

    if AI_PROVIDER == "deepseek" and not DEEPSEEK_API_KEY:
        await chat_cmd.finish("⚠️ 未配置 DEEPSEEK_API_KEY")
    if AI_PROVIDER == "doubao" and not ARK_API_KEY:
        await chat_cmd.finish("⚠️ 未配置 ARK_API_KEY")

    user_id = event.get_user_id()

    now = time.time()
    if user_id in chat_timestamps and now - chat_timestamps[user_id] > HISTORY_EXPIRE:
        chat_histories[user_id].clear()
    chat_timestamps[user_id] = now

    reply = await call_ai_api(user_id, user_input)
    await chat_cmd.finish(reply)


# ============== 清除对话历史 ==============
clear_cmd = on_command("clear", aliases={"清空上下文", "清除记忆", "重置对话", "新对话"}, priority=10, block=True)


@clear_cmd.handle()
async def handle_clear(event: MessageEvent):
    user_id = event.get_user_id()
    history = chat_histories[user_id]
    rounds = len(history) // 2
    history.clear()
    chat_timestamps.pop(user_id, None)
    if rounds > 0:
        await clear_cmd.finish(
            f"🧹 已清除 {rounds} 轮对话记录（上限 {MAX_HISTORY} 轮）\n"
            f"可以开始新的话题啦！"
        )
    else:
        await clear_cmd.finish("🧹 当前没有对话记录，无需清除~")


# ============== AI API 调用（统一入口）==============
async def call_ai_api(user_id: str, user_input: str) -> str:
    """根据当前 AI_PROVIDER 调用对应的 API"""
    if AI_PROVIDER == "deepseek":
        return await call_deepseek_api(user_id, user_input)
    elif AI_PROVIDER == "doubao":
        return await call_doubao_api(user_id, user_input)
    else:
        return f"⚠️ 未知的 AI 提供商: {AI_PROVIDER}"


def _save_history(user_id: str, user_input: str, reply: str):
    """保存对话历史"""
    history = chat_histories[user_id]
    history.append({"role": "user", "content": user_input})
    history.append({"role": "assistant", "content": reply})
    if len(history) > MAX_HISTORY * 2:
        chat_histories[user_id] = history[-(MAX_HISTORY * 2):]


def _build_messages(user_id: str, user_input: str) -> list[dict]:
    """构建包含历史上下文的消息列表（合并自定义 Prompt + 好感度语气）"""
    # 合并默认 prompt 和用户自定义 prompt
    prompt = SYSTEM_PROMPT
    user_prompt = custom_prompts.get(user_id)
    if user_prompt:
        prompt = f"{SYSTEM_PROMPT}\n\n用户自定义设定: {user_prompt}"

    # 好感度语气融合
    try:
        from awesome_bot.plugins.affinity import get_favor_tone
        tone = get_favor_tone(user_id)
        prompt += f"\n\n语气要求: {tone}"
    except Exception:
        pass

    # 追加字数限制指令
    prompt += f"\n请将每次回复控制在{MAX_RESPONSE_LENGTH}字以内。"
    messages = [{"role": "system", "content": prompt}]
    messages.extend(chat_histories[user_id])
    messages.append({"role": "user", "content": user_input})
    return messages


# ============== DeepSeek API ==============
async def call_deepseek_api(user_id: str, user_input: str) -> str:
    """调用 DeepSeek API 进行对话"""
    try:
        messages = _build_messages(user_id, user_input)

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 1024,
                },
            )
            response.raise_for_status()
            data = response.json()

        reply = data["choices"][0]["message"]["content"]
        # 截断超长回复
        if len(reply) > MAX_RESPONSE_LENGTH:
            reply = reply[:MAX_RESPONSE_LENGTH] + "..."
        _save_history(user_id, user_input, reply)
        return reply

    except httpx.TimeoutException:
        return "⚠️ AI 响应超时了，请稍后再试~"
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "401" in error_msg:
            return "⚠️ DeepSeek API 密钥无效，请检查 DEEPSEEK_API_KEY"
        elif "rate" in error_msg.lower() or "429" in error_msg:
            return "⚠️ 请求太频繁了，请稍后再试~"
        else:
            return f"⚠️ DeepSeek 回复出错: {error_msg}"


# ============== 豆包 API ==============
async def call_doubao_api(user_id: str, user_input: str) -> str:
    """调用豆包 API 进行对话"""
    try:
        from volcenginesdkarkruntime import Ark
        import asyncio

        client = Ark(api_key=ARK_API_KEY)
        messages = _build_messages(user_id, user_input)

        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(
            None,
            lambda: client.chat.completions.create(
                model=DOUBAO_MODEL,
                messages=messages,
            ),
        )

        reply = completion.choices[0].message.content
        # 截断超长回复
        if len(reply) > MAX_RESPONSE_LENGTH:
            reply = reply[:MAX_RESPONSE_LENGTH] + "..."
        _save_history(user_id, user_input, reply)
        return reply

    except ImportError:
        return "⚠️ 缺少豆包 SDK，请安装: pip install volcengine-python-sdk[ark]"
    except Exception as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "key" in error_msg.lower():
            return "⚠️ 豆包 API 密钥无效，请检查 ARK_API_KEY"
        elif "rate" in error_msg.lower() or "limit" in error_msg.lower():
            return "⚠️ 请求太频繁了，请稍后再试~"
        else:
            return f"⚠️ 豆包回复出错: {error_msg}"
