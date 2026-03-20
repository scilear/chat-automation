#!/usr/bin/env python3
"""
Complete code review process - uses conversation URL to resume

Usage:
    python do_code_review.py [conversation_url_or_id]

If conversation_url_or_id provided, resumes that conversation.
Otherwise starts fresh.
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/fabien/clawd')

from chat_automation import ChatManager

# Get code files to review
def get_file_content(filename, filepath):
    """Read and truncate file if needed"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Truncate very long files
        if len(content) > 6000:
            print(f"  Note: {filename} is {len(content)} chars, truncating to 6000")
            content = content[:6000] + "\n\n[...truncated for length...]"
        
        return content
    except Exception as e:
        print(f"  Error reading {filename}: {e}")
        return None

async def full_code_review(conversation_url=None):
    chat = ChatManager()
    
    try:
        # Step 1: Setup - either resume or start fresh
        print("=" * 70)
        print("STEP 1: Setting up code review")
        print("=" * 70)
        
        if conversation_url:
            # Resume existing conversation
            print(f"Resuming conversation: {conversation_url}")
            success = await chat.open_conversation_by_url(conversation_url)
            if not success:
                print("Failed to open conversation, starting fresh")
                conversation_url = None
        
        if not conversation_url:
            # Start fresh - first get the review prompt
            print("Starting fresh code review...")
            print("First, we need a code review prompt from the AI")
            print("\nSending: Create a comprehensive code review prompt...")
            
            prompt_request = """I'm working on a Python browser automation project using Playwright. Could you create a practical code review checklist for me?

I'd like you to focus on these areas:
- Common security pitfalls in browser automation
- Proper error handling and resource cleanup
- Async/await best practices
- Efficient element selection strategies
- Reliability improvements (retries, waits)

Keep it practical and actionable so I can use it to review my own code."""
            
            chat.start_conversation("Code Review Session")
            review_prompt = await chat.send(prompt_request, wait_for_response=True)
            
            print("\n✓ Got review prompt")
            print(f"Length: {len(review_prompt)} chars")
            print("\nPrompt preview:")
            print("-" * 70)
            print(review_prompt[:500] + "..." if len(review_prompt) > 500 else review_prompt)
            print("-" * 70)
            
            # Store the prompt for later use
            review_guidelines = review_prompt
        else:
            # We resumed, check what we already have
            history = chat.get_history()
            print(f"Resumed conversation with {len(history)} messages")
            review_guidelines = "Use the review guidelines already established in this conversation"
        
        # Step 2: Review files one by one
        print("\n" + "=" * 70)
        print("STEP 2: Reviewing files")
        print("=" * 70)
        
        files_to_review = [
            ('config.py', '/home/fabien/clawd/chat_automation/config.py'),
            ('base.py', '/home/fabien/clawd/chat_automation/base.py'),
            ('chatgpt.py', '/home/fabien/clawd/chat_automation/chatgpt.py'),
            ('manager.py', '/home/fabien/clawd/chat_automation/manager.py'),
        ]
        
        for filename, filepath in files_to_review:
            print(f"\n{'='*70}")
            print(f"Reviewing: {filename}")
            print('='*70)
            
            code = get_file_content(filename, filepath)
            if not code:
                print(f"  Skipping {filename} - couldn't read file")
                continue
            
            message = f"""Could you review this file for me?

Here's the code for {filename}:

```python
{code}
```

Based on the review guidelines we discussed, I'd appreciate your thoughts on:
- Any security concerns or bugs
- Architecture and design improvements  
- Error handling gaps
- General best practices

Feel free to reference specific lines if helpful."""
            
            print(f"  Sending {filename} ({len(code)} chars)...")
            
            try:
                response = await chat.send(message, wait_for_response=True)
                
                print(f"\n  ✓ Review received ({len(response)} chars)")
                print("\n" + "-"*70)
                print("REVIEW:")
                print("-"*70)
                print(response)
                print("-"*70)
                
                # Save progress after each file
                await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_progress.json')
                print(f"  ✓ Progress saved")
                
            except Exception as e:
                print(f"\n  ✗ Error reviewing {filename}: {e}")
                print("  Continuing with next file...")
                continue
        
        # Step 3: Summary
        print("\n" + "=" * 70)
        print("STEP 3: Getting final summary")
        print("=" * 70)
        
        summary_request = """Based on all the file reviews above, provide:

1. TOP 3 CRITICAL ISSUES to fix immediately (with file names)
2. OVERALL ARCHITECTURE ASSESSMENT
3. RECOMMENDED REFACTORING ORDER (what to do first, second, third)

Be actionable and specific."""
        
        print("Requesting summary...")
        summary = await chat.send(summary_request, wait_for_response=True)
        
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        print(summary)
        
        # Step 4: Save final results
        print("\n" + "=" * 70)
        print("STEP 4: Saving results")
        print("=" * 70)
        
        final_path = await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_complete.json')
        print(f"✓ Conversation saved: {final_path}")
        
        # Get the conversation URL
        if chat._current_conversation and chat._current_conversation.url:
            print(f"\n✓ Conversation URL: {chat._current_conversation.url}")
            print(f"\nTo resume this review later, run:")
            print(f"  python do_code_review.py '{chat._current_conversation.url}'")
        
        print("\n" + "=" * 70)
        print("CODE REVIEW COMPLETE")
        print("=" * 70)
        print(f"Files reviewed: {len(files_to_review)}")
        print(f"Total conversation messages: {len(chat.get_history())}")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        print("Saving progress...")
        try:
            await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_progress.json')
            if chat._current_conversation and chat._current_conversation.url:
                print(f"\nTo resume, run: python do_code_review.py '{chat._current_conversation.url}'")
        except:
            pass
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\nClosing browser...")
        await chat.close()
        print("Done!")

if __name__ == "__main__":
    print("ChatGPT Code Review Tool")
    print("=" * 70)
    
    # Get conversation URL from command line if provided
    conversation_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if conversation_url:
        print(f"Will resume conversation: {conversation_url}")
    else:
        print("Starting fresh code review")
    
    print()
    
    # Run with timeout
    import signal
    
    def timeout_handler(signum, frame):
        print("\n\n30 minute timeout reached!")
        raise TimeoutError()
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1800)  # 30 minutes
    
    try:
        asyncio.run(full_code_review(conversation_url))
    except TimeoutError:
        print("\nReview stopped after 30 minutes")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
