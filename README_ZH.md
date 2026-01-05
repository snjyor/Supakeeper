# 🛡️ Supakeeper

**保持你的 Supabase 项目活跃！** 防止免费版 Supabase 项目因不活动而被暂停。

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <a href="README.md">English</a> | <a href="README_ZH.md">中文</a>
</p>

## 📋 背景

Supabase 免费版项目如果 **7 天内没有任何活动**，会被自动暂停。Supakeeper 通过定期对你的 Supabase 项目执行轻量级操作来保持项目活跃，防止被暂停。

## ✨ 特性

- 🔄 **多项目支持** - 同时管理多个 Supabase 项目
- ⏰ **灵活调度** - 可配置的检查间隔（默认每48小时）
- 🔀 **并发处理** - 并行 ping 多个项目，提高效率
- 📝 **详细日志** - 文件和控制台日志，便于监控
- 🔔 **通知支持** - 支持 Telegram Bot / Discord / Slack 通知
- 🛡️ **多重策略** - 多种保活策略，确保可靠性
- 🔐 **安全配置** - 使用 .env 文件存储敏感凭据
- 🖥️ **CLI 工具** - 简洁的命令行界面

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/supakeeper.git
cd supakeeper

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或 .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 或使用 pip 安装为包
pip install -e .
```

### 配置

1. **复制配置文件**

```bash
cp env.example .env
```

2. **编辑 `.env` 文件**

```bash
# 单个项目
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_NAME=My Project

# 或多个项目
SUPABASE_URL_1=https://project1.supabase.co
SUPABASE_KEY_1=key1
SUPABASE_NAME_1=Project 1

SUPABASE_URL_2=https://project2.supabase.co
SUPABASE_KEY_2=key2
SUPABASE_NAME_2=Project 2
```

3. **获取 Supabase 凭据**

   - 登录 [Supabase Dashboard](https://supabase.com/dashboard)
   - 选择你的项目
   - 进入 Settings → API
   - 复制 `Project URL` 和 `anon` key

### 使用

```bash
# 运行一次
python main.py

# 守护进程模式
python main.py --daemon
```

## 📁 项目结构

```
supakeeper/
├── src/supakeeper/
│   ├── __init__.py     # 包入口
│   ├── cli.py          # 命令行界面
│   ├── config.py       # 配置管理
│   ├── keeper.py       # 核心保活逻辑
│   ├── logger.py       # 日志系统
│   ├── notifier.py     # 通知系统
│   └── scheduler.py    # 调度器
├── tests/              # 测试文件
├── logs/               # 日志文件
├── env.example         # 配置示例
├── main.py             # 直接运行入口
├── pyproject.toml      # 项目配置
└── requirements.txt    # 依赖列表
```

## ⚙️ 配置选项

所有配置通过 `.env` 文件或环境变量设置：

### 单个项目

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_NAME=My Project          # 可选，默认 "Default Project"
SUPABASE_TABLE=my_table           # 可选，指定查询的表
```

### 多个项目

```bash
# Project 1
SUPABASE_URL_1=https://project1.supabase.co
SUPABASE_KEY_1=key1
SUPABASE_NAME_1=Project One

# Project 2
SUPABASE_URL_2=https://project2.supabase.co
SUPABASE_KEY_2=key2
SUPABASE_NAME_2=Project Two

# Project 3, 4, 5... 以此类推
```

### 调度和日志设置

```bash
# 检查间隔（小时），Supabase 7天暂停，48小时是安全值
KEEPALIVE_INTERVAL_HOURS=48

# 失败重试次数
RETRY_ATTEMPTS=3

# 重试延迟（秒）
RETRY_DELAY=30

# 日志级别: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# 日志文件路径
LOG_FILE=logs/supakeeper.log

# 控制台输出
CONSOLE_OUTPUT=true
```

### 通知设置

```bash
# Telegram Bot 通知（推荐）
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Webhook 通知 URL（Discord, Slack 等）
WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
```

## 🔧 部署方式

### 1. 本地 Cron Job

```bash
# 编辑 crontab
crontab -e

# 每天运行两次（0:00 和 12:00）
0 0,12 * * * cd /path/to/supakeeper && /path/to/venv/bin/python main.py >> /path/to/supakeeper/logs/cron.log 2>&1
```

### 2. Docker

