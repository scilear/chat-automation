# ChatGPT Automation Architecture

## Overview

Lazy browser architecture that keeps ChatGPT open between conversations, with auto-restart on crash and conversation persistence.

## Key Components

### 1. **ChatManager** (Async)
Main class for managing persistent browser sessions.

**Features:**
- Lazy initialization (browser starts on first `send()`)
- Keeps browser open between calls
- Auto-restart if browser crashes
- Auto-saves conversations to JSON
- Handles login prompts

**Usage:**
```python
from chat_automation import ChatManager

chat = ChatManager()

# Browser starts automatically on first send
response = await chat.send("Hello!")

# Continue conversation (browser stays open)
response2 = await chat.send("Tell me more")

# Export conversation
filepath = await chat.export_conversation("chat.json")

# Close when done
await chat.close()
```

### 2. **SyncChatManager** (Sync)
Synchronous wrapper for simpler usage in notebooks/scripts.

**Usage:**
```python
from chat_automation import SyncChatManager

with SyncChatManager() as chat:
    response = chat.send("Hello!")
    print(response)
```

### 3. **Persistent Profile**
Uses `ChatAutomationConfig.brave_automation()` which saves:
- Login cookies (so you don't log in every time)
- ChatGPT preferences
- Session state

Profile location: `~/.config/BraveSoftware/Brave-Automation/`

### 4. **Conversation Storage**
Auto-saves to: `~/.chat_automation/conversations/`

Each conversation saved as JSON with:
- ID, title, timestamps
- Full message history
- Export/import support

## File Structure

```
chat_automation/
├── __init__.py          # Exports all classes
├── base.py             # BrowserAutomation base class
├── chatgpt.py          # ChatGPTAutomation (low-level)
├── manager.py          # ChatManager & SyncChatManager (high-level)
├── config.py           # Configuration classes
├── conversation.py     # Conversation utilities
└── examples/
    ├── interactive_chat.py   # Manager example
    └── ...
```

## API Levels

### Low-Level (Direct browser control)
```python
from chat_automation import ChatGPTAutomation, ChatAutomationConfig

config = ChatAutomationConfig.brave_automation()
async with ChatGPTAutomation(config) as chatgpt:
    await chatgpt.goto("https://chatgpt.com")
    response = await chatgpt.chat("Hello")
```

### High-Level (Managed sessions)
```python
from chat_automation import ChatManager

chat = ChatManager()
response = await chat.send("Hello")  # Browser auto-starts
```

## Error Handling

- **Browser crashes**: Auto-restarts on next send()
- **Login required**: Prompts user with 60s timeout
- **Detached elements**: Uses page-level fill (more robust)
- **Send button**: Retries 3 times before failing

## Next Steps / Improvements

1. **Rate limiting**: Add delays between messages
2. **Claude/Deepseek**: Add other chat providers
3. **Image support**: Handle file uploads
4. **Multi-conversation**: Manage multiple threads
5. **API server**: Optional FastAPI wrapper
