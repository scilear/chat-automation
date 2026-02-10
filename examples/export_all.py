#!/usr/bin/env python3
"""
Example: Export all conversations to JSON files
"""

import asyncio
from chat_automation import ChatGPTAutomation, ConversationManager, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig(headless=False)
    async with ChatGPTAutomation(config) as chatgpt:
        print("Navigating to ChatGPT...")
        await chatgpt.goto("https://chatgpt.com")

        manager = ConversationManager(chatgpt, storage_dir="./exports/chatgpt")

        print("Exporting all conversations...")
        saved_files = await manager.export_all_conversations()

        print(f"\nExported {len(saved_files)} conversations:")
        for f in saved_files:
            print(f"  - {f}")


if __name__ == "__main__":
    asyncio.run(main())
