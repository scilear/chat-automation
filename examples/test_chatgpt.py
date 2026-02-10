#!/usr/bin/env python3
"""
Test ChatGPT loading without user data dir
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig.brave()

    print("Opening ChatGPT in Brave (NO profile)...")
    async with ChatGPTAutomation(config) as chatgpt:
        await chatgpt.goto("https://chatgpt.com")

        print(f"Page title: {await chatgpt.page.title()}")

        await asyncio.sleep(5)

        body = await chatgpt.page.query_selector('body')
        if body:
            inner_text = await body.inner_text()
            print(f"Body text preview:\n{inner_text[:300]}")

        textarea = await chatgpt.page.query_selector('textarea[name="prompt-textarea"]')
        if textarea:
            print("Found textarea!")

            await textarea.fill("Tell me a joke.")
            await textarea.press("Enter")

            await asyncio.sleep(8)

            response = await chatgpt.get_last_response()
            print(f"\nResponse:\n{response}")
        else:
            print("No textarea found")

        await chatgpt.page.screenshot(path="/tmp/chatgpt_test.png")
        print("Screenshot: /tmp/chatgpt_test.png")


if __name__ == "__main__":
    asyncio.run(main())
