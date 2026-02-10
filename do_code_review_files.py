#!/usr/bin/env python3
"""
Complete code review process using file uploads

Usage:
    python do_code_review_files.py [conversation_url_or_id]

Uses file upload feature instead of pasting code in messages
"""

import asyncio
import sys
import os
sys.path.insert(0, '/home/fabien/clawd')

from chat_automation import ChatManager

async def full_code_review(conversation_url=None):
    chat = ChatManager()
    
    try:
        # Step 1: Setup
        print("=" * 70)
        print("STEP 1: Setting up code review")
        print("=" * 70)
        
        if conversation_url:
            print(f"Resuming conversation: {conversation_url}")
            success = await chat.open_conversation_by_url(conversation_url)
            if not success:
                print("Failed to open conversation, starting fresh")
                conversation_url = None
        
        if not conversation_url:
            print("Starting fresh code review...")
            
            prompt_request = """I'm working on a Python browser automation project using Playwright. 

Could you create a practical code review checklist focusing on:
- Security issues in browser automation
- Error handling and resource cleanup  
- Async/await best practices
- Element selection strategies
- Reliability improvements

Keep it practical and actionable."""
            
            chat.start_conversation("Code Review - File Upload Method")
            review_prompt = await chat.send(prompt_request, wait_for_response=True)
            
            print("\n✓ Got review prompt")
            print(f"Length: {len(review_prompt)} chars")
        else:
            history = chat.get_history()
            print(f"Resumed conversation with {len(history)} messages")
        
        # Step 2: Upload files one by one
        print("\n" + "=" * 70)
        print("STEP 2: Uploading files for review")
        print("=" * 70)
        
        files_to_review = [
            ('config.py', '/home/fabien/clawd/chat_automation/config.py'),
            ('base.py', '/home/fabien/clawd/chat_automation/base.py'),
            ('chatgpt.py', '/home/fabien/clawd/chat_automation/chatgpt.py'),
            ('manager.py', '/home/fabien/clawd/chat_automation/manager.py'),
        ]
        
        for filename, filepath in files_to_review:
            print(f"\n{'='*70}")
            print(f"Uploading: {filename}")
            print('='*70)
            
            if not os.path.exists(filepath):
                print(f"  ✗ File not found: {filepath}")
                continue
            
            message = f"Please review this file ({filename}) based on the guidelines we discussed. Focus on critical security issues, bugs, and major improvements."
            
            print(f"  Uploading {filename}...")
            try:
                response = await chat.send_file(filepath, message)
                
                print(f"\n  ✓ Review received ({len(response)} chars)")
                print("\n" + "-"*70)
                print("REVIEW:")
                print("-"*70)
                print(response[:1000])  # Show first 1000 chars
                if len(response) > 1000:
                    print(f"... ({len(response) - 1000} more chars)")
                print("-"*70)
                
                # Save progress
                await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_progress.json')
                print(f"  ✓ Progress saved")
                
            except Exception as e:
                print(f"\n  ✗ Error with {filename}: {e}")
                print("  Continuing with next file...")
                continue
        
        # Step 3: Summary
        print("\n" + "=" * 70)
        print("STEP 3: Getting final summary")
        print("=" * 70)
        
        summary_request = """Based on all the file reviews above, provide:

1. TOP 3 CRITICAL ISSUES to fix immediately (with file names)
2. OVERALL ARCHITECTURE ASSESSMENT  
3. RECOMMENDED REFACTORING ORDER

Be specific and actionable."""
        
        print("Requesting summary...")
        summary = await chat.send(summary_request, wait_for_response=True)
        
        print("\n" + "=" * 70)
        print("FINAL SUMMARY")
        print("=" * 70)
        print(summary)
        
        # Step 4: Save
        print("\n" + "=" * 70)
        print("STEP 4: Saving results")
        print("=" * 70)
        
        final_path = await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_complete.json')
        print(f"✓ Saved to: {final_path}")
        
        if chat._current_conversation and chat._current_conversation.url:
            print(f"\n✓ Conversation URL: {chat._current_conversation.url}")
            print(f"\nTo resume: python do_code_review_files.py '{chat._current_conversation.url}'")
        
        print("\n" + "=" * 70)
        print("CODE REVIEW COMPLETE")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print("\n\nInterrupted")
        print("Saving progress...")
        try:
            await chat.export_conversation('/home/fabien/clawd/chat_automation/code_review_progress.json')
            if chat._current_conversation and chat._current_conversation.url:
                print(f"\nTo resume: python do_code_review_files.py '{chat._current_conversation.url}'")
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
    print("ChatGPT Code Review Tool - File Upload Method")
    print("=" * 70)
    
    conversation_url = sys.argv[1] if len(sys.argv) > 1 else None
    
    if conversation_url:
        print(f"Will resume: {conversation_url}")
    else:
        print("Starting fresh code review")
    
    print()
    
    import signal
    def timeout_handler(signum, frame):
        print("\n\n30 minute timeout!")
        raise TimeoutError()
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(1800)
    
    try:
        asyncio.run(full_code_review(conversation_url))
    except TimeoutError:
        print("\nReview stopped after 30 minutes")
    except KeyboardInterrupt:
        print("\n\nStopped by user")
