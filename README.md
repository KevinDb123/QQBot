# 🤖 NoneBot QQ 机器人

基于 [NoneBot2](https://nonebot.dev/) 框架的 QQ 机器人项目。

## 📂 项目结构

```
Nonebot/
├── bot.py                          # 机器人入口文件
├── .env                            # 环境变量配置
├── .env.prod                       # 生产环境配置
├── pyproject.toml                  # 项目配置
├── requirements.txt                # Python 依赖
└── awesome_bot/
    └── plugins/                    # 插件目录
        ├── hello.py                # 打招呼插件
        ├── help.py                 # 帮助菜单插件
        ├── weather.py              # 天气查询插件（模拟数据）
        ├── tools.py                # 实用工具（时间、骰子）
        ├── guess_number.py         # 猜数字游戏
        ├── joke.py                 # 随机笑话
        └── status.py               # 机器人状态查看
```

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

- [NoneBot2 官方文档](https://nonebot.dev/docs/)
- [OneBot V11 适配器](https://onebot.adapters.nonebot.dev/)
- [NoneBot2 商店](https://nonebot.dev/store/plugins) - 更多第三方插件
