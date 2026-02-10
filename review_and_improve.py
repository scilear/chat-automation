#!/usr/bin/env python3
"""
Interactive code improvement session
Uses ChatGPT to review and suggest improvements
"""

import asyncio
import sys
sys.path.insert(0, '/home/fabien/clawd')

from chat_automation import ChatManager

# Files to review in order of importance
FILES_TO_REVIEW = [
    ('manager.py', '/home/fabien/clawd/chat_automation/manager.py', 'Core ChatManager class - manages browser sessions'),
    ('base.py', '/home/fabien/clawd/chat_automation/base.py', 'Base browser automation class'),
    ('chatgpt.py', '/home/fabien/clawd/chat_automation/chatgpt.py', 'ChatGPT-specific automation'),
    ('config.py', '/home/fabien/clawd/chat_automation/config.py', 'Configuration classes'),
]

async def interactive_review():
    chat = ChatManager()
    
    try:
        print("=" * 80)
        print("CODE IMPROVEMENT SESSION")
        print("=" * 80)
        
        # Start conversation
        chat.start_conversation("Code Review - Improvements")
        
        # Initial request
        print("\n1. Setting up code review context...")
        intro = """I'm working on a Python browser automation framework using Playwright. 

The framework provides:
- Long-running browser sessions (persistent between messages)
- Auto-restart on crashes
- Conversation history tracking
- Both async and sync APIs

I'll share the files one by one. For each file, please:
1. Identify critical bugs or security issues
2. Suggest specific improvements with code examples
3. Point out Python best practices I'm missing

Let's start!"""
        
        await chat.send(intro, wait_for_response=True)
        print("✓ Context established\n")
        
        improvements = {}
        
        # Review each file
        for filename, filepath, description in FILES_TO_REVIEW:
            print(f"\n{'='*80}")
            print(f"REVIEWING: {filename}")
            print(f"Description: {description}")
            print('='*80)
            
            # Read file
            with open(filepath, 'r') as f:
                code = f.read()
            
            # Send for review
            message = f"""Please review this file: {filename}

Context: {description}

```python
{code}
```

Please provide:
1. CRITICAL issues (bugs, security risks) - must fix
2. MAJOR improvements (architecture, error handling) - should fix  
3. MINOR suggestions (style, best practices) - nice to have

For each issue, include:
- Line number(s)
- Current code
- Suggested fix with code
- Brief explanation of why"""
            
            print(f"Sending {filename} for review...")
            response = await chat.send(message, wait_for_response=True)
            
            print(f"\n✓ Review received ({len(response)} characters)")
            print("\n" + "-"*80)
            print("FEEDBACK:")
            print("-"*80)
            print(response)
            print("-"*80)
            
            improvements[filename] = response
            
            # Save progress
            await chat.export_conversation('/home/fabien/clawd/chat_automation/improvement_session.json')
            
            print("\n✓ Progress saved")
            print("\n" + "="*80)
        
        # Get overall recommendations
        print("\n\n2. Getting overall recommendations...")
        summary_request = """Based on all the files reviewed, provide:

PRIORITY 1 - Fix Immediately (Critical bugs/security):
- List the top 3 most critical issues

PRIORITY 2 - Should Fix (Major improvements):
- List 3-5 important improvements

PRIORITY 3 - Nice to Have (Minor enhancements):
- List minor suggestions

REFACTORING ROADMAP:
What order should I tackle these improvements in?"""
        
        summary = await chat.send(summary_request, wait_for_response=True)
        
        print("\n" + "="*80)
        print("OVERALL RECOMMENDATIONS")
        print("="*80)
        print(summary)
        
        # Save final
        await chat.export_conversation('/home/fabien/clawd/chat_automation/improvement_session_complete.json')
        
        print("\n" + "="*80)
        print("REVIEW COMPLETE")
        print("="*80)
        print(f"\nReviewed {len(FILES_TO_REVIEW)} files")
        print(f"Total messages: {len(chat.get_history())}")
        
        if chat._current_conversation and chat._current_conversation.url:
            print(f"\nConversation URL: {chat._current_conversation.url}")
        
        print("\nNow I'll implement the improvements...")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted. Saving...")
        await chat.export_conversation('/home/fabien/clawd/chat_automation/improvement_session.json')
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nClosing browser...")
        await chat.close()
        print("Done!")

if __name__ == "__main__":
    print("Starting Interactive Code Improvement Session")
    print("This will review all files and collect improvement suggestions\n")
    
    asyncio.run(interactive_review())
