# UI Selectors for Project/Space Management

## ChatGPT Projects

### Projects List
- **Location**: Sidebar, under "Projects" heading
- **Projects button**: `button` with text "Projects"
- **Project links**: `a[href*="/g/g-p-"]` with `data-sidebar-item="true"`
- **URL pattern**: `/g/g-p-{id}-{name}/project`
- **Example**: `https://chatgpt.com/g/g-p-6978779fe4d08191af15240af4d87671-wendy/project`

### Conversations in Project
- **Selector**: `a[href*="/c/"]`
- **URL pattern**: `/c/{uuid}`
- **Example**: `https://chatgpt.com/c/698c9002-5048-838a-86f9-30aeca853c79`
- **Note**: Conversations show "Your chats" section in sidebar when viewing project

### All Conversations (No Project)
- **Location**: Sidebar under "Your chats" section
- **Same selector**: `a[href*="/c/"]`

### DOM Structure
```html
<nav>
  <h2>Projects</h2>
  <a data-sidebar-item="true" href="/g/g-p-{id}-{name}/project">ProjectName</a>
  
  <h2>Your chats</h2>
  <a href="/c/{uuid}">ConversationTitle</a>
</nav>
```

---

## Perplexity Spaces

### Spaces List
- **Page**: `/spaces`
- **Selector**: `a[href^="/spaces/"]` (excluding `/spaces/templates`)
- **URL pattern**: `/spaces/{name}-{id}`
- **Example**: `https://www.perplexity.ai/spaces/wendy-VI.ac6xOQiSCAKVfSzWwfA`
- **Class**: `block`

### Threads in Space
- **Selector**: `a[href*="/search/"]`
- **URL pattern**: `/search/{title}-{id}`
- **Example**: `https://www.perplexity.ai/search/wendy-issues-jgkUf3c1SZK8P4UluNf8Tw`
- **Note**: Requires scrolling to trigger lazy loading

### Thread Data
- Each thread link contains title as innerText
- First ~50 chars of thread content may be visible

### DOM Structure
```html
<a href="/spaces/{name}-{id}" class="block">
  {SpaceName}
  {Date}
  {Private|Shared}
</a>

<!-- Inside space page, after scroll -->
<a href="/search/{title}-{id}">
  {ThreadTitle}
  {Preview text}
</a>
```

---

## Delete Operations

### ChatGPT
- **Delete button**: Appears on hover over conversation item
- **Selector**: Look for trash icon or "Delete" button near `a[href*="/c/"]`
- **Confirmation**: Usually a modal dialog

### Perplexity
- **Delete button**: Likely similar hover behavior
- **Needs further investigation**: Test on actual thread item

---

## ID Extraction Patterns

### ChatGPT
```python
# Project ID from URL
url = "https://chatgpt.com/g/g-p-6978779fe4d08191af15240af4d87671-wendy/project"
project_id = url.split("/g/g-p-")[1].split("-")[0]  # 6978779fe4d08191af15240af4d87671

# Conversation ID from URL
url = "https://chatgpt.com/c/698c9002-5048-838a-86f9-30aeca853c79"
conv_id = url.split("/c/")[1]  # 698c9002-5048-838a-86f9-30aeca853c79
```

### Perplexity
```python
# Space ID from URL
url = "https://www.perplexity.ai/spaces/wendy-VI.ac6xOQiSCAKVfSzWwfA"
space_id = url.split("/spaces/")[1]  # wendy-VI.ac6xOQiSCAKVfSzWwfA

# Thread ID from URL
url = "https://www.perplexity.ai/search/wendy-issues-jgkUf3c1SZK8P4UluNf8Tw"
thread_id = url.split("/search/")[1]  # wendy-issues-jgkUf3c1SZK8P4UluNf8Tw
```
