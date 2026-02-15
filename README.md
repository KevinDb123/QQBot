
# 🤖 NoneBot QQ 机器人

基于 [NoneBot2](https://nonebot.dev/) 框架的多功能 QQ 机器人，支持群聊互动、AI 对话、签到、提醒、热搜、词云等丰富插件。

---

## 📂 项目结构

```
Nonebot/
├── bot.py                # 机器人入口
├── pyproject.toml        # 项目配置
├── requirements.txt      # 依赖列表
├── awesome_bot/
│   ├── __init__.py
│   └── plugins/          # 插件目录
│       ├── affinity.py           # 好感度系统
│       ├── ai_chat.py            # AI 对话/模型切换
│       ├── daily_report.py       # 群聊日报（AI 总结）
│       ├── hello.py              # 打招呼
│       ├── help.py               # 帮助菜单
│       ├── hotsearch.py          # 微博/百度热搜
│       ├── luck.py               # 今日运势
│       ├── plus_one.py           # 自动+1
│       ├── poke.py               # 拍一拍
│       ├── remind.py             # 定时提醒
│       ├── sign.py               # 签到/排行榜
│       ├── status.py             # 运行状态
│       ├── tools.py              # 掷骰子
│       ├── translate.py          # AI 翻译
│       ├── welcome.py            # 入群欢迎/退群提示
│       ├── wordcloud_plugin.py   # 群聊词云
│       └── ...
├── data/
│   ├── favor_data.json           # 好感度数据
│   └── sign_data.json            # 签到数据
└── README.md
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
# 或 source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

### 2. 配置 QQ 协议端

需配合 OneBot V11 协议实现（如 [Lagrange.Core](https://github.com/LagrangeDev/Lagrange.Core)、[NapCatQQ](https://github.com/NapNeko/NapCatQQ) 等），将反向 WebSocket 地址设为：

```
ws://127.0.0.1:8080/onebot/v11/ws
```

### 3. 启动机器人

```bash
python bot.py
```

---

## 🧩 插件功能一览

| 功能         | 主要命令/触发词         | 简介 |
|--------------|------------------------|------|
| 打招呼       | /hello /hi /你好       | 问候机器人 |
| 帮助菜单     | /help /帮助 /菜单      | 查看功能列表 |
| AI 对话      | @机器人 /chat /模型 /切换ai | 支持多模型AI对话 |
| 群聊日报     | /report                | AI 总结群聊内容 |
| 热搜         | /hot /热搜 /hotsearch  | 微博/百度热搜 |
| 今日运势     | /luck /运势            | 查看今日运势 |
| 自动+1       | 连续3条相同消息        | 自动跟+1 |
| 拍一拍       | /poke /拍 @人 [次数]   | 拍一拍成员 |
| 定时提醒     | /remind /提醒          | 定时闹钟提醒 |
| 签到系统     | /sign /签到 /rank      | 每日签到/排行榜 |
| 状态查询     | /status /状态          | 查看机器人运行状态 |
| 掷骰子       | /roll /掷骰子          | 掷骰子小游戏 |
| AI 翻译      | /translate /翻译       | 多语言AI翻译 |
| 入群欢迎     | 新成员入群/退群        | 自动欢迎/提示 |
| 群聊词云     | /wordcloud /词云 /wc   | 群消息生成词云 |
| 好感度系统   | /favor /favorrank      | 互动提升好感度 |

---

## 📝 说明与注意事项

- Python 版本需 >= 3.9
- 需配合 OneBot V11 协议端（如 Lagrange.Core、NapCatQQ 等）
- AI/日报/翻译等部分功能需配置 API KEY（详见插件源码注释）
- 插件目录可自由扩展，按需增删
- 数据文件默认保存在 data/ 目录

---

## 📚 参考文档

- [NoneBot2 官方文档](https://nonebot.dev/docs/)
- [OneBot V11 适配器](https://onebot.adapters.nonebot.dev/)
- [Lagrange.Core](https://github.com/LagrangeDev/Lagrange.Core)
- [NapCatQQ](https://github.com/NapNeko/NapCatQQ)


## 🚀 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置

编辑 `.env` 文件：

```env
HOST=0.0.0.0
PORT=8080
SUPERUSERS=["你的QQ号"]        # 替换为你自己的 QQ 号
NICKNAME=["小助手", "bot"]       # 机器人昵称
COMMAND_START=["/", ""]           # 命令前缀
```

### 3. 配置 QQ 协议端

NoneBot2 需要配合 **OneBot V11 协议实现** 来连接 QQ。推荐使用以下方案之一：

| 方案 | 说明 |
|------|------|
| [Lagrange.Core](https://github.com/LagrangeDev/Lagrange.Core) | 基于 NTQQ 协议的实现（推荐） |
| [NapCatQQ](https://github.com/NapNeko/NapCatQQ) | 基于 NTQQ 的 OneBot 协议实现 |
| [LLOneBot](https://github.com/LLOneBot/LLOneBot) | NTQQ 的 OneBot 插件 |

配置协议端时，将 **反向 WebSocket** 地址设置为：
```
ws://127.0.0.1:8080/onebot/v11/ws
```

### 4. 运行机器人

```bash
python bot.py
```

或者使用 nb-cli：
```bash
nb run
```

## 📋 功能列表

| 命令 | 别名 | 说明 |
|------|------|------|
| `/你好` | `/hello`, `/hi` | 打招呼 |
| `/help` | `/帮助`, `/菜单` | 查看功能菜单 |
| `/echo <内容>` | - | 复读消息（内置插件） |
| `/天气 <城市>` | `/weather` | 查询天气（模拟数据） |
| `/time` | `/时间` | 查看当前时间 |
| `/roll [n]` | `/掷骰子` | 掷骰子（默认1-6） |
| `/猜数字` | `/guess` | 猜数字游戏（1-100） |
| `/猜 <数字>` | - | 在游戏中猜测数字 |
| `/笑话` | `/joke` | 随机讲一个笑话 |
| `/状态` | `/status` | 查看机器人运行状态 |

## 🔧 自定义开发

### 添加新插件

在 `awesome_bot/plugins/` 目录下创建新的 `.py` 文件即可。示例：

```python
from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent

my_cmd = on_command("我的命令", priority=10, block=True)

@my_cmd.handle()
async def handle(event: MessageEvent):
    await my_cmd.finish("这是我的自定义命令！")
```

### 接入真实天气 API

编辑 `awesome_bot/plugins/weather.py`，将 `get_mock_weather()` 函数替换为调用真实天气 API 的实现（如[和风天气](https://www.qweather.com/)）。

## 📝 注意事项

- Python 版本需要 >= 3.9
- `SUPERUSERS` 中请填写你自己的 QQ 号（管理员）
- 天气插件当前使用模拟数据，需要接入真实 API 才能获取准确天气
- 需要搭配 OneBot V11 协议端使用（如 Lagrange / NapCatQQ）

## 📚 参考文档
- [Napcat官方文档](https://napneko.github.io/)
- [NoneBot2 官方文档](https://nonebot.dev/docs/)
- [OneBot V11 适配器](https://onebot.adapters.nonebot.dev/)
- [NoneBot2 商店](https://nonebot.dev/store/plugins) - 更多第三方插件
=======
