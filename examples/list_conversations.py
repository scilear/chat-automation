#!/usr/bin/env python3
"""
Example: List all conversations from ChatGPT sidebar
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig(headless=False)
    async with ChatGPTAutomation(config) as chatgpt:
        print("Loading conversations...")
        conversations = await chatgpt.list_conversations(limit=50)

        print(f"\nFound {len(conversations)} conversations:\n")
        for i, conv in enumerate(conversations, 1):
            print(f"{i}. {conv['title']} ({conv['date']})")


if __name__ == "__main__":
    asyncio.run(main())
