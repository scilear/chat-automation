#!/usr/bin/env python3
"""
ChatGPT automation - SEPARATE profile, no impact on main Brave
10 minute timeout for recaptcha/human verification
"""

import asyncio
from chat_automation import ChatGPTAutomation, ChatAutomationConfig


async def main():
    config = ChatAutomationConfig.brave_automation()

    print("Opening Brave (automation profile - separate from your main profile)...")
    chatgpt = None
    try:
        chatgpt = ChatGPTAutomation(config)
        await chatgpt.start()

        print("Navigating to chatgpt.com...")
        await chatgpt.goto("https://chatgpt.com")

        await asyncio.sleep(3)

        try:
            print(f"URL: {chatgpt.page.url}")
            print(f"Title: {await chatgpt.page.title()}")
        except Exception as e:
            print(f"Could not get page info: {e}")

        inner_text = ""
        try:
            body = await chatgpt.page.query_selector('body')
            if body:
                inner_text = await body.inner_text() or ""
                print(f"\nPage preview:\n{inner_text[:400]}")
        except Exception as e:
            print(f"Could not get page content: {e}")

        textarea = await chatgpt.find_textarea()

        if not textarea:
            print("\nChat input not visible yet.")
            print("Please log into ChatGPT in the Brave window.")
            print("I'll detect when the chat interface appears...")

            print(f"\nWaiting up to 10 MINUTES for chat input...")

            for i in range(120):
                try:
                    textarea = await chatgpt.find_textarea()
                    if textarea:
                        print(f"Chat input found at {i*5} seconds!")
                        break
                except Exception as e:
                    print(f"Error checking textarea: {e}")

                await asyncio.sleep(5)
                if i % 12 == 0:
                    print(f"  Still waiting... ({i//12} minutes)")
                else:
                    print(f"  Still waiting... ({i*5}s)")

        if textarea:
            print("\nSending: 'Tell me a joke.'")

            success = await chatgpt.send_message("Tell me a joke.")
            if not success:
                print("Failed to send message!")
            else:
                print("Waiting for response (20s)...")
                await asyncio.sleep(20)

                try:
                    response = await chatgpt.get_last_response()
                    print(f"\n{'='*50}")
                    print("ChatGPT Response:")
                    print(f"{'='*50}")
                    print(response if response.strip() else "[Response not captured - check browser]")
                    print(f"{'='*50}")
                except Exception as e:
                    print(f"Could not get response: {e}")
                    print("Check the browser window for the answer!")
        else:
            print("\nChat input never appeared.")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if chatgpt:
            try:
                await chatgpt.stop()
            except:
                pass


if __name__ == "__main__":
    asyncio.run(main())
