#!/usr/bin/env python3
"""
Example: Open a specific conversation and continue chatting
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig(headless=False)
    async with ChatGPTAutomation(config) as chatgpt:
        target_title = "python automation"

        print(f"Looking for conversation containing: '{target_title}'")
        found = await chatgpt.open_conversation(target_title)

        if found:
            print("Conversation opened!")
            await chatgpt.wait_for_ready()

            response = await chatgpt.chat("Continue from where we left off")
            print(f"\nResponse:\n{response}")
        else:
            print("Conversation not found")


if __name__ == "__main__":
    asyncio.run(main())
