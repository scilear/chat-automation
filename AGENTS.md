# Agent Guidelines - Chat Automation

Browser automation framework for ChatGPT and other AI chat services with persistent sessions.

## Build / Test Commands

```bash
# Setup (run once)
bash setup.sh

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Run a single test
python -m pytest examples/test_chatgpt.py -v

# Python syntax check
python -m py_compile chat_automation/*.py

# Type checking (if mypy installed)
python -m mypy chat_automation/

# Run an example
python examples/interactive_chat.py
```

## Dependencies

### External Tools

| Tool | Purpose | Install |
|------|---------|---------|
| **fzf** | Interactive fuzzy finder for CLI menus | `./install_dependencies.sh` or `apt install fzf` |
| **Playwright** | Browser automation | `playwright install chromium` |

### Interactive Selectors

Use fzf for interactive selection in CLI tools:

```python
async def interactive_select(self, title: str, items: List, key_attr: str, multi: bool = True):
    """Interactive selector using fzf"""
    import subprocess
    
    lines = []
    for item in items:
        key = getattr(item, key_attr, '')
        display = getattr(item, "title", str(item))
        lines.append(f"{display}\t{key}")
    
    proc = subprocess.Popen(
        ["fzf", "--multi", "--header", title],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )
    stdout, _ = proc.communicate("\n".join(lines))
    # Parse selected items from stdout...
```

## Browser Daemon

Keep browser running for instant CLI connections:

```bash
python browser_daemon.py start   # Start daemon
python browser_daemon.py status  # Check status
python browser_daemon.py stop    # Stop daemon
```

## Code Style Guidelines

### Imports
Order in three groups separated by blank lines:
1. Standard library
2. Third-party
3. Local

```python
import asyncio
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from playwright.async_api import Page, Browser

from .base import BrowserAutomation
from .config import ChatAutomationConfig
```

### Type Hints
Use full type hints for all function signatures:

```python
async def send_message(self, message: str, wait_for_response: bool = True) -> str:
    ...

def get_history(self) -> List[Dict[str, Any]]:
    ...

async def find_textarea(self) -> Optional[PageElement]:
    ...
```

### Naming Conventions
- **Classes**: `PascalCase` (`ChatManager`, `ChatGPTAutomation`)
- **Functions/Variables**: `snake_case` (`send_message`, `user_data_dir`)
- **Constants**: `UPPER_SNAKE_CASE` (`DEFAULT_CONFIG`, `PID_FILE`)
- **Private methods**: Leading underscore (`_ensure_browser`, `_is_browser_alive`)

### Formatting
- Line length: ~100 characters (practical, not strict)
- Indentation: 4 spaces
- Use double quotes for strings

### Dataclasses for Structured Data

```python
@dataclass
class Message:
    role: str
    content: str
    timestamp: str

@dataclass
class Conversation:
    id: str
    title: str
    messages: List[Message]
    created_at: str
    updated_at: str
    url: Optional[str] = None
```

### Async/Await Patterns
- Async for all I/O and browser operations
- Provide sync wrapper (`SyncChatManager`) for convenience
- Use context managers for cleanup:

```python
async with ChatManager() as chat:
    response = await chat.send("Hello")

with SyncChatManager() as chat:
    response = chat.send("Hello")
```

### Error Handling
Use broad `try/except Exception` with meaningful messages. Return error strings or `False`/`None`:

```python
async def send_message(self, message: str, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            element = await self.find_textarea()
            if not element:
                print(f"Attempt {attempt + 1}: Could not find chat input!")
                await asyncio.sleep(2)
                continue
            await element.fill(message)
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
    return False
```

### Browser Automation Patterns

Multiple fallback selectors for UI elements:

```python
selectors = [
    '#prompt-textarea',
    'div[contenteditable="true"]',
    '[data-testid="chat-input"]',
]

for selector in selectors:
    element = await self.page.query_selector(selector)
    if element:
        return element
```

Health checks for browser state:

```python
async def _is_browser_alive(self) -> bool:
    try:
        await self._chatgpt.page.evaluate("1 + 1")
        return True
    except Exception as e:
        print(f"Browser check failed: {e}")
        return False
```

### Configuration
Use dataclass factory methods:

```python
@dataclass
class ChatAutomationConfig:
    headless: bool = False
    browser_type: str = "chromium"
    timeout: int = 30000
    user_data_dir: Optional[str] = None

    @classmethod
    def brave_automation(cls) -> "ChatAutomationConfig":
        automation_dir = os.path.expanduser("~/.config/BraveSoftware/Brave-Automation")
        return cls(
            headless=False,
            browser_type="chromium",
            browser_channel="brave",
            user_data_dir=automation_dir,
        )
```

## File Structure

```
chat_automation/
├── __init__.py              # Public API exports
├── base.py                  # Base BrowserAutomation class (CDP support)
├── chatgpt.py               # ChatGPT-specific implementation
├── manager.py               # ChatManager, SyncChatManager
├── config.py                # Configuration dataclasses
├── conversation.py          # Conversation management
├── browser_daemon.py        # Background browser daemon
└── examples/                # Usage examples
```

## API Overview

```python
# Async - high level
chat = ChatManager()
response = await chat.send("Hello")
await chat.close()

# Sync - simpler API
with SyncChatManager() as chat:
    response = chat.send("Hello")

# Low-level - direct browser control
config = ChatAutomationConfig.brave_automation()
async with ChatGPTAutomation(config) as chatgpt:
    await chatgpt.goto("https://chatgpt.com")
    response = await chatgpt.chat("Hello")
```

## Key Paths

| Path | Purpose |
|------|---------|
| `~/.config/BraveSoftware/Brave-Automation/` | Persistent browser profile |
| `~/.chat_automation/conversations/` | Saved conversation JSON files |
| `~/.chat_automation/browser_cdp.json` | CDP endpoint for reconnection |
| `~/.chat_automation/browser_daemon.pid` | Daemon process ID |
