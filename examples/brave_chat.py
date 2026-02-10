#!/usr/bin/env python3
"""
Example: Use Brave browser with existing profile to chat with ChatGPT
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig

BRAVE_USER_DATA_DIR = "/home/fabien/.config/BraveSoftware/Brave-Browser"


async def main():
    config = ChatAutomationConfig.brave(user_data_dir=BRAVE_USER_DATA_DIR)
    async with ChatGPTAutomation(config) as chatgpt:
        print("Opening ChatGPT in Brave with your profile...")
        await chatgpt.goto("https://chatgpt.com")
        await asyncio.sleep(3)

        print("Page title:", await chatgpt.page.title())

        page_content = await chatgpt.page.content()

        if 'login' in page_content.lower() or 'sign up' in page_content.lower():
            print("WARNING: ChatGPT is showing login/signup page!")
            print("Your Brave profile may not be logged into ChatGPT.")
            print("Please log in manually first, then run this script again.")
            return

        print("Logged in detected. Sending message...")

        response = await chatgpt.chat(
            "Hello! This is a test message from my automation script.",
            wait_for_response=True
        )

        print(f"\nChatGPT Response:\n{response}")


if __name__ == "__main__":
    asyncio.run(main())
