#!/usr/bin/env python3
"""
Example: Interactive ChatGPT conversation with persistent browser

This shows the ChatManager class which keeps the browser open
between messages and auto-saves conversations.
"""

import asyncio
from chat_automation import ChatManager, SyncChatManager

# Option 1: Async usage (recommended for scripts)
async def async_example():
    print("=== Async ChatManager Example ===\n")
    
    # Create manager - browser starts on first use
    chat = ChatManager()
    
    try:
        # Start a conversation
        conv_id = chat.start_conversation("Learning Python")
        print(f"Started conversation: {conv_id}\n")
        
        # Send messages - browser stays open
        print("You: What is Python?")
        response1 = await chat.send("What is Python?")
        print(f"ChatGPT: {response1[:200]}...\n")
        
        print("You: What are its main features?")
        response2 = await chat.send("What are its main features?")
        print(f"ChatGPT: {response2[:200]}...\n")
        
        # Get conversation history
        history = chat.get_history()
        print(f"Total messages: {len(history)}\n")
        
        # Export to file
        filepath = await chat.export_conversation("my_conversation.json")
        print(f"Saved to: {filepath}\n")
        
        # Start new chat (clears browser thread)
        await chat.new_chat()
        print("Started new chat in browser\n")
        
        # List all saved conversations
        saved = await chat.list_saved_conversations()
        print(f"You have {len(saved)} saved conversations")
        
    finally:
        # Close browser when done
        await chat.close()
        print("\nBrowser closed")


# Option 2: Sync usage (simpler for notebooks/interactive)
def sync_example():
    print("=== SyncChatManager Example ===\n")
    
    # Use context manager for automatic cleanup
    with SyncChatManager() as chat:
        chat.start_conversation("Quick Chat")
        
        response = chat.send("Hello! Tell me a fun fact")
        print(f"Response: {response[:150]}...\n")
        
        # Continue conversation
        response2 = chat.send("Another one?")
        print(f"Response: {response2[:150]}...\n")
        
        print(f"Total messages: {len(chat.get_history())}")


if __name__ == "__main__":
    # Run async example
    asyncio.run(async_example())
    
    print("\n" + "="*50 + "\n")
    
    # Run sync example
    sync_example()
