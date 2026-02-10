# Chat Automation - Usage Guide

Complete examples for using the ChatGPT automation framework.

## Table of Contents

1. [Basic Usage](#basic-usage)
2. [Long-Running Sessions](#long-running-sessions)
3. [Conversation Management](#conversation-management)
4. [Advanced Patterns](#advanced-patterns)
5. [Error Handling](#error-handling)
6. [Integration Examples](#integration-examples)

## Basic Usage

### Quick Start (Sync)

```python
from chat_automation import SyncChatManager

# Simple conversation
with SyncChatManager() as chat:
    response = chat.send("What is machine learning?")
    print(response)
```

### Quick Start (Async)

```python
import asyncio
from chat_automation import ChatManager

async def main():
    chat = ChatManager()
    try:
        response = await chat.send("Explain neural networks")
        print(response)
    finally:
        await chat.close()

asyncio.run(main())
```

## Long-Running Sessions

### Multi-Hour Research Session

```python
import asyncio
from chat_automation import ChatManager

async def research_session():
    """Example: Long-running research session over hours"""
    chat = ChatManager()
    chat.start_conversation("AI Research Project")
    
    try:
        # Phase 1: Initial research
        print("=== Phase 1: Understanding the topic ===")
        r1 = await chat.send("What are transformers in AI?")
        
        # Phase 2: Deep dive (minutes or hours later)
        print("\n=== Phase 2: Technical details ===")
        r2 = await chat.send("How does the attention mechanism work specifically?")
        
        # Phase 3: Application (hours later, same browser session)
        print("\n=== Phase 3: Practical application ===")
        r3 = await chat.send("Show me a simple transformer implementation in Python")
        
        # Export complete conversation
        filepath = await chat.export_conversation("transformer_research.json")
        print(f"\nSaved to: {filepath}")
        
    finally:
        await chat.close()

asyncio.run(research_session())
```

### Interactive Q&A Loop

```python
from chat_automation import SyncChatManager

def interactive_chat():
    """Interactive terminal chat with ChatGPT"""
    with SyncChatManager() as chat:
        chat.start_conversation("Interactive Session")
        
        print("ChatGPT Interactive Mode (type 'quit' to exit)")
        print("=" * 50)
        
        while True:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                break
            
            if not user_input:
                continue
            
            response = chat.send(user_input)
            print(f"\nChatGPT: {response}")
        
        # Export at the end
        chat.export_conversation("interactive_session.json")
        print("\nConversation saved!")

if __name__ == "__main__":
    interactive_chat()
```

## Conversation Management

### Managing Multiple Topics

```python
import asyncio
from chat_automation import ChatManager

async def multi_topic_chat():
    """Manage multiple conversation threads"""
    chat = ChatManager()
    
    try:
        # Topic 1: Python
        print("=== Topic 1: Python ===")
        chat.start_conversation("Python Learning")
        await chat.send("What are Python decorators?")
        await chat.send("Show me an example")
        
        # Save Python conversation
        python_conv = await chat.export_conversation("python_learning.json")
        
        # Topic 2: JavaScript (new chat)
        print("\n=== Topic 2: JavaScript ===")
        await chat.new_chat()  # Clears browser thread
        chat.start_conversation("JavaScript Async")
        await chat.send("Explain Promises in JavaScript")
        await chat.send("How do they compare to Python async/await?")
        
        # Save JS conversation
        js_conv = await chat.export_conversation("javascript_async.json")
        
        # List all saved conversations
        print("\n=== Saved Conversations ===")
        saved = await chat.list_saved_conversations()
        for i, path in enumerate(saved, 1):
            print(f"{i}. {path}")
            
    finally:
        await chat.close()

asyncio.run(multi_topic_chat())
```

### Loading and Continuing Previous Conversations

```python
import asyncio
from chat_automation import ChatManager

async def continue_conversation():
    """Resume a previous conversation"""
    chat = ChatManager()
    
    try:
        # List available conversations
        saved = await chat.list_saved_conversations()
        
        if not saved:
            print("No saved conversations found")
            return
        
        print("Available conversations:")
        for i, path in enumerate(saved, 1):
            print(f"{i}. {path}")
        
        # Load the most recent one
        print(f"\nLoading: {saved[0]}")
        await chat.load_conversation(saved[0])
        
        # Show history
        history = chat.get_history()
        print(f"\nLoaded {len(history)} messages")
        for msg in history[-3:]:  # Show last 3
            role = "You" if msg['role'] == 'user' else "ChatGPT"
            print(f"{role}: {msg['content'][:50]}...")
        
        # Continue conversation
        print("\n=== Continuing conversation ===")
        response = await chat.send("Can you expand on that last point?")
        print(f"\nChatGPT: {response}")
        
    finally:
        await chat.close()

asyncio.run(continue_conversation())
```

## Advanced Patterns

### Batch Processing Questions

```python
import asyncio
from chat_automation import ChatManager

async def batch_questions():
    """Process multiple questions with rate limiting"""
    questions = [
        "What is Docker?",
        "What is Kubernetes?",
        "What is the difference between them?",
        "When should I use each?",
    ]
    
    chat = ChatManager()
    chat.start_conversation("Container Orchestration")
    
    try:
        responses = []
        
        for i, question in enumerate(questions, 1):
            print(f"Processing question {i}/{len(questions)}: {question}")
            
            response = await chat.send(question)
            responses.append({
                'question': question,
                'answer': response
            })
            
            # Rate limiting - be nice to ChatGPT
            if i < len(questions):
                print("  Waiting 3 seconds...")
                await asyncio.sleep(3)
        
        # Export all responses
        import json
        with open('batch_responses.json', 'w') as f:
            json.dump(responses, f, indent=2)
        
        print(f"\nProcessed {len(responses)} questions")
        
    finally:
        await chat.close()

asyncio.run(batch_questions())
```

### Custom Configuration

```python
from chat_automation import ChatManager, ChatAutomationConfig

# Custom configuration
def create_custom_chat():
    config = ChatAutomationConfig.brave_automation()
    
    # Use headless mode (no visible browser)
    config.headless = True
    
    # Custom profile directory
    config.user_data_dir = "/path/to/custom/profile"
    
    # Longer timeout for slow connections
    config.timeout = 60000  # 60 seconds
    
    return ChatManager(config=config)

# Usage
async def main():
    chat = create_custom_chat()
    # ... use chat
```

### Error Recovery Loop

```python
import asyncio
from chat_automation import ChatManager

async def resilient_chat():
    """Continue even if errors occur"""
    chat = ChatManager()
    
    try:
        questions = [
            "Question 1",
            "Question 2 (might fail)",
            "Question 3",
        ]
        
        for question in questions:
            try:
                print(f"Asking: {question}")
                response = await chat.send(question)
                print(f"Success: {response[:100]}...")
            except Exception as e:
                print(f"Failed: {e}")
                print("Continuing with next question...")
                continue
            
            await asyncio.sleep(2)
        
    finally:
        await chat.close()

asyncio.run(resilient_chat())
```

## Error Handling

### Handling Login Prompts

```python
import asyncio
from chat_automation import ChatManager

async def with_login_handling():
    """First time setup - handle login"""
    chat = ChatManager()
    
    try:
        # If not logged in, this will prompt:
        # "Please log in to ChatGPT manually in the browser window"
        response = await chat.send("Hello")
        print(response)
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nTip: Make sure you're logged into ChatGPT in the browser")
        
    finally:
        await chat.close()

asyncio.run(with_login_handling())
```

### Browser Crash Recovery

```python
import asyncio
from chat_automation import ChatManager

async def crash_recovery_demo():
    """Demonstrates auto-restart on crash"""
    chat = ChatManager()
    
    try:
        # Normal operation
        r1 = await chat.send("Message 1")
        print("Message 1 sent")
        
        # Simulate crash by killing browser process manually
        # Or just wait - if it crashes, next send() recovers
        
        # This will auto-restart if browser crashed
        r2 = await chat.send("Message 2 (auto-recovery if needed)")
        print("Message 2 sent")
        
    finally:
        await chat.close()
```

## Integration Examples

### Jupyter Notebook

```python
# In a Jupyter cell
from chat_automation import SyncChatManager

# Create chat instance (persists across cells)
chat = SyncChatManager().__enter__()
chat.start_conversation("Notebook Session")
```

```python
# In another cell
response = chat.send("What is the capital of France?")
print(response)
```

```python
# When done
chat.__exit__(None, None, None)
```

### CLI Tool

```python
#!/usr/bin/env python3
"""CLI tool for ChatGPT automation"""

import argparse
import asyncio
from chat_automation import SyncChatManager

def main():
    parser = argparse.ArgumentParser(description='ChatGPT CLI')
    parser.add_argument('message', help='Message to send')
    parser.add_argument('--conversation', '-c', help='Conversation title')
    parser.add_argument('--export', '-e', help='Export to file')
    
    args = parser.parse_args()
    
    with SyncChatManager() as chat:
        if args.conversation:
            chat.start_conversation(args.conversation)
        
        response = chat.send(args.message)
        print(response)
        
        if args.export:
            chat.export_conversation(args.export)
            print(f"Saved to {args.export}")

if __name__ == "__main__":
    main()
```

Usage:
```bash
python cli.py "What is Python?" -c "Learning" -e "python_basics.json"
```

### Web Scraping Integration

```python
import asyncio
from chat_automation import ChatManager

async def analyze_webpage():
    """Fetch webpage, summarize with ChatGPT"""
    import requests
    from bs4 import BeautifulSoup
    
    # Fetch article
    url = "https://example.com/article"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    article_text = soup.get_text()[:2000]  # First 2000 chars
    
    # Summarize with ChatGPT
    chat = ChatManager()
    try:
        prompt = f"Summarize this article in 3 bullet points:\n\n{article_text}"
        summary = await chat.send(prompt)
        print(summary)
    finally:
        await chat.close()

asyncio.run(analyze_webpage())
```

## Best Practices

1. **Always use context managers** when possible
2. **Export important conversations** - auto-save happens but explicit is safer
3. **Add rate limiting** for batch operations
4. **Handle login once** - cookies persist in the profile
5. **Check for errors** in production code
6. **Use meaningful conversation titles** for organization

## Common Patterns

### Research Workflow

```python
# 1. Start research session
chat.start_conversation("Research: Topic X")

# 2. Ask initial questions
await chat.send("Give me an overview of Topic X")

# 3. Drill down
await chat.send("Explain the key concepts")

# 4. Get practical examples
await chat.send("Show me code examples")

# 5. Export
await chat.export_conversation("research_topic_x.json")
```

### Code Review

```python
# Review code with ChatGPT
code = """
def my_function():
    pass
"""

response = chat.send(f"Review this code:\n```python\n{code}\n```")
```

### Learning Path

```python
# Structured learning over multiple sessions
learning_plan = [
    "What is {topic}?",
    "What are the prerequisites?",
    "Give me a step-by-step learning path",
    "What are common mistakes?",
    "Show me a simple project",
]

for question_template in learning_plan:
    question = question_template.format(topic="Machine Learning")
    response = chat.send(question)
    print(f"Q: {question}\nA: {response}\n")
```
