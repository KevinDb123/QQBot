"""
好感度系统插件
- 每次互动自动变化好感度
- /favor - 查看对你的好感度
- /favorrank - 好感度排行榜
- 不同好感度等级影响机器人语气
"""
import json
import os
import asyncio
from functools import lru_cache

from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.log import logger

driver = get_driver()

# ============== BERT 情感分析 ==============
_sentiment_pipeline = None
_model_loading = False


def _get_sentiment_pipeline():
    """懒加载 BERT 情感分析模型（首次调用会下载模型）"""
    global _sentiment_pipeline, _model_loading
    if _sentiment_pipeline is not None:
        return _sentiment_pipeline
    if _model_loading:
        return None
    try:
        _model_loading = True
        from transformers import pipeline
        _model_name = "uer/roberta-base-finetuned-jd-binary-chinese"
        logger.info(f"正在加载情感分析模型 {_model_name} ...")
        _sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=_model_name,
            truncation=True,
            max_length=512,
        )
        logger.info("情感分析模型加载完成")
        return _sentiment_pipeline
    except Exception as e:
        logger.warning(f"情感分析模型加载失败: {e}")
        _model_loading = False
        return None


async def analyze_sentiment(text: str) -> tuple[str, float]:
    """分析文本情感，返回 (label, score)
    label: 'positive' / 'negative'
    score: 0.0 ~ 1.0 置信度
    """
    pipe = _get_sentiment_pipeline()
    if pipe is None:
        return "neutral", 0.5

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: pipe(text[:512])
        )
        raw_label = result[0]["label"].lower()
        score = result[0]["score"]
        # uer/roberta 模型输出 label: "positive (stars 4 and 5)" / "negative (stars 1, 2 and 3)"
        if "positive" in raw_label:
            label = "positive"
        elif "negative" in raw_label:
            label = "negative"
        else:
            label = raw_label
        return label, score
    except Exception as e:
        logger.warning(f"情感分析出错: {e}")
        return "neutral", 0.5


def sentiment_to_favor_delta(label: str, score: float) -> int:
    """将情感分析结果转换为好感度变化值"""
    if label == "positive":
        if score >= 0.95:
            return 5   # 非常积极
        elif score >= 0.85:
            return 3   # 比较积极
        elif score >= 0.7:
            return 2   # 积极
        else:
            return 1   # 轻微积极
    elif label == "negative":
        if score >= 0.95:
            return -5  # 非常消极
        elif score >= 0.85:
            return -3  # 比较消极
        elif score >= 0.7:
            return -2  # 消极
        else:
            return -1  # 轻微消极
    return 0  # 中性

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
FAVOR_FILE = os.path.join(DATA_DIR, "favor_data.json")

# 好感度等级定义（分数范围, 称号, 语气描述）
FAVOR_LEVELS = [
    (-100, -50, "仇敌 💀", "你用冷漠、嘲讽的语气回复，偶尔阴阳怪气，不太想搭理对方。"),
    (-50, -10, "厌恶 😤", "你有点不耐烦，回复简短且带有轻微不满。"),
    (-10, 10, "陌生人 😐", "你礼貌但冷淡，像对待刚认识的人。"),
    (10, 30, "认识 🙂", "你态度友好，愿意聊天但不算亲近。"),
    (30, 60, "朋友 😊", "你很热情友好，像好哥们/好姐妹一样聊天，偶尔开玩笑。"),
    (60, 80, "好友 🥰", "你非常亲密，会撒娇、用可爱的语气说话，很关心对方。"),
    (80, 100, "挚友 💖", "你把对方当最好的朋友，语气超级亲昵，无话不谈，偶尔说肉麻的话。"),
    (100, 999, "知己 ✨", "你视对方为灵魂知己，用最真诚温暖的方式交流，会表达深厚的感情。"),
]

# 好感度变化事件（特殊事件固定变化量）
FAVOR_EVENTS = {
    "sign": 2,          # 签到 +2
    "poke_me": -3,      # 拍机器人 -3
    "banned_word": -10,  # 说违禁词 -10
}


