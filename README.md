# Chat Automation Framework

**Long-running browser automation for ChatGPT and other AI chat services.**

Keep the browser open between conversations, auto-save chats, and recover from crashes automatically.

## Quick Start

```bash
# 1. Navigate to directory
cd chat_automation

# 2. Run setup (creates isolated virtual environment)
bash setup.sh

# 3. Activate environment
source .venv/bin/activate

# 4. Try it
python -c "from chat_automation import SyncChatManager; print('Ready!')"
```

## First-Time Usage

### 1. Simple Example (Sync)

```python
from chat_automation import SyncChatManager

# Browser opens, login if needed, then chat
with SyncChatManager() as chat:
    response = chat.send("What is Python?")
    print(response)
```

### 2. Multi-Message Conversation (Async)

```python
import asyncio
from chat_automation import ChatManager

async def main():
    chat = ChatManager()
    chat.start_conversation("Learning Python")
    
    # Browser stays open - no restart between messages
    r1 = await chat.send("What is Python?")
    r2 = await chat.send("Show me an example")
    r3 = await chat.send("What are its main features?")
    
    # Export conversation
    filepath = await chat.export_conversation("python_chat.json")
    print(f"Saved to: {filepath}")
    
    await chat.close()

asyncio.run(main())
```

## Key Features

- **Persistent Browser** - Stays open between `send()` calls (no restart overhead)
- **Auto-Restart** - Recovers from crashes automatically
- **Cookie Persistence** - Login once, use indefinitely
- **Conversation Export** - Auto-saves to JSON with full history
- **Multiple Conversations** - Manage different chat threads
- **Sync & Async APIs** - Use what fits your workflow

## Documentation

| File | Purpose |
|------|---------|
| `AGENTS.md` | **Agent guidelines** - How to use this framework |
| `USAGE.md` | **Detailed examples** - Common patterns and workflows |
| `ARCHITECTURE.md` | **Technical docs** - Architecture overview |

## API Overview

### High-Level: ChatManager

```python
from chat_automation import ChatManager, SyncChatManager

# Async version
chat = ChatManager()
response = await chat.send("Hello")
await chat.close()

# Sync version (simpler)
with SyncChatManager() as chat:
    response = chat.send("Hello")
```

### Low-Level: Direct Browser Control

```python
from chat_automation import ChatGPTAutomation, ChatAutomationConfig

config = ChatAutomationConfig.brave_automation()
async with ChatGPTAutomation(config) as chatgpt:
    await chatgpt.goto("https://chatgpt.com")
    response = await chatgpt.chat("Hello")
```

## Examples

See `examples/` directory:

```bash
# Interactive chat example
python examples/interactive_chat.py

# Send a single message
python examples/send_message.py

# List and export conversations
python examples/list_conversations.py
python examples/export_all.py
```

## Configuration

### Default (Persistent Profile)

```python
from chat_automation import ChatManager

# Uses ~/.config/BraveSoftware/Brave-Automation/
# Login cookies persist between runs
chat = ChatManager()
```

### Custom Settings

```python
from chat_automation import ChatManager, ChatAutomationConfig

config = ChatAutomationConfig.brave_automation()
config.headless = True  # No visible browser
config.timeout = 60000  # 60 second timeout

chat = ChatManager(config=config)
```

## File Structure

```
chat_automation/
├── .venv/                      # Isolated Python environment
├── setup.sh                    # One-time setup script
├── requirements.txt            # Dependencies
├── pyproject.toml             # Package config
├── AGENTS.md                  # Agent guidelines
├── USAGE.md                   # Detailed examples
├── ARCHITECTURE.md            # Technical architecture
├── README.md                  # This file
├── chat_automation/           # Source code
│   ├── __init__.py
│   ├── manager.py            # ChatManager (main interface)
│   ├── chatgpt.py            # ChatGPT automation
│   ├── base.py               # Browser base class
│   ├── config.py             # Configuration
│   ├── conversation.py       # Conversation utilities
│   └── examples/             # Example scripts
└── ~/.chat_automation/       # Runtime data
    └── conversations/        # Saved chats (auto-created)
```

## Troubleshooting

### First Run - Login Required

On first run, you'll see:
```
Please log in to ChatGPT manually in the browser window
Waiting for login...
```

Simply log in to ChatGPT in the browser window that opens. After that, cookies are saved.

### "Browser check failed"

The browser crashed. Next `send()` will auto-restart it.

### Stale Lock Files

If you get lock file errors:
```bash
rm -f ~/.config/BraveSoftware/Brave-Automation/SingletonLock
```

## Dependencies

- **playwright** - Browser automation
- **chromium** - Installed by setup.sh via `playwright install chromium`
- **brave** - System browser (for persistent profile storage)

All dependencies are isolated in `.venv/` - no conflicts with other projects.

## License

MIT
