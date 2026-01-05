# 🛡️ Supakeeper

**Keep your Supabase projects alive!** Prevent free-tier Supabase projects from being paused due to inactivity.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <a href="README.md">English</a> | <a href="README_ZH.md">中文</a>
</p>

## 📋 Background

Supabase free-tier projects are **automatically paused after 7 days of inactivity**. Supakeeper keeps your projects active by periodically performing lightweight operations on your Supabase projects.

## ✨ Features

- 🔄 **Multi-project Support** - Manage multiple Supabase projects simultaneously
- ⏰ **Flexible Scheduling** - Configurable check interval (default: every 48 hours)
- 🔀 **Concurrent Processing** - Ping multiple projects in parallel for efficiency
- 📝 **Detailed Logging** - File and console logs for easy monitoring
- 🔔 **Notifications** - Support for Telegram Bot / Discord / Slack notifications
- 🛡️ **Multiple Strategies** - Various keep-alive strategies for reliability
- 🔐 **Secure Configuration** - Store sensitive credentials in .env file
- 🖥️ **CLI Tool** - Clean command-line interface

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/supakeeper.git
cd supakeeper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Or install as a package
pip install -e .
```

### Configuration

1. **Copy the configuration file**

```bash
cp env.example .env
```

2. **Edit the `.env` file**

```bash
# Single project
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
SUPABASE_NAME=My Project

# Or multiple projects
SUPABASE_URL_1=https://project1.supabase.co
SUPABASE_KEY_1=key1
SUPABASE_NAME_1=Project 1

SUPABASE_URL_2=https://project2.supabase.co
SUPABASE_KEY_2=key2
SUPABASE_NAME_2=Project 2
```

3. **Get Supabase Credentials**

   - Log in to [Supabase Dashboard](https://supabase.com/dashboard)
   - Select your project
   - Go to Settings → API
   - Copy `Project URL` and `anon` key

### Usage

```bash
# Run once
python main.py

# Daemon mode
python main.py --daemon
```

## 📁 Project Structure

```
supakeeper/
├── src/supakeeper/
│   ├── __init__.py     # Package entry
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration management
│   ├── keeper.py       # Core keep-alive logic
│   ├── logger.py       # Logging system
│   ├── notifier.py     # Notification system
│   └── scheduler.py    # Scheduler
├── tests/              # Test files
├── logs/               # Log files
├── env.example         # Configuration example
├── main.py             # Direct run entry
├── pyproject.toml      # Project configuration
└── requirements.txt    # Dependencies
```

## ⚙️ Configuration Options

All configuration is done via `.env` file or environment variables:

### Single Project

```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_NAME=My Project          # Optional, defaults to "Default Project"
SUPABASE_TABLE=my_table           # Optional, specific table to query
```

### Multiple Projects

```bash
# Project 1
SUPABASE_URL_1=https://project1.supabase.co
SUPABASE_KEY_1=key1
SUPABASE_NAME_1=Project One

# Project 2
SUPABASE_URL_2=https://project2.supabase.co
SUPABASE_KEY_2=key2
SUPABASE_NAME_2=Project Two
SUPABASE_TABLE_2=my_table

# Project 3, 4, 5... and so on
```

### Scheduling and Logging Settings

```bash
# Check interval (hours), Supabase pauses after 7 days, 48 hours is safe
KEEPALIVE_INTERVAL_HOURS=48

# Number of retry attempts
RETRY_ATTEMPTS=3

# Retry delay (seconds)
RETRY_DELAY=30

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Log file path
LOG_FILE=logs/supakeeper.log

# Console output
CONSOLE_OUTPUT=true
```

### Notification Settings

```bash
# Telegram Bot notifications (recommended)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789

# Webhook URL for notifications (Discord, Slack, etc.)
WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
```

## 🔧 Deployment

### 1. Local Cron Job

```bash
# Edit crontab
crontab -e

# Run twice daily (00:00 and 12:00)
0 0,12 * * * cd /path/to/supakeeper && /path/to/venv/bin/python main.py >> /path/to/supakeeper/logs/cron.log 2>&1
```

### 2. Docker

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t supakeeper .
docker run -d --name supakeeper --env-file .env supakeeper
```

### 3. GitHub Actions

Create `.github/workflows/supakeeper.yml`:

```yaml
name: Supakeeper

on:
  schedule:
    - cron: '0 0 * * 0,3'  # Run every Sunday and Wednesday
  workflow_dispatch:  # Allow manual trigger

jobs:
  keepalive:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Supakeeper
        env:
          SUPABASE_URL_1: ${{ secrets.SUPABASE_URL_1 }}
          SUPABASE_KEY_1: ${{ secrets.SUPABASE_KEY_1 }}
          # ... add more as needed
        run: python main.py
```

### 4. Serverless (AWS Lambda / Vercel / Cloudflare Workers)

Easily adapt to various serverless platforms by calling the core function:

```python
from supakeeper import SupaKeeper, Config

def handler(event, context):
    config = Config.load()
    keeper = SupaKeeper(config)
    success, failed = keeper.run_once()
    return {"success": success, "failed": failed}
```

## 🔔 Notification Configuration

### Telegram Bot (Recommended)

**Step 1: Create a Bot**
1. Find [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` to create a new bot
3. Copy the Bot Token (format: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

**Step 2: Get Chat ID**

> ⚠️ `chat_id` is the ID of your conversation with the bot, not the bot's username!

1. Search for your newly created bot on Telegram
2. **Send any message to the bot** (e.g., `/start` or `hello`)
3. Visit in your browser:
   ```
   https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
   ```
4. Find the `chat` object in the returned JSON:
   ```json
   "chat":{"id":123456789,"first_name":"Your Name"...}
   ```
5. This `id` (e.g., `123456789`) is your `TELEGRAM_CHAT_ID`

**Step 3: Configure `.env`**

```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

> 💡 To send to a group, add the bot to the group, send a message in the group, then use the same method to get the group's chat_id (usually a negative number)

Reference: [Telegram Bot API - sendMessage](https://core.telegram.org/bots/api#sendmessage)

### Discord Webhook

1. Create a Webhook in your Discord server
2. Copy the Webhook URL
3. Set in `.env`:

```bash
WEBHOOK_URL=https://discord.com/api/webhooks/xxx/yyy
```

### Slack Webhook

Also supports Slack Incoming Webhooks.

> 💡 You can configure both Telegram and Webhook simultaneously - both notification channels will send.

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests
pytest

# With coverage
pytest --cov=supakeeper
```

## 📊 Keep-Alive Strategies

Supakeeper uses multiple strategies to ensure projects stay active:

1. **Table Query** - If a specific table is configured (SUPABASE_TABLE), query that table
2. **Auth Users Query** - Query the `auth.users` table
3. **Auth Session Check** - Check authentication session status
4. **REST API Ping** - Direct request to PostgREST API

Any successful strategy indicates the project is active.

## ⚠️ Notes

- Free-tier Supabase projects pause after **7 days** of inactivity
- Recommended check interval: **48-72 hours**
- Projects can be restored within **90 days** after pausing
- Use `anon` key only, no need for `service_role` key
- `.env` file contains sensitive information - do not commit to version control

## 📄 License

MIT License - See [LICENSE](LICENSE)

## 🤝 Contributing

Issues and Pull Requests are welcome!

---

**⭐ If this project helps you, please give it a Star!**

