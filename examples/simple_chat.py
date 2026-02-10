#!/usr/bin/env python3
"""
Simple ChatGPT automation - run after logging in manually
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig.brave(
        user_data_dir="/home/fabien/.config/BraveSoftware/Brave-Browser"
    )

    print("Opening ChatGPT in Brave...")
    async with ChatGPTAutomation(config) as chatgpt:
        await chatgpt.goto("https://chatgpt.com")

        print(f"Initial page title: {await chatgpt.page.title()}")

        try:
            await chatgpt.page.wait_for_load_state("networkidle", timeout=30000)
            print(f"After networkidle - page title: {await chatgpt.page.title()}")
        except Exception as e:
            print(f"Timeout waiting for networkidle: {e}")

        await asyncio.sleep(3)

        textarea = await chatgpt.page.query_selector('textarea[name="prompt-textarea"]')

        if not textarea:
            print("Textarea not found - checking page structure...")

            body = await chatgpt.page.query_selector('body')
            if body:
                inner_text = await body.inner_text()
                print(f"Body inner text (first 500 chars):\n{inner_text[:500]}")

        if textarea:
            print("Found chat input! Sending message...")

            await textarea.fill("Tell me a joke.")
            await textarea.press("Enter")

            print("Waiting for response (10 seconds)...")
            await asyncio.sleep(10)

            response = await chatgpt.get_last_response()
            print(f"\nChatGPT Response:\n{response}")
        else:
            print("Taking screenshot...")
            await chatgpt.page.screenshot(path="/tmp/chatgpt_state.png")
            print("Screenshot saved to /tmp/chatgpt_state.png")


if __name__ == "__main__":
    asyncio.run(main())