def _load_favor_data() -> dict:
    """加载好感度数据"""
    if os.path.exists(FAVOR_FILE):
        try:
            with open(FAVOR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def _save_favor_data(data: dict):
    """保存好感度数据"""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FAVOR_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# 新用户默认好感度
DEFAULT_FAVOR = 50


def get_favor(user_id: str) -> int:
    """获取用户好感度"""
    data = _load_favor_data()
    return data.get(user_id, {}).get("favor", DEFAULT_FAVOR)


def change_favor(user_id: str, delta: int, reason: str = "") -> int:
    """改变好感度，返回最新值"""
    data = _load_favor_data()
    if user_id not in data:
        data[user_id] = {"favor": DEFAULT_FAVOR}

    old = data[user_id]["favor"]
    new = max(-100, min(100, old + delta))  # 限制在 -100 ~ 100
    data[user_id]["favor"] = new
    _save_favor_data(data)
    return new


def get_favor_level(favor: int) -> tuple[str, str]:
    """根据好感度获取等级称号和语气描述"""
    for low, high, title, tone in FAVOR_LEVELS:
        if low <= favor < high:
            return title, tone
    return "知己 ✨", FAVOR_LEVELS[-1][3]


def get_favor_tone(user_id: str) -> str:
    """获取用户对应的语气描述（用于 AI system prompt）"""
    favor = get_favor(user_id)
    _, tone = get_favor_level(favor)
    return tone


def get_favor_bar(favor: int) -> str:
    """生成好感度进度条"""
    # -100 到 100 映射到 0-20
    normalized = (favor + 100) / 200
    filled = int(normalized * 20)
    bar = "█" * filled + "░" * (20 - filled)
    return bar


async def check_favor_by_sentiment(text: str) -> int:
    """用 BERT 情感分析判断好感度变化"""
    if len(text) < 2:
        return 0
    label, score = await analyze_sentiment(text)
    return sentiment_to_favor_delta(label, score)


# ============== 查询好感度 ==============
favor_cmd = on_command("favor", aliases={"好感度", "好感", "亲密度"}, priority=10, block=True)


@favor_cmd.handle()
async def handle_favor(event: MessageEvent):
    user_id = event.get_user_id()
    favor = get_favor(user_id)
    title, tone = get_favor_level(favor)
    bar = get_favor_bar(favor)

    # 根据好感度给出不同风格的回复
    if favor >= 60:
        flavor = "你对我超好的，我最喜欢你了！💕"
    elif favor >= 30:
        flavor = "我们关系挺好的，继续保持哦~"
    elif favor >= 10:
        flavor = "还行吧，多聊聊就更好了~"
    elif favor >= -10:
        flavor = "我们好像不太熟...多互动互动？"
    elif favor >= -50:
        flavor = "哼，你是不是做了什么让我不开心的事？"
    else:
        flavor = "...我不想跟你说话 💢"

    text = (
        f"💝 好感度查询\n"
        f"━━━━━━━━━━━━━━━\n"
        f"等级: {title}\n"
        f"好感度: {favor} / 100\n"
        f"[{bar}]\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💬 {flavor}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💡 AI情感分析自动调整好感度\n"
        f"   积极+1~5 | 消极-1~5 | 拍我-3 | 违禁-10"
    )
    await favor_cmd.finish(text)


# ============== 好感度排行 ==============
fav_rank_cmd = on_command("favorrank", aliases={"好感排行", "好感榜"}, priority=10, block=True)


@fav_rank_cmd.handle()
async def handle_favor_rank(event: MessageEvent):
    data = _load_favor_data()

    if not data:
        await fav_rank_cmd.finish("📊 还没有好感度数据~")

    sorted_users = sorted(
        [(uid, info.get("favor", 0)) for uid, info in data.items()],
        key=lambda x: x[1],
        reverse=True,
    )[:10]

    lines = ["💝 好感度排行榜 TOP10", "━━━━━━━━━━━━━━━"]
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, fav) in enumerate(sorted_users):
        medal = medals[i] if i < 3 else f" {i + 1}."
        title, _ = get_favor_level(fav)
        lines.append(f"{medal} {uid} | {title} | 💝{fav}")

    lines.append("━━━━━━━━━━━━━━━")
    await fav_rank_cmd.finish("\n".join(lines))
