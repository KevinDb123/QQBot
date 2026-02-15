"""
翻译插件 - 使用 AI 进行多语言翻译
- /translate <内容> - 自动检测语言并翻译
- /翻译 <内容>
"""
import os

import httpx
from nonebot import on_command, get_driver
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageEvent


driver = get_driver()

# 复用 ai_chat 的配置
_AI_PROVIDER = "doubao"
_ARK_API_KEY = ""
_DOUBAO_MODEL = "doubao-seed-2-0-mini-260215"
_DEEPSEEK_API_KEY = ""
_DEEPSEEK_MODEL = "deepseek-chat"

TRANSLATE_PROMPT = (
    "你是一个专业翻译助手。请翻译用户输入的文本。"
    "规则：\n"
    "1. 如果用户输入的是中文，翻译成英文\n"
    "2. 如果用户输入的是其他语言，翻译成中文\n"
    "3. 只输出翻译结果，不要加任何解释或前缀\n"
    "4. 保持原文的语气和格式"
)


@driver.on_startup
async def _load_translate_config():
    global _AI_PROVIDER, _ARK_API_KEY, _DOUBAO_MODEL, _DEEPSEEK_API_KEY, _DEEPSEEK_MODEL
    config = driver.config
    _AI_PROVIDER = getattr(config, "ai_provider", "") or _AI_PROVIDER
    _ARK_API_KEY = getattr(config, "ark_api_key", "") or os.environ.get("ARK_API_KEY", "")
    _DOUBAO_MODEL = getattr(config, "doubao_model", "") or _DOUBAO_MODEL
    _DEEPSEEK_API_KEY = getattr(config, "deepseek_api_key", "") or os.environ.get("DEEPSEEK_API_KEY", "")
    _DEEPSEEK_MODEL = getattr(config, "deepseek_model", "") or _DEEPSEEK_MODEL


async def _translate(text: str, target_lang: str = "") -> str:
    """调用 AI 进行翻译"""
    prompt = TRANSLATE_PROMPT
    if target_lang:
        prompt = f"你是一个专业翻译助手，请将以下内容翻译成{target_lang}。只输出翻译结果，不要加任何解释。"

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": text},
    ]

    if _AI_PROVIDER == "deepseek":
        return await _call_deepseek(messages)
    else:
        return await _call_doubao(messages)


async def _call_deepseek(messages: list[dict]) -> str:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.deepseek.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {_DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _DEEPSEEK_MODEL,
                    "messages": messages,
                    "temperature": 0.3,
                    "max_tokens": 1024,
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"⚠️ 翻译失败: {e}"


async def _call_doubao(messages: list[dict]) -> str:
    try:
        from volcenginesdkarkruntime import Ark
        import asyncio

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
    except ImportError:
        return "⚠️ 缺少豆包 SDK"
    except Exception as e:
        return f"⚠️ 翻译失败: {e}"


# ============== 翻译命令 ==============
translate_cmd = on_command("translate", aliases={"翻译", "tr"}, priority=10, block=True)


@translate_cmd.handle()
async def handle_translate(event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await translate_cmd.finish(
            "📝 翻译用法:\n"
            "  /translate <内容> - 自动翻译\n"
            "  /tren <内容> - 翻译成英文\n"
            "  /trja <内容> - 翻译成日文\n"
            "  /trko <内容> - 翻译成韩文"
        )

    await translate_cmd.send("🔄 翻译中...")
    result = await _translate(text)
    await translate_cmd.finish(f"📝 翻译结果:\n{result}")


# 指定语言翻译
tr_en = on_command("tren", aliases={"翻译英文", "英译"}, priority=10, block=True)
tr_ja = on_command("trja", aliases={"翻译日文", "日译"}, priority=10, block=True)
tr_ko = on_command("trko", aliases={"翻译韩文", "韩译"}, priority=10, block=True)


@tr_en.handle()
async def handle_tr_en(event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await tr_en.finish("请输入要翻译的内容，例如: /tren 你好世界")
    await tr_en.send("🔄 翻译中...")
    result = await _translate(text, "英文")
    await tr_en.finish(f"📝 → English:\n{result}")


@tr_ja.handle()
async def handle_tr_ja(event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await tr_ja.finish("请输入要翻译的内容，例如: /trja 你好世界")
    await tr_ja.send("🔄 翻译中...")
    result = await _translate(text, "日文")
    await tr_ja.finish(f"📝 → 日本語:\n{result}")


@tr_ko.handle()
async def handle_tr_ko(event: MessageEvent, args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await tr_ko.finish("请输入要翻译的内容，例如: /trko 你好世界")
    await tr_ko.send("🔄 翻译中...")
    result = await _translate(text, "韩文")
    await tr_ko.finish(f"📝 → 한국어:\n{result}")
