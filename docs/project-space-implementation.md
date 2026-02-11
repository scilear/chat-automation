# Project/Space Management - Implementation Plan

## Summary

Add CLI commands to list and manage projects/spaces and their conversations for both ChatGPT and Perplexity.

## Research Complete

DOM structure documented in `docs/ui-selectors.md`

---

## Phase 1: Core Methods

### 1.1 ChatGPT (`chatgpt.py`)

```python
async def get_projects(self) -> list[dict]:
    """List all projects"""
    # Navigate to home if needed
    # Select: a[href*="/g/g-p-"]
    # Return: [{id, name, url}, ...]

async def get_project_conversations(self, project_id: str) -> list[dict]:
    """List conversations in a project"""
    # Navigate to project URL
    # Select: a[href*="/c/"]
    # Return: [{id, title, url}, ...]

async def get_all_conversations(self) -> list[dict]:
    """List all conversations (with project info)"""
    # Get conversations from sidebar
    # Determine which project they belong to
    # Return: [{id, title, url, project_id}, ...]

async def delete_conversation(self, conv_id: str) -> bool:
    """Delete a conversation"""
    # Find conversation in sidebar
    # Hover to reveal delete button
    # Click delete, confirm
    # Return: success
```

### 1.2 Perplexity (`perplexity.py`)

```python
async def get_spaces(self) -> list[dict]:
    """List all spaces"""
    # Navigate to /spaces
    # Select: a[href^="/spaces/"]
    # Return: [{id, name, url, privacy}, ...]

async def get_space_threads(self, space_id: str) -> list[dict]:
    """List threads in a space"""
    # Navigate to space URL
    # Scroll to load threads
    # Select: a[href*="/search/"]
    # Return: [{id, title, url}, ...]

async def delete_thread(self, thread_id: str) -> bool:
    """Delete a thread"""
    # Similar to ChatGPT
```

---

## Phase 2: CLI Commands

### 2.1 ChatGPT CLI (`chatgpt`)

```bash
# Projects
./chatgpt projects list                    # List all projects
./chatgpt projects show <project-id>       # Show conversations in project

# Conversations
./chatgpt conversations list               # List all conversations
./chatgpt conversations list --project X   # Filter by project
./chatgpt conversations resume <id>        # Resume a conversation
./chatgpt conversations delete <id>        # Delete a conversation
./chatgpt conversations delete <id1> <id2> # Delete multiple
```

### 2.2 Perplexity CLI (`perplexity`)

```bash
# Spaces
./perplexity spaces list                   # List all spaces
./perplexity spaces show <space-id>        # Show threads in space

# Threads
./perplexity threads list                  # List all threads
./perplexity threads list --space X        # Filter by space
./perplexity threads resume <id>           # Resume a thread
./perplexity threads delete <id>           # Delete a thread
```

---

## Phase 3: Output Formats

### Default (Human-readable)
```
$ ./chatgpt projects list
PROJECT                    CONVS   UPDATED
Wendy                      12      2h ago
Finance Coding             5       1d ago
CapitalMarkets             8       3d ago
(No project)               45      5m ago

$ ./chatgpt conversations list
ID           TITLE                        PROJECT       UPDATED
698c9002...  Put Ratio Spread Strategy     Wendy         2h ago
698c568d...  Funniest Joke Request         (none)        1h ago
```

### JSON Output (`--json`)
```json
{
  "projects": [
    {
      "id": "6978779fe4d08191af15240af4d87671",
      "name": "Wendy",
      "url": "https://chatgpt.com/g/g-p-6978779fe4d08191af15240af4d87671-wendy/project",
      "conversation_count": 12
    }
  ]
}
```

---

## Phase 4: Delete Operations

### Safety Measures
- Single delete: Confirm with `--force` or prompt
- Bulk delete (>5): Require `--force` flag
- Preview mode: `--dry-run` shows what would be deleted

```bash
# Delete single (prompts for confirmation)
./chatgpt conversations delete 698c9002-5048-838a-86f9-30aeca853c79

# Delete multiple (requires --force)
./chatgpt conversations delete id1 id2 id3 --force

# Preview deletion
./chatgpt conversations delete --project wendy --older-than 30d --dry-run
```

---

## Implementation Order

1. **get_projects()** - ChatGPT
2. **get_spaces()** - Perplexity
3. **get_all_conversations()** - ChatGPT
4. **get_space_threads()** - Perplexity
5. **CLI: list commands** - Both
6. **CLI: resume command** - Both
7. **delete_conversation()** - ChatGPT
8. **delete_thread()** - Perplexity
9. **CLI: delete commands** - Both

---

## Estimated Effort

| Task | Time |
|------|------|
| Core methods (ChatGPT) | 2h |
| Core methods (Perplexity) | 1h |
| CLI commands | 2h |
| Delete operations | 2h |
| Testing & polish | 1h |
| **Total** | **8h** |

---

## Files to Modify

| File | Additions |
|------|-----------|
| `chatgpt.py` | ~100 lines (project/conv methods) |
| `perplexity.py` | ~80 lines (space/thread methods) |
| `chatgpt` (CLI) | ~150 lines (subcommands) |
| `perplexity` (CLI) | ~120 lines (subcommands) |
| `manager.py` | ~30 lines (project filtering) |
