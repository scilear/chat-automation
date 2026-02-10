#!/usr/bin/env python3
"""
CLI tool for code review with ChatGPT

Usage:
    python code_review_cli.py --file manager.py [--session SESSION_ID]
    python code_review_cli.py --file base.py --prompt "Focus on error handling"
    python code_review_cli.py --continue SESSION_ID
"""

import argparse
import asyncio
import sys
import os
import json
from pathlib import Path

sys.path.insert(0, '/home/fabien/clawd')
from chat_automation import ChatManager

# Configuration
SAVE_DIR = Path.home() / ".chat_automation" / "code_reviews"
SAVE_DIR.mkdir(parents=True, exist_ok=True)

FILES_MAP = {
    'manager.py': '/home/fabien/clawd/chat_automation/manager.py',
    'base.py': '/home/fabien/clawd/chat_automation/base.py',
    'chatgpt.py': '/home/fabien/clawd/chat_automation/chatgpt.py',
    'config.py': '/home/fabien/clawd/chat_automation/config.py',
}

DEFAULT_PROMPT = """Please review this Python code file from a browser automation framework.

Focus on:
1. Critical bugs or security issues
2. Error handling gaps
3. Resource management problems
4. Python best practices

Provide specific line references and code examples for any fixes you suggest."""

async def start_review_session(file_name: str, custom_prompt: str = None, session_id: str = None):
    """Start a new review session for a file"""
    
    if file_name not in FILES_MAP:
        print(f"Error: Unknown file '{file_name}'")
        print(f"Available: {', '.join(FILES_MAP.keys())}")
        return None
    
    filepath = FILES_MAP[file_name]
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        return None
    
    chat = ChatManager()
    
    try:
        print(f"\n{'='*80}")
        print(f"CODE REVIEW: {file_name}")
        print(f"{'='*80}\n")
        
        # Start or resume session
        if session_id:
            print(f"Resuming session: {session_id}")
            # Try to find conversation file
            conv_file = SAVE_DIR / f"{session_id}.json"
            if conv_file.exists():
                await chat.load_conversation(str(conv_file))
                print(f"✓ Loaded conversation with {len(chat.get_history())} messages")
            else:
                print(f"⚠ Session file not found, starting fresh")
                session_id = None
        
        if not session_id:
            print("Starting new review session...")
            chat.start_conversation(f"Code Review - {file_name}")
            
            # Send context prompt
            context = custom_prompt or DEFAULT_PROMPT
            print("\n1. Sending review prompt...")
            intro = await chat.send(context, wait_for_response=True)
            print(f"✓ Context established ({len(intro)} chars)\n")
        
        # Read and send file
        print(f"2. Reading {file_name}...")
        with open(filepath, 'r') as f:
            code = f.read()
        
        print(f"   File size: {len(code)} characters")
        
        # Truncate if needed
        if len(code) > 6000:
            code = code[:6000] + "\n\n[...truncated...]"
            print(f"   Truncated to {len(code)} characters")
        
        # Send file for review
        print(f"\n3. Sending file for review...")
        message = f"Please review this file ({file_name}):\n\n```python\n{code}\n```"
        
        review = await chat.send(message, wait_for_response=True)
        
        print(f"\n{'='*80}")
        print("REVIEW RECEIVED")
        print(f"{'='*80}\n")
        print(review)
        print(f"\n{'='*80}\n")
        
        # Save session
        session_file = SAVE_DIR / f"{chat._current_conversation.id}.json"
        await chat.export_conversation(str(session_file))
        
        print(f"✓ Session saved: {session_file}")
        
        if chat._current_conversation.url:
            print(f"✓ Conversation URL: {chat._current_conversation.url}")
            print(f"\nTo continue this review:")
            print(f"  python code_review_cli.py --continue {chat._current_conversation.id}")
        
        # Save review text separately for easy reading
        review_file = SAVE_DIR / f"{chat._current_conversation.id}_review.txt"
        with open(review_file, 'w') as f:
            f.write(f"Code Review: {file_name}\n")
            f.write(f"{'='*80}\n\n")
            f.write(review)
        
        print(f"✓ Review saved: {review_file}")
        
        return {
            'session_id': chat._current_conversation.id,
            'file': file_name,
            'review': review,
            'url': chat._current_conversation.url
        }
        
    except Exception as e:
        print(f"\n✗ Error during review: {e}")
        import traceback
        traceback.print_exc()
        return None
        
    finally:
        print("\nClosing browser...")
        await chat.close()

