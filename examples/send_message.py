#!/usr/bin/env python3
"""
Example: Send a message to ChatGPT and get response
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig(headless=False)
    async with ChatGPTAutomation(config) as chatgpt:
        print("Logged in. Waiting for ready state...")
        await chatgpt.wait_for_ready()

        response = await chatgpt.chat(
            "Explain quantum computing in simple terms",
            wait_for_response=True
        )

        print(f"\nChatGPT Response:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
