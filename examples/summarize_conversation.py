#!/usr/bin/env python3
"""
Example: Summarize current conversation
"""

import asyncio
from chat_automation import ChatGPTAutomation, ConversationManager, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig(headless=False)
    async with ChatGPTAutomation(config) as chatgpt:
        await chatgpt.wait_for_ready()

        manager = ConversationManager(chatgpt, storage_dir="./exports/chatgpt")

        summary = await manager.summarize_conversation()
        print(f"\nConversation Summary:\n{summary}")

        saved_path = await manager.save_conversation()
        print(f"\nConversation saved to: {saved_path}")


if __name__ == "__main__":
    asyncio.run(main())
