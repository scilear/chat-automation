"""
ChatGPT-specific automation module
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .base import BrowserAutomation
from .config import ChatAutomationConfig
from .verbose import log


class ChatGPTAutomation(BrowserAutomation):
    """Automation for ChatGPT web interface"""

    def __init__(self, config: Optional[ChatAutomationConfig] = None):
        super().__init__(config)

    async def setup_popup_handler(self):
        """Handle dialogs/popups automatically"""
        self.page.on("dialog", lambda dialog: dialog.accept())

    async def login(self) -> bool:
        """Navigate to login page and wait for user interaction"""
        await self.goto(self.config.chatgpt_url)
        await self.wait_for_load_state("networkidle")
        return True

    async def is_logged_in(self) -> bool:
        """Check if logged into ChatGPT"""
        try:
            await self.page.wait_for_selector("[data-testid='user-button'], [data-testid='login-button']", timeout=5000)
            login_btn = await self.page.query_selector("[data-testid='login-button']")
            return login_btn is None
        except:
            return False

    async def find_textarea(self):
        """Find the chat input (contenteditable div or textarea)"""
        # After first message, interface changes - try multiple selectors
        selectors = [
            '#prompt-textarea[contenteditable="true"]',  # Main input
            'div[contenteditable="true"]',  # Contenteditable fallback
            'textarea[name="prompt-textarea"]',  # Textarea fallback
            '[data-testid="chat-input"]',  # Test ID
            'div[id="prompt-textarea"]',  # ID only (in conversation view)
            '.ProseMirror',  # ProseMirror editor class
            '[class*="prompt-textarea"]',  # Class contains
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    # Check if it's actually editable
                    try:
                        is_editable = await element.is_editable()
                        if is_editable:
                            return element
                    except:
                        # If we can't check, return it anyway
                        return element
            except:
                continue
        return None

    async def find_send_button(self):
        """Find the send/submit button"""
        selectors = [
            '#composer-submit-button',  # ID selector
            '[data-testid="send-button"]',  # Test ID
            'button[type="submit"]',  # Submit button
            '[aria-label*="Send"]',  # English
            '[aria-label*="Envoyer"]',  # French
            'button.composer-submit-btn',  # Class-based
            'button svg[class*="send"]',  # SVG-based
            'button:has(svg)',  # Has SVG icon
            'button[class*="submit"]',  # Class contains submit
            'button[class*="primary"]',  # Primary action button
        ]

        for selector in selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn:
                    # Check if visible and enabled
                    try:
                        visible = await btn.is_visible()
                        enabled = await btn.is_enabled()
                        if visible and enabled:
                            return btn
                    except:
                        # If we can't check, return it anyway
                        return btn
            except:
                continue
        return None

    async def wait_for_ready(self) -> None:
        """Wait for ChatGPT interface to be ready"""
        await asyncio.sleep(2)
        textarea = await self.find_textarea()
        if textarea:
            await asyncio.sleep(1)
        else:
            await asyncio.sleep(3)

    async def start_new_chat(self) -> None:
        """Start a new chat conversation"""
        try:
            new_chat_btn = await self.page.query_selector("[data-testid='new-chat-button'], button:has-text('New chat')")
            if new_chat_btn:
                await new_chat_btn.click()
                await asyncio.sleep(1)
        except Exception as e:
            log(f"New chat button not found: {e}")

    async def send_message(self, message: str, max_retries: int = 3) -> bool:
        """Send a message to ChatGPT"""
        for attempt in range(max_retries):
            try:
                # Find the input element
                element = await self.find_textarea()
                if not element:
                    log(f"Attempt {attempt + 1}: Could not find chat input!")
                    await asyncio.sleep(2)
                    continue

                # Try page-level fill with selector first (more robust)
                fill_success = False
                selectors = [
                    '#prompt-textarea',
                    'div[contenteditable="true"]',
                    'textarea[name="prompt-textarea"]'
                ]
                
                for selector in selectors:
                    try:
                        await self.page.fill(selector, message, timeout=5000)
                        log(f"Filled input via page.fill(): {message}")
                        fill_success = True
                        break
                    except Exception as fill_err:
                        continue
                
                if not fill_success:
                    # Fallback to element-level fill
                    await element.fill(message)
                    log(f"Filled input via element.fill(): {message}")
                
                await asyncio.sleep(0.5)

                # Find and click send button
                send_btn = await self.find_send_button()
                if send_btn:
                    try:
                        await send_btn.click()
                        log(f"Sent message via button: {message}")
                        return True
                    except Exception as click_err:
                        log(f"Button click failed: {click_err}, trying Enter key...")
                        # Fallback to Enter key
                        await element.press("Enter")
                        log(f"Sent message via Enter: {message}")
                        return True
                else:
                    # No button found, try Enter key
                    log(f"Send button not found, using Enter key...")
                    await element.press("Enter")
                    log(f"Sent message via Enter: {message}")
                    return True

            except Exception as e:
                log(f"Attempt {attempt + 1} error sending message: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
                continue

        log("Failed to send message after all retries")
        return False

    async def attach_file(self, filepath: str, message: str = "") -> bool:
        """Attach a file to the conversation using file upload
        
        Args:
            filepath: Path to the file to upload
            message: Optional message to send with the file
        """
        try:
            # Find the attach file button
            attach_selectors = [
                'button[data-testid="attach-file-button"]',
                'button[aria-label*="Attach"]',
                'button[aria-label*="Attach file"]',
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
                log("Attach file button not found, trying file input directly...")
                # Try to find file input directly
                file_input = await self.page.query_selector('input[type="file"]')
                if file_input:
                    await file_input.set_input_files(filepath)
                    log(f"Attached file: {filepath}")
                    
                    # Wait a moment for upload
                    await asyncio.sleep(2)
                    
                    # Send message if provided
                    if message:
                        await self.send_message(message)
                    else:
                        # Just click send button
                        send_btn = await self.find_send_button()
                        if send_btn:
                            await send_btn.click()
                            log("Sent file")
                    return True
                else:
                    log("No file input found")
                    return False
            
            # Click attach button
            await attach_btn.click()
            log("Clicked attach button")
            await asyncio.sleep(1)
            
            # Find file input that should now be visible
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(filepath)
                log(f"Attached file: {filepath}")
                
                # Wait for upload
                await asyncio.sleep(2)
                
                # Send message if provided
                if message:
                    await self.send_message(message)
                else:
                    # Click send
                    send_btn = await self.find_send_button()
                    if send_btn:
                        await send_btn.click()
                        log("Sent file")
                
                return True
            else:
                log("File input not found after clicking attach")
                return False
                
        except Exception as e:
            log(f"Error attaching file: {e}")
            return False

    async def wait_for_response(self, timeout: int = 120000) -> bool:
        """Wait for ChatGPT to finish generating response and input to be ready"""
        try:
            for _ in range(timeout // 2000):
                await asyncio.sleep(2)

                stop_btn = await self.page.query_selector("[data-testid='stop-button'], [aria-label='Stop generating']")
                if stop_btn and await stop_btn.is_visible():
                    continue

                textarea = await self.find_textarea()
                if textarea:
                    enabled = await textarea.is_enabled()
                    if enabled:
                        return True

            return False
        except Exception as e:
            log(f"Error waiting for response: {e}")
            return False

    async def get_last_response(self) -> str:
        """Get the last response from ChatGPT"""
        try:
            await self.scroll_to_bottom()
            await asyncio.sleep(1)

            responses = await self.page.query_selector_all('[data-message-id], .assistant-content, .markdown, .prose')

            if responses:
                last = responses[-1]
                text = await last.text_content()
                return text or ""
        except Exception as e:
            log(f"Error getting response: {e}")
        return ""

    async def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get all messages in current conversation"""
        messages = []
        try:
            user_msgs = await self.page.query_selector_all("[data-testid='conversation-turn:user'], .user-message, .human-message")
            assistant_msgs = await self.page.query_selector_all("[data-testid='conversation-turn:assistant'], .assistant-message, .ai-message")

            for i, (user, assistant) in enumerate(zip(user_msgs, assistant_msgs)):
                user_text = (await user.text_content()) or ""
                assistant_text = (await assistant.text_content()) or ""
                messages.append({"role": "user", "content": user_text})
                if assistant_text:
                    messages.append({"role": "assistant", "content": assistant_text})
        except Exception as e:
            log(f"Error getting history: {e}")
        return messages

    async def list_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent conversations from sidebar"""
        await self.goto(self.config.chatgpt_url)
        await asyncio.sleep(2)

        conversations = []
        try:
            conv_items = await self.page.query_selector_all("[data-testid='conversation-item'], .conversation-item, [class*='conversation']")[:limit]

            for item in conv_items:
                try:
                    title_elem = await item.query_selector(".title, [data-testid='conversation-title'], [class*='title']")
                    date_elem = await item.query_selector(".date, [data-testid='conversation-date'], [class*='date']")
                    title = (await title_elem.text_content()) if title_elem else "Untitled"
                    date = (await date_elem.text_content()) if date_elem else ""

                    conversations.append({
                        "title": title.strip() if title else "Untitled",
                        "date": date.strip() if date else "",
                        "element": item
                    })
                except Exception as e:
                    log(f"Error parsing conversation item: {e}")
        except Exception as e:
            log(f"Error listing conversations: {e}")
        return conversations

    async def open_conversation(self, title: str) -> bool:
        """Open a specific conversation by title"""
        conversations = await self.list_conversations()
        for conv in conversations:
            if title.lower() in conv["title"].lower():
                await conv["element"].click()
                await self.wait_for_ready()
                return True
        return False

    async def chat(self, message: str, wait_for_response: bool = True) -> str:
        """Send message and return response"""
        success = await self.send_message(message)
        if not success:
            return "Failed to send message"

        if wait_for_response:
            log("Waiting for response...")
            ready = await self.wait_for_response()
            if not ready:
                return "Response timed out"
            await asyncio.sleep(1)

        return await self.get_last_response()
