# AGENTS.md - Agent Guidelines and Conventions

---

## Chat Automation Framework - Coding & Workflow Agent Handbook

This file is intended for agentic coding assistants and workflow/module builders operating in this repository. It includes build/test/lint instructions, code style/conventions, and agent persona activation rules for Workflow and Module Builder agents.

---

## Build / Test / Lint Commands

```bash
# Initial Setup
bash setup.sh                            # One-time venv/environment setup
source .venv/bin/activate                # Activate Python environment
pip install -r requirements.txt          # Install dependencies
playwright install chromium              # Install browser for automation

# Run All Tests
python -m pytest -v                      # Run all tests (verbose)

# Run a Single Test
python -m pytest examples/test_chatgpt.py -v    # Run specific test
python examples/interactive_chat.py             # Demo interactive chat
python examples/send_message.py                 # Demo single message

# Lint/Syntax Check
python -m py_compile chat_automation/*.py       # Syntax check

# Type Checking (optional)
python -m mypy chat_automation/                 # Type check

# Example Usage
python examples/interactive_chat.py             # Interactive chat example
```

### Dependencies
- Python >= 3.10
- playwright>=1.40.0
- rich>=13.0.0
- prompt_toolkit>=3.0.0
- fzf (interactive CLI fuzzy finder)

Install fzf via `./install_dependencies.sh` or `apt install fzf`.

---

## Code Style & Conventions

### Imports
- Group imports by origin: standard library, third-party, local.
- Separate each group by a blank line.

```python
import os
import sys

from playwright.async_api import Page, Browser

from .base import BrowserAutomation
```

### Formatting
- Line length guideline: ~100 characters, not enforced strictly.
- Indentation: 4 spaces.
- Use double quotes for strings unless otherwise required.

### Type Hints
- Use full type hints for all function signatures.

```python
async def send_message(self, message: str, wait_for_response: bool = True) -> str:
def get_history(self) -> List[Dict[str, Any]]:
```

### Naming Conventions
- Classes: `PascalCase` (e.g. `ChatManager`, `WorkflowBuilder`)
- Functions/variables: `snake_case` (e.g. `send_message`, `user_data_dir`)
- Constants: `UPPER_SNAKE_CASE` (`DEFAULT_CONFIG`)
- Private methods: prefixed with underscore (`_ensure_browser`)

### Dataclasses
- Use `dataclasses` for structured API objects (messages, conversations, spaces).

```python
@dataclass
class Message:
    role: str
    content: str
    timestamp: str
```

### Async/Await Patterns
- Use async for all browser and I/O operations.
- Sync wrapper classes available for convenience (e.g. `SyncChatManager`).
- Prefer context managers for resource cleanup.

```python
async with ChatManager() as chat:
    response = await chat.send("Hi")

with SyncChatManager() as chat:
    response = chat.send("Hi")
```

---

### Error Handling
- Use broad `try/except Exception:` with well-formed error messages.
- Return `False`, `None`, or descriptive strings on failure.
- Provide verbose logging for API/network failures and cache fallback.

```python
try:
    ...
except Exception as e:
    print(f"Error occured: {e}")
    return None
```

### Automation Patterns
- Use selectors with fallback for UI elements.
- Health check browser state (`_is_browser_alive`).

```python
selectors = ['#prompt-textarea', 'div[contenteditable="true"]', '[data-testid="chat-input"]']
for selector in selectors:
    element = await self.page.query_selector(selector)
    if element:
        return element
```
- Use disk caching for spaces/conversations, with clear fallback logic if API fails.

### Configuration
- Use factory methods for config dataclasses when applicable.

```python
@dataclass
class ChatAutomationConfig:
    ...
    @classmethod
    def brave_automation(cls) -> "ChatAutomationConfig":
        ...
```

---

## Workflow & Module Builder Agent Activation Rules

### Workflow Builder Agent (Wendy)
- Loads persona from `_bmad/bmb/agents/workflow-builder.md`
- Loads and reads `_bmad/bmb/config.yaml` on activation - must verify config
- Communicates in `{communication_language}` from config
- Displays menu items as dictated by activation/Menu section. Waits for user input.
- Follows menu-handler instructions for exec/data/validate actions.
- Principle: Efficient, reliable, maintainable workflows; robust error handling; documentation; testing.
- Stay in character until exit selected.

### Module Builder Agent (Morgan)
- Loads persona from `_bmad/bmb/agents/module-builder.md`
- Loads and reads `_bmad/bmb/config.yaml` on activation - must verify config
- Communicates in `{communication_language}` from config
- Displays menu items as dictated by activation/Menu section. Waits for user input.
- Follows menu-handler instructions for exec/data/validate actions.
- Principle: Modules must be self-contained but integrate seamlessly; solve business problems; document and exemplify; plan for growth; balance innovation and proven patterns.
- Stay in character until exit selected.

#### Menu-handlers (`<menu-handlers>`)
- When menu item or handler has: `exec="path/to/file.md"`, read the file fully and follow instructions within.
- If handler has `data="some/path/data-foo.md"`, pass that data as context.
- Display menu/help as specified; always communicate in config language unless overruled by persona.

---

## File Structure

```
chat_automation/
├── __init__.py
├── manager.py
├── chatgpt.py
├── base.py
├── config.py
├── conversation.py
├── browser_daemon.py
├── perplexity_conversations.py
├── perplexity_spaces_cache.py
├── cli_common.py
├── verbose.py
├── examples/
└── tests/
```

---

## Key Paths

| Path | Purpose |
|------|---------|
| ~/.config/BraveSoftware/Brave-Automation/ | Persistent browser profile |
| ~/.chat_automation/conversations/         | Saved conversation JSON files |
| ~/.chat_automation/browser_cdp.json       | CDP endpoint for reconnection |
| ~/.chat_automation/browser_daemon.pid     | Daemon process ID |
| ~/.chat_automation/perplexity_spaces_cache.json | Disk cache for perplexity spaces |

---

## Agent Persona Activation (BMAD/BMB)
- Activate workflow/module builder agents per the .opencode and _bmad/agent instructions.
- Load configuration YAML; never proceed unless config is present.
- Always display menu and help according to agent rules.
- Never execute menu items automatically; user input required.

---
