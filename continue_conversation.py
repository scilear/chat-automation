#!/usr/bin/env python3
"""
Interactive ChatGPT tool for continuing conversations

Usage:
    python continue_conversation.py [conversation_id]
    
If no conversation_id provided, lists all saved conversations.
"""

import sys
import asyncio
from chat_automation import SyncChatManager

def list_conversations():
    """List all saved conversations"""
    with SyncChatManager() as chat:
        saved = chat.list_saved_conversations()
        print(f"\nFound {len(saved)} saved conversations:\n")
        for i, path in enumerate(saved, 1):
            # Load to get title
            import json
            try:
                with open(path) as f:
                    data = json.load(f)
                print(f"{i}. {data.get('title', 'Untitled')}")
                print(f"   ID: {data['id']}")
                print(f"   Messages: {len(data.get('messages', []))}")
                print(f"   Updated: {data.get('updated_at', 'Unknown')[:10]}")
                print()
            except:
                print(f"{i}. {path}")
        return saved

def continue_conversation(conv_path):
    """Continue an existing conversation"""
    with SyncChatManager() as chat:
        print(f"\nLoading conversation from: {conv_path}")
        
        if not chat.load_conversation(conv_path):
            print("Failed to load conversation!")
            return
        
        history = chat.get_history()
        print(f"Loaded {len(history)} messages")
        
        # Show last few messages for context
        if history:
            print("\n--- Recent context ---")
            for msg in history[-3:]:
                role = "You" if msg['role'] == 'user' else "AI"
                content = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                print(f"{role}: {content}")
            print("---\n")
        
        print("Interactive mode started. Type your messages (type 'quit' to exit, 'save' to export)\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    break
                
                if user_input.lower() == 'save':
                    import os
                    filename = input("Filename (without extension): ").strip()
                    if filename:
                        chat.export_conversation(f"{filename}.json")
                        print(f"Saved to {filename}.json")
                    continue
                
                print("Waiting for response...")
                response = chat.send(user_input)
                print(f"\nAI: {response}\n")
                
            except KeyboardInterrupt:
                print("\n\nInterrupted. Saving conversation...")
                break
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        # Auto-save at end
        chat.export_conversation(conv_path)
        print(f"\nConversation saved!")

def main():
    if len(sys.argv) < 2:
        print("Usage: python continue_conversation.py <conversation_id>")
        print("\nListing all saved conversations...")
        saved = list_conversations()
        
        if saved:
            choice = input("\nEnter number to continue (or press Enter to exit): ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(saved):
                    continue_conversation(saved[idx])
    else:
        conv_id = sys.argv[1]
        # Find conversation by ID
        import os
        conv_dir = os.path.expanduser("~/.chat_automation/conversations")
        conv_path = os.path.join(conv_dir, f"{conv_id}.json")
        
        if os.path.exists(conv_path):
            continue_conversation(conv_path)
        else:
            print(f"Conversation not found: {conv_id}")
            print("\nAvailable conversations:")
            list_conversations()

if __name__ == "__main__":
    main()
