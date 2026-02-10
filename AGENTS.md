# Agent Guidelines - Chat Automation

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

# Verify installation
python -c "from chat_automation import SyncChatManager; print('Ready')"

# Run a simple example
python examples/interactive_chat.py

# Python syntax check
python -m py_compile chat_automation/*.py

# Type checking (if mypy installed)
python -m mypy chat_automation/

# Run single test (if pytest installed)
python -m pytest examples/test_chatgpt.py -v
```

## Code Style Guidelines

### Imports
Order imports in three groups separated by blank lines:
1. Standard library (`import asyncio`, `from typing import Optional`)
2. Third-party (`from playwright.async_api import async_api`)
3. Local (`from .config import ChatAutomationConfig`)

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
Use full type hints for function signatures. Prefer specific types over `Any`.

```python
async def send_message(self, message: str, wait_for_response: bool = True) -> str:
    ...

def get_history(self) -> List[Dict[str, Any]]:
    ...

# Optional for nullable returns
async def find_textarea(self) -> Optional[PageElement]:
    ...
```

### Naming Conventions
- **Classes**: `PascalCase` (`ChatManager`, `ChatGPTAutomation`)
- **Functions/Variables**: `snake_case` (`send_message`, `user_data_dir`)
- **Constants**: `UPPER_SNAKE_CASE` or simple `snake_case` (`DEFAULT_CONFIG`)
- **Private methods**: Leading underscore (`_ensure_browser`, `_is_browser_alive`)
- **Dataclass fields**: `snake_case` (`role`, `content`, `timestamp`)

### Formatting
- Line length: ~100 characters (practical, not strict)
- Indentation: 4 spaces
- Use dataclasses for structured data:

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
- Provide sync wrapper for convenience (`SyncChatManager`)
- Use context managers for cleanup:

```python
async with ChatManager() as chat:
    response = await chat.send("Hello")

# Or sync version
with SyncChatManager() as chat:
    response = chat.send("Hello")
```

### Error Handling
- Use broad `try/except Exception` with meaningful error messages
- Print errors to stdout, return error strings or `False`/`None`
- Implement retry logic for transient failures:

```python
async def send_message(self, message: str, max_retries: int = 3) -> bool:
    for attempt in range(max_retries):
        try:
            # ... operation
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3)
    return False
```

### Browser Automation Patterns
- Multiple fallback selectors for UI elements:

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

- Health checks for browser state:

```python
async def _is_browser_alive(self) -> bool:
    try:
        await self._chatgpt.page.evaluate("1 + 1")
        return True
    except Exception as e:
        print(f"Browser check failed: {e}")
        return False
```

### File Structure
```
chat_automation/
├── __init__.py              # Public API exports
├── base.py                  # Base BrowserAutomation class
├── chatgpt.py               # ChatGPT-specific implementation
├── manager.py               # ChatManager, SyncChatManager
├── config.py                # Configuration dataclasses
├── conversation.py          # Conversation management
└── examples/                # Usage examples
```

### Module Docstrings
Each module should have a docstring at the top:

```python
"""
ChatGPT-specific automation module.

Provides async browser automation for ChatGPT web interface.
"""
```

### Configuration
Use dataclass builders for configuration:

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

## Quick Reference

```python
# Async
chat = ChatManager()
response = await chat.send("Hello")
await chat.close()

# Sync
with SyncChatManager() as chat:
    response = chat.send("Hello")

# Low-level
config = ChatAutomationConfig.brave_automation()
async with ChatGPTAutomation(config) as chatgpt:
    await chatgpt.goto("https://chatgpt.com")
```
