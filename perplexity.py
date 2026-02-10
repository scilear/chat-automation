"""
Perplexity-specific automation module
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BrowserAutomation
from .config import ChatAutomationConfig


class PerplexityAutomation(BrowserAutomation):
    """Automation for Perplexity web interface"""

    def __init__(self, config: Optional[ChatAutomationConfig] = None):
        super().__init__(config)

    async def setup_popup_handler(self):
        """Handle dialogs/popups automatically"""
        self.page.on("dialog", lambda dialog: dialog.accept())

    async def login(self) -> bool:
        """Navigate to login page and wait for user interaction"""
        await self.goto(self.config.perplexity_url)
        await self.wait_for_load_state("networkidle")
        return True

    async def is_logged_in(self) -> bool:
        """Check if logged into Perplexity"""
        try:
            await self.page.wait_for_selector("[data-testid='user-menu'], button[aria-label*='profile'], nav", timeout=5000)
            login_btn = await self.page.query_selector("button:has-text('Sign In'), a:has-text('Sign In')")
            return login_btn is None
        except:
            return False

    async def find_textarea(self):
        """Find the chat input textarea"""
        selectors = [
            'textarea[placeholder*="Ask"]',
            'textarea[placeholder*="question"]',
            'textarea[name="q"]',
            'textarea[aria-label*="Ask"]',
            'div[contenteditable="true"]',
            'textarea',
            '[data-testid="ask-input"]',
            'input[type="text"][placeholder*="Ask"]',
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    try:
                        is_visible = await element.is_visible()
                        if is_visible:
                            return element
                    except:
                        return element
            except:
                continue
        return None

    async def find_send_button(self):
        """Find the send/submit button"""
        selectors = [
            'button[type="submit"]',
            'button[aria-label*="Send"]',
            'button[aria-label*="Submit"]',
            'button:has(svg)',
            'button[class*="send"]',
            'button[class*="submit"]',
            'button:has-text("Ask")',
        ]

        for selector in selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    try:
                        visible = await btn.is_visible()
                        enabled = await btn.is_enabled()
                        if visible and enabled:
                            return btn
                    except:
                        return btn
            except:
                continue
        return None

    async def wait_for_ready(self) -> None:
        """Wait for Perplexity interface to be ready"""
        await asyncio.sleep(2)
        textarea = await self.find_textarea()
        if textarea:
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(3)

    async def start_new_chat(self) -> None:
        """Start a new chat conversation"""
        try:
            new_chat_btn = await self.page.query_selector("button:has-text('New'), a:has-text('New'), [data-testid='new-thread']")
            if new_chat_btn:
                await new_chat_btn.click()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"New chat button not found: {e}")

    async def send_message(self, message: str, max_retries: int = 3) -> bool:
        """Send a message to Perplexity"""
        for attempt in range(max_retries):
            try:
                element = await self.find_textarea()
                if not element:
                    print(f"Attempt {attempt + 1}: Could not find chat input!")
                    await asyncio.sleep(2)
                    continue

                fill_success = False
                selectors = [
                    'textarea[placeholder*="Ask"]',
                    'textarea[name="q"]',
                    'div[contenteditable="true"]',
                    'textarea',
                ]
                
                for selector in selectors:
                    try:
                        await self.page.fill(selector, message, timeout=5000)
                        print(f"Filled input via page.fill(): {message}")
                        fill_success = True
                        break
                    except Exception as fill_err:
                        continue
                
                if not fill_success:
                    await element.fill(message)
                    print(f"Filled input via element.fill(): {message}")
                
                await asyncio.sleep(0.5)

                send_btn = await self.find_send_button()
                if send_btn:
                    try:
                        await send_btn.click()
                        print(f"Sent message via button: {message}")
                        return True
                    except Exception as click_err:
                        print(f"Button click failed: {click_err}, trying Enter key...")
                        await element.press("Enter")
                        print(f"Sent message via Enter: {message}")
                        return True
                else:
                    print(f"Send button not found, using Enter key...")
                    await element.press("Enter")
                    print(f"Sent message via Enter: {message}")
                    return True

            except Exception as e:
                print(f"Attempt {attempt + 1} error sending message: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                continue

        print("Failed to send message after all retries")
        return False

    async def attach_file(self, filepath: str, message: str = "") -> bool:
        """Attach a file to the conversation using file upload
        
        Args:
            filepath: Path to the file to upload
            message: Optional message to send with the file
        """
        try:
            attach_selectors = [
                'button[aria-label*="Attach"]',
                'button[aria-label*="Upload"]',
                'button svg[class*="attach"]',
                'button svg[class*="paperclip"]',
                'button:has(svg[class*="attach"])',
                'button:has(svg[class*="paperclip"])',
            ]
            
            attach_btn = None
            for selector in attach_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        visible = await btn.is_visible()
                        if visible:
                            attach_btn = btn
                            break
                except:
                    continue
            
            if not attach_btn:
                print("Attach file button not found, trying file input directly...")
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(filepath)
                    print(f"Attached file: {filepath}")
                    await asyncio.sleep(2)
                    if message:
                        await self.send_message(message)
                    else:
                        send_btn = await self.find_send_button()
                        if send_btn:
                            await send_btn.click()
                            print("Sent file")
                    return True
                else:
                    print("No file input found")
                    return False
            
            await attach_btn.click()
            print("Clicked attach button")
            await asyncio.sleep(1)
            
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(filepath)
                print(f"Attached file: {filepath}")
                await asyncio.sleep(2)
                if message:
                    await self.send_message(message)
                else:
                    send_btn = await self.find_send_button()
                    if send_btn:
                        await send_btn.click()
                        print("Sent file")
                return True
            else:
                print("File input not found after clicking attach")
                return False
                
        except Exception as e:
            print(f"Error attaching file: {e}")
            return False

    async def wait_for_response(self, timeout: int = 120000) -> bool:
        """Wait for Perplexity to finish generating response"""
        try:
            for _ in range(timeout // 2000):
                await asyncio.sleep(2)

                stop_btn = await self.page.query_selector("button[aria-label*='Stop'], button:has-text('Stop')")
                if stop_btn and await stop_btn.is_visible():
                    continue

                textarea = await self.find_textarea()
                if textarea:
                    enabled = await textarea.is_enabled()
                    if enabled:
                        return True

            return False
        except Exception as e:
            print(f"Error waiting for response: {e}")
            return False

    async def get_last_response(self) -> str:
        """Get the last response from Perplexity"""
        try:
            await self.scroll_to_bottom()
            await asyncio.sleep(1)

            selectors = [
                '[data-testid="answer"]',
                '.answer-content',
                '.prose',
                '.markdown',
                'article',
                '[class*="answer"]',
            ]
            
            for selector in selectors:
                responses = await self.page.query_selector_all(selector)
                if responses:
                    last = responses[-1]
                    text = await last.text_content()
                    return text or ""
            
            page_content = await self.page.content()
            return ""
        except Exception as e:
            print(f"Error getting response: {e}")
        return ""

    async def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get all messages in current conversation"""
        messages = []
        try:
            user_selectors = ["[data-testid='user-query']", ".user-message", "[class*='user-query']"]
            assistant_selectors = ["[data-testid='answer']", ".assistant-message", "[class*='answer']"]
            
            for user_sel, assistant_sel in zip(user_selectors, assistant_selectors):
                user_msgs = await self.page.query_selector_all(user_sel)
                assistant_msgs = await self.page.query_selector_all(assistant_sel)
                
                if user_msgs or assistant_msgs:
                    for i, (user, assistant) in enumerate(zip(user_msgs, assistant_msgs)):
                        user_text = (await user.text_content()) or ""
                        assistant_text = (await assistant.text_content()) or ""
                        messages.append({"role": "user", "content": user_text})
                        if assistant_text:
                            messages.append({"role": "assistant", "content": assistant_text})
                    break
        except Exception as e:
            print(f"Error getting history: {e}")
        return messages

    async def chat(self, message: str, wait_for_response: bool = True) -> str:
        """Send message and return response"""
        success = await self.send_message(message)
        if not success:
            return "Failed to send message"

        if wait_for_response:
            print("Waiting for response...")
            ready = await self.wait_for_response()
            if not ready:
                return "Response timed out"
            await asyncio.sleep(1)

        return await self.get_last_response()