```bash
# 使用 docker-compose（推荐）
docker-compose up -d

# 或手动构建运行
docker build -t supakeeper .
docker run -d --name supakeeper --env-file .env supakeeper
```

### 3. GitHub Actions

本仓库已包含预配置的工作流文件 `.github/workflows/supakeeper.yml`。

**配置步骤：**

1. 进入 GitHub 仓库：`Settings → Environments → New environment`
2. 创建一个名为 **`SUPABASE KEY`** 的环境（必须与 workflow 中的 `environment` 名称一致）
3. 在此环境中添加 secrets：

| Secret 名称 | 说明 |
|------------|------|
| `SUPABASE_URL_1` | 项目 1 的 URL |
| `SUPABASE_KEY_1` | 项目 1 的 anon key |
| `SUPABASE_NAME_1` | 项目 1 的名称（可选） |
| `SUPABASE_URL_2` | 项目 2 的 URL |
| `SUPABASE_KEY_2` | 项目 2 的 anon key |
| ... | 最多支持 7 个项目 |
| `TELEGRAM_BOT_TOKEN` | Telegram Bot token（可选） |
| `TELEGRAM_CHAT_ID` | Telegram Chat ID（可选） |
| `WEBHOOK_URL` | Discord/Slack webhook（可选） |

> ⚠️ **重要提示**：环境名称 `SUPABASE KEY` 必须与 workflow 文件中的 `environment:` 字段完全一致。你可以使用其他名称，但两处必须保持一致。

### 4. 云函数 (AWS Lambda / Vercel / Cloudflare Workers)

可以轻松适配到各种 Serverless 平台，只需调用核心函数：

```python
from supakeeper import SupaKeeper, Config

def handler(event, context):
    config = Config.load()
    keeper = SupaKeeper(config)
    success, failed = keeper.run_once()
    return {"success": success, "failed": failed}
```

## 🔔 通知配置

### Telegram Bot（推荐）

**步骤 1: 创建机器人**
1. 在 Telegram 中找到 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 创建新机器人
3. 复制获得的 Bot Token（格式: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`）

**步骤 2: 获取 Chat ID**

> ⚠️ `chat_id` 是你与机器人对话的 ID，不是机器人的用户名！

1. 在 Telegram 中搜索你刚创建的机器人
2. **向机器人发送任意消息**（如 `/start` 或 `hello`）
3. 在浏览器中访问：
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. 在返回的 JSON 中找到 `chat` 对象：
   ```json
   "chat":{"id":123456789,"first_name":"Your Name"...}
   ```
5. 这个 `id`（如 `123456789`）就是你的 `TELEGRAM_CHAT_ID`

**步骤 3: 配置 `.env`**

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

> 💡 如果要发送到群组，先把机器人加入群组并在群组中发送消息，然后用同样方法获取群组的 chat_id（通常是负数）

参考: [Telegram Bot API - sendMessage](https://core.telegram.org/bots/api#sendmessage)

### Discord Webhook

1. 在 Discord 服务器中创建 Webhook
2. 复制 Webhook URL
3. 在 `.env` 中设置：

```bash
WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
```

### Slack Webhook

同样支持 Slack Incoming Webhooks。

> 💡 你可以同时配置 Telegram 和 Webhook，两个通知渠道会同时发送。

## 🧪 测试

```bash
# 安装测试依赖
pip install pytest pytest-asyncio pytest-cov

# 运行测试
pytest

# 带覆盖率
pytest --cov=supakeeper
```

## 📊 保活策略

Supakeeper 使用多重策略确保项目活跃：

1. **表查询** - 如果配置了特定表（SUPABASE_TABLE），查询该表
2. **Auth 用户表查询** - 查询 `auth.users` 表
3. **Auth 会话检查** - 检查认证会话状态
4. **REST API Ping** - 直接请求 PostgREST API

任何一种策略成功即表示项目活跃。

## ⚠️ 注意事项

- 免费版 Supabase 项目 **7 天**无活动会被暂停
- 建议设置检查间隔为 **48-72 小时**
- 暂停后 **90 天内**可以恢复项目
- 使用 `anon` key 即可，无需 `service_role` key
- `.env` 文件包含敏感信息，请勿提交到版本控制

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**⭐ 如果这个项目对你有帮助，请给个 Star！**