async def continue_session(session_id: str, message: str = None):
    """Continue an existing session"""
    
    chat = ChatManager()
    
    try:
        print(f"\n{'='*80}")
        print(f"CONTINUING SESSION: {session_id}")
        print(f"{'='*80}\n")
        
        # Load conversation
        conv_file = SAVE_DIR / f"{session_id}.json"
        if not conv_file.exists():
            print(f"Error: Session not found: {conv_file}")
            return None
        
        print(f"Loading session...")
        await chat.load_conversation(str(conv_file))
        print(f"✓ Loaded conversation with {len(chat.get_history())} messages")
        
        # If message provided, send it
        if message:
            print(f"\nSending message...")
            response = await chat.send(message, wait_for_response=True)
            
            print(f"\n{'='*80}")
            print("RESPONSE")
            print(f"{'='*80}\n")
            print(response)
            
            # Save updated session
            await chat.export_conversation(str(conv_file))
            print(f"\n✓ Session updated")
        else:
            print("\nSession loaded. Ready for interactive use.")
            print("Use --message 'your message' to send a message")
        
        return {
            'session_id': session_id,
            'message_count': len(chat.get_history())
        }
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return None
        
    finally:
        await chat.close()

async def list_sessions():
    """List all saved review sessions"""
    print(f"\n{'='*80}")
    print("SAVED REVIEW SESSIONS")
    print(f"{'='*80}\n")
    
    sessions = []
    for f in SAVE_DIR.glob("*.json"):
        if not f.name.endswith("_review.txt"):
            try:
                with open(f) as file:
                    data = json.load(file)
                sessions.append({
                    'id': data.get('id', 'Unknown'),
                    'title': data.get('title', 'Untitled'),
                    'updated': data.get('updated_at', 'Unknown')[:10],
                    'messages': len(data.get('messages', [])),
                    'file': f.name
                })
            except:
                pass
    
    if not sessions:
        print("No saved sessions found")
        return
    
    # Sort by updated date
    sessions.sort(key=lambda x: x['updated'], reverse=True)
    
    for i, s in enumerate(sessions, 1):
        print(f"{i}. {s['title']}")
        print(f"   ID: {s['id']}")
        print(f"   Messages: {s['messages']}")
        print(f"   Updated: {s['updated']}")
        print()

def main():
    parser = argparse.ArgumentParser(description='Code Review CLI with ChatGPT')
    parser.add_argument('--file', '-f', help='File to review (manager.py, base.py, chatgpt.py, config.py)')
    parser.add_argument('--prompt', '-p', help='Custom review prompt')
    parser.add_argument('--continue', '-c', dest='continue_session', help='Continue existing session ID')
    parser.add_argument('--message', '-m', help='Message to send when continuing session')
    parser.add_argument('--list', '-l', action='store_true', help='List all saved sessions')
    
    args = parser.parse_args()
    
    if args.list:
        asyncio.run(list_sessions())
    elif args.continue_session:
        asyncio.run(continue_session(args.continue_session, args.message))
    elif args.file:
        result = asyncio.run(start_review_session(args.file, args.prompt))
        if result:
            print(f"\n{'='*80}")
            print("SUMMARY")
            print(f"{'='*80}")
            print(f"File reviewed: {result['file']}")
            print(f"Session ID: {result['session_id']}")
            print(f"Review length: {len(result['review'])} characters")
            print(f"\nNext steps:")
            print(f"  1. Read the review: {SAVE_DIR}/{result['session_id']}_review.txt")
            print(f"  2. Continue conversation: python code_review_cli.py --continue {result['session_id']}")
    else:
        parser.print_help()
        print(f"\n\nAvailable files to review:")
        for name, path in FILES_MAP.items():
            print(f"  - {name}")

if __name__ == "__main__":
    main()
