"""
群聊词云插件
- 自动记录群聊消息
- /wordcloud - 生成当前群聊的词云图片
- /wc - 简写命令
"""
import io
import base64
import time
from collections import defaultdict

from nonebot import on_command, on_message
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
    MessageSegment,
)


# 群消息存储 {group_id: [(timestamp, user_id, text), ...]}
group_messages: dict[int, list[tuple[float, str, str]]] = defaultdict(list)

# 最多保留的消息数
MAX_MESSAGES = 2000
# 消息过期时间（24小时）
MESSAGE_EXPIRE = 24 * 3600

# 停用词（不统计的常见词）
STOP_WORDS = {
    "的", "了", "是", "在", "我", "有", "和", "就", "不", "人", "都",
    "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你",
    "会", "着", "没有", "看", "好", "自己", "这", "他", "她", "它",
    "吗", "吧", "呢", "啊", "哦", "嗯", "呀", "哈", "嘿", "哎",
    "那", "什么", "怎么", "可以", "这个", "那个", "还是", "但是",
    "因为", "所以", "如果", "已经", "或者", "只是", "而且", "不是",
    "没", "被", "把", "让", "给", "对", "从", "比", "为", "与",
}


# ============== 消息记录（静默监听）==============
msg_recorder = on_message(priority=999, block=False)


@msg_recorder.handle()
async def record_message(event: GroupMessageEvent):
    """记录群消息用于词云和日报"""
    text = event.get_plaintext().strip()
    if not text or text.startswith("/"):
        return

    group_id = event.group_id
    user_id = event.get_user_id()
    now = time.time()

    # 添加消息 (时间戳, 用户ID, 文本)
    group_messages[group_id].append((now, user_id, text))

    # 清理过期消息
    cutoff = now - MESSAGE_EXPIRE
    group_messages[group_id] = [
        (t, uid, msg) for t, uid, msg in group_messages[group_id]
        if t > cutoff
    ][-MAX_MESSAGES:]


# ============== 生成词云 ==============
wordcloud_cmd = on_command("wordcloud", aliases={"词云", "wc", "群词云"}, priority=10, block=True)


@wordcloud_cmd.handle()
async def handle_wordcloud(bot: Bot, event: GroupMessageEvent):
    group_id = event.group_id
    messages = group_messages.get(group_id, [])

    if len(messages) < 10:
        await wordcloud_cmd.finish(
            "📊 消息数量不足（至少需要10条）\n"
            "机器人会自动记录群消息，请稍后再试~"
        )

    await wordcloud_cmd.send("🔄 正在生成词云...")

    # 合并所有文本
    all_text = " ".join(msg for _, _, msg in messages)

    try:
        import jieba
    except ImportError:
        await wordcloud_cmd.finish("⚠️ 缺少 jieba 库，请安装: pip install jieba")

    try:
        from wordcloud import WordCloud
    except ImportError:
        await wordcloud_cmd.finish("⚠️ 缺少 wordcloud 库，请安装: pip install wordcloud")

    # 分词
    words = jieba.lcut(all_text)
    filtered = [w for w in words if len(w) >= 2 and w not in STOP_WORDS]

    if not filtered:
        await wordcloud_cmd.finish("📊 没有足够的有效词汇生成词云")

    # 统计词频
    from collections import Counter
    word_freq = Counter(filtered)

    # 生成词云
    try:
        # 尝试使用系统中文字体
        font_path = None
        import os
        font_candidates = [
            "C:/Windows/Fonts/msyh.ttc",   # 微软雅黑
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",  # 宋体
        ]
        for fp in font_candidates:
            if os.path.exists(fp):
                font_path = fp
                break

        wc = WordCloud(
            font_path=font_path,
            width=800,
            height=600,
            background_color="white",
            max_words=100,
            max_font_size=100,
            colormap="viridis",
        )
        wc.generate_from_frequencies(word_freq)

        # 输出为图片字节
        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format="PNG")
        img_bytes = img_buffer.getvalue()

        # 发送图片
        b64 = base64.b64encode(img_bytes).decode()
    except Exception as e:
        await wordcloud_cmd.finish(f"⚠️ 生成词云失败: {e}")

    await wordcloud_cmd.finish(
        MessageSegment.text(f"📊 群聊词云（基于{len(messages)}条消息）\n")
        + MessageSegment.image(f"base64://{b64}")
    )
