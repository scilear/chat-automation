# AGENTS.md - Agent Guidelines and Conventions

---

## Chat Automation Framework - Coding Agent Handbook

This file provides build/test/lint instructions, code style conventions, and agent activation rules.

---

## Build / Test / Lint Commands

```bash
# Initial Setup
bash setup.sh                            # One-time venv/environment setup
source .venv/bin/activate                # Activate Python environment
pip install -r requirements.txt          # Install dependencies
playwright install chromium              # Install browser for automation

# Run All Tests
python -m pytest -v

# Run a Single Test
python -m pytest examples/test_chatgpt.py -v

# Example Usage
python examples/interactive_chat.py
python examples/send_message.py

# Lint/Syntax Check
python -m py_compile chat_automation/*.py
```

### Dependencies
- Python >= 3.10, playwright>=1.40.0, rich>=13.0.0, prompt_toolkit>=3.0.0
- fzf (install via `./install_dependencies.sh` or `apt install fzf`)

---

## Code Style & Conventions

### Imports
Group imports by origin: standard library, third-party, local. Separate groups with blank lines.

```python
import os
import sys
from typing import Optional, List, Dict, Any

from playwright.async_api import Page, Browser

from .base import BrowserAutomation
from .config import ChatAutomationConfig
```

### Formatting
- Line length: ~100 characters, Indentation: 4 spaces
- Use double quotes for strings unless otherwise required

### Type Hints
Use full type hints: `async def send_message(self, message: str) -> str:`

### Naming Conventions
- Classes: `PascalCase` (e.g., `ChatManager`)
- Functions/variables: `snake_case` (e.g., `send_message`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CONFIG`)
- Private methods: `_ensure_browser`

### Dataclasses
Use `dataclasses` for structured API objects.

```python
@dataclass
class Message:
    role: str
    content: str
    timestamp: str
```

### Async/Await
Use async for all browser/I/O. Prefer context managers.

```python
async with ChatManager() as chat:
    response = await chat.send("Hi")
```

### Error Handling
Use `try/except Exception:` with descriptive messages. Return `False`, `None`, or descriptive strings on failure.

```python
try:
    ...
except Exception as e:
    print(f"Error occurred: {e}")
    return None
```

### Automation Patterns
Use selectors with fallback for UI elements.

```python
selectors = ['#prompt-textarea', 'div[contenteditable="true"]', '[data-testid="chat-input"]']
for selector in selectors:
    element = await self.page.query_selector(selector)
    if element:
        return element
```

### Configuration
Use factory methods for config dataclasses.

```python
@dataclass
class ChatAutomationConfig:
    headless: bool = False
    @classmethod
    def brave_automation(cls) -> "ChatAutomationConfig":
        ...
```

---

## Workflow & Module Builder Agent Activation

### Workflow Builder Agent (Wendy)
1. Load persona from `_bmad/bmb/agents/workflow-builder.md`
2. Read `_bmad/bmb/config.yaml` - must verify config exists
3. Display menu, wait for user input
4. Follow menu-handler instructions (exec/data/validate actions)

### Module Builder Agent (Morgan)
1. Load persona from `_bmad/bmb/agents/module-builder.md`
2. Read `_bmad/bmb/config.yaml` - must verify config exists
3. Display menu, wait for user input
4. Follow menu-handler instructions

### Menu-handlers
- If handler has `exec="path/to/file.md"`, read file fully and follow instructions
- If handler has `data="path/data-foo.md"`, pass as context

---

## File Structure

```
chat_automation/
├── __init__.py    ├── manager.py       ├── chatgpt.py      ├── base.py
├── config.py      ├── conversation.py  ├── browser_daemon.py
├── perplexity*.py ├── cli_common.py    ├── verbose.py
├── examples/      └── tests/
```

## Key Paths
| Path | Purpose |
|------|---------|
| ~/.config/BraveSoftware/Brave-Automation/ | Persistent browser profile |
| ~/.chat_automation/conversations/ | Saved conversation JSON files |
| ~/.chat_automation/browser_cdp.json | CDP endpoint for reconnection |
| ~/.chat_automation/browser_daemon.pid | Daemon process ID |
