"""
Lazy Browser Manager for ChatGPT Automation

Keeps browser open between conversations, with auto-restart on crash.
Simple class-based API - no server needed.

Usage:
    from chat_manager import ChatManager
    
    # Browser starts automatically on first use
    chat = ChatManager()
    
    # Start a conversation
    chat.start_conversation()
    response = chat.send("Tell me about Python")
    
    # Continue conversation (browser stays open)
    response2 = chat.send("What are its main features?")
    
    # Save when done
    chat.export_conversation("python_chat.json")
    
    # Browser stays open until you explicitly close
    chat.close()
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from pathlib import Path

from .chatgpt import ChatGPTAutomation
from .config import ChatAutomationConfig
from .verbose import log

PID_FILE = Path.home() / ".chat_automation" / "browser_daemon.pid"


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: str


@dataclass  
class Conversation:
    id: str
    title: str
    messages: List[Message]
    created_at: str
    updated_at: str
    url: Optional[str] = None  # ChatGPT conversation URL (e.g., https://chatgpt.com/c/xxx)


class ChatManager:
    """
    Manages persistent ChatGPT browser sessions.
    
    - Lazy initialization (browser starts on first use)
    - Auto-restart if browser crashes
    - Conversation history tracking
    - Export/import conversations
    """
    
    def __init__(
        self,
        config: Optional[ChatAutomationConfig] = None,
        save_dir: str = "~/.chat_automation/conversations"
    ):
        self.config = config or ChatAutomationConfig.brave_automation()
        self.save_dir = os.path.expanduser(save_dir)
        os.makedirs(self.save_dir, exist_ok=True)
        
        # Browser state
        self._chatgpt: Optional[ChatGPTAutomation] = None
        self._browser_started = False
        
        # Current conversation
        self._current_conversation: Optional[Conversation] = None
        
    async def _start_daemon(self) -> bool:
        """Start browser daemon if not running"""
        script = '''
import asyncio
import sys
import os
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation.config import ChatAutomationConfig
from chat_automation.base import BrowserAutomation
from pathlib import Path

PID_FILE = Path.home() / ".chat_automation" / "browser_daemon.pid"

async def main():
    config = ChatAutomationConfig.brave_automation()
    
    # Actually launch a browser with CDP
    from playwright.async_api import async_playwright
    pw = await async_playwright().start()
    browser = await pw.chromium.launch_persistent_context(
        user_data_dir=config.user_data_dir,
        headless=False,
        viewport={"width": 1280, "height": 800},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--remote-debugging-port=9222",
        ]
    )
    
    page = browser.pages[0] if browser.pages else await browser.new_page()
    await page.goto("https://chatgpt.com")
    
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    print("Browser daemon started on port 9222")
    
    while True:
        await asyncio.sleep(60)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
'''
        script_file = Path.home() / ".chat_automation" / "daemon_runner.py"
        script_file.parent.mkdir(parents=True, exist_ok=True)
        with open(script_file, 'w') as f:
            f.write(script)
        
        subprocess.Popen(
            [sys.executable, str(script_file)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        
        for _ in range(20):
            await asyncio.sleep(1)
            try:
                import urllib.request
                with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2) as response:
                    if response.status == 200:
                        return True
            except:
                pass
        return False
    
    async def _ensure_browser(self) -> ChatGPTAutomation:
        """Start browser if not running, with auto-restart on failure"""
        if self._chatgpt is None or not await self._is_browser_alive():
            log("Connecting to browser...")
            self._chatgpt = ChatGPTAutomation(self.config)
            
            try:
                await self._chatgpt.start()
            except RuntimeError as e:
                if "Browser daemon not running" in str(e):
                    log("Starting browser daemon...")
                    if await self._start_daemon():
                        log("Daemon started, connecting...")
                        await self._chatgpt.start()
                    else:
                        raise RuntimeError("Failed to start browser daemon")
                else:
                    raise
            
            try:
                current_url = self._chatgpt.page.url
                if 'chatgpt.com' not in current_url:
                    log("Navigating to ChatGPT...")
                    await self._chatgpt.goto("https://chatgpt.com")
                    await asyncio.sleep(2)
                else:
                    log("Already on ChatGPT, skipping navigation")
            except Exception as e:
                log(f"URL check failed, navigating anyway: {e}")
                await self._chatgpt.goto("https://chatgpt.com")
                await asyncio.sleep(2)
            
            self._browser_started = True
            log("Connected")
        return self._chatgpt
    
    async def _is_browser_alive(self) -> bool:
        """Check if browser is still responsive"""
        if self._chatgpt is None or self._chatgpt.page is None:
            return False
        try:
            await self._chatgpt.page.evaluate("1 + 1")
            return True
        except Exception as e:
            log(f"Browser check failed: {e}")
            return False
    
    async def _ensure_logged_in(self) -> bool:
        """Check if logged in, prompt if not"""
        chatgpt = await self._ensure_browser()
        
        try:
            login_btn = await chatgpt.page.query_selector('[data-testid="login-button"], button:has-text("Log in")')
            if login_btn and await login_btn.is_visible():
                log("Waiting for login...")
                for i in range(60):
                    await asyncio.sleep(1)
                    login_btn = await chatgpt.page.query_selector('[data-testid="login-button"]')
                    if not login_btn or not await login_btn.is_visible():
                        log("Logged in")
                        return True
                log("Login timeout - continuing anyway")
                return False
        except Exception as e:
            log(f"Login check error: {e}")
        
        return True
    
    def start_conversation(self, title: Optional[str] = None) -> str:
        """Start a new conversation"""
        conv_id = f"conv_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._current_conversation = Conversation(
            id=conv_id,
            title=title or f"Conversation {conv_id}",
            messages=[],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        return conv_id
    
    async def send(self, message: str, wait_for_response: bool = True) -> str:
        """Send a message in current conversation"""
        if self._current_conversation is None:
            self.start_conversation()
        
        await self._ensure_browser()
        await self._ensure_logged_in()
        
        self._current_conversation.messages.append(Message(
            role="user",
            content=message,
            timestamp=datetime.now().isoformat()
        ))
        
        try:
            response = await self._chatgpt.chat(message, wait_for_response=wait_for_response)
            
            self._current_conversation.messages.append(Message(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat()
            ))
            
            self._current_conversation.updated_at = datetime.now().isoformat()
            
            await self._auto_save()
            
            return response
            
        except Exception as e:
            log(f"Error sending message: {e}")
            log("Attempting browser restart...")
            await self._restart_browser()
            return f"Error: {str(e)}"
    
    async def send_formatted(self, message: str) -> str:
        """Send a message and return response with markdown formatting preserved
        
        Uses clipboard-based extraction to get the raw markdown from the response.
        """
        if self._current_conversation is None:
            self.start_conversation()
        
        await self._ensure_browser()
        await self._ensure_logged_in()
        
        self._current_conversation.messages.append(Message(
            role="user",
            content=message,
            timestamp=datetime.now().isoformat()
        ))
        
        try:
            success = await self._chatgpt.send_message(message)
            if not success:
                return "Failed to send message"
            
            log("Waiting for response...")
            ready = await self._chatgpt.wait_for_response()
            if not ready:
                return "Response timed out"
            
            await asyncio.sleep(1)
            
            log("Getting formatted response...")
            response = await self._chatgpt.get_formatted_response()
            
            if not response:
                log("Formatted response empty, trying fallback")
                response = await self._chatgpt.get_last_response()
            
            log(f"Got response ({len(response)} chars)")
            
            self._current_conversation.messages.append(Message(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat()
            ))
            
            self._current_conversation.updated_at = datetime.now().isoformat()
            
            await self._auto_save()
            
            return response
            
        except Exception as e:
            log(f"Error sending message: {e}")
            await self._restart_browser()
            return f"Error: {str(e)}"
            await self._restart_browser()
            return f"Error: {str(e)}"
    
    async def send_file(self, filepath: str, message: str = "") -> str:
        """Send a file attachment to ChatGPT
        
        Args:
            filepath: Path to file to upload
            message: Optional message to send with file
            
        Returns:
            Response text from ChatGPT
        """
        if self._current_conversation is None:
            self.start_conversation()
        
        # Ensure browser and login
        await self._ensure_browser()
        await self._ensure_logged_in()
        
        try:
            # Add user message
            self._current_conversation.messages.append(Message(
                role="user",
                content=f"[File: {filepath}] {message}".strip(),
                timestamp=datetime.now().isoformat()
            ))
            
            # Upload file
            success = await self._chatgpt.attach_file(filepath, message)
            
            if not success:
                log("File upload failed, sending as text...")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    return f"Error: Cannot send binary file '{filepath}' as text. Upload failed."
                
                # Truncate if too long
                if len(content) > 5000:
                    content = content[:5000] + "\n\n[...truncated...]"
                
                response = await self._chatgpt.chat(f"Please review this code:\n\n```python\n{content}\n```", wait_for_response=True)
            else:
                # Wait for response after file upload
                await self._chatgpt.wait_for_response()
                response = await self._chatgpt.get_last_response()
            
            # Add assistant response
            self._current_conversation.messages.append(Message(
                role="assistant",
                content=response,
                timestamp=datetime.now().isoformat()
            ))
            
            self._current_conversation.updated_at = datetime.now().isoformat()
            
            # Auto-save
            await self._auto_save()
            
            return response
            
        except Exception as e:
            log(f"Error sending file: {e}")
            return f"Error: {str(e)}"
    
    async def _restart_browser(self):
        """Restart the browser"""
        log("Restarting browser...")
        if self._chatgpt:
            try:
                await self._chatgpt.stop()
            except:
                pass
        self._chatgpt = None
        self._browser_started = False
        await self._ensure_browser()
    
    async def _auto_save(self):
        """Auto-save current conversation"""
        if self._current_conversation:
            await self.export_conversation(
                os.path.join(self.save_dir, f"{self._current_conversation.id}.json")
            )
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get current conversation history"""
        if not self._current_conversation:
            return []
        return [
            {"role": msg.role, "content": msg.content, "timestamp": msg.timestamp}
            for msg in self._current_conversation.messages
        ]
    
    async def _update_conversation_url(self):
        """Update conversation URL from browser"""
        if self._chatgpt and self._chatgpt.page:
            try:
                current_url = self._chatgpt.page.url
                if '/c/' in current_url:
                    self._current_conversation.url = current_url
            except:
                pass
    
    async def open_conversation_by_url(self, url: str) -> bool:
        """Open a specific conversation by its ChatGPT URL"""
        try:
            chatgpt = await self._ensure_browser()
            await chatgpt.goto(url)
            await asyncio.sleep(3)
            
            if self._current_conversation:
                self._current_conversation.url = url
            
            log(f"Opened conversation: {url}")
            return True
        except Exception as e:
            log(f"Error opening conversation: {e}")
            return False
    
    async def export_conversation(self, filepath: str) -> str:
        """Export conversation to JSON file"""
        if not self._current_conversation:
            return "No conversation to export"
        
        # Update URL before exporting
        await self._update_conversation_url()
        
        data = {
            "id": self._current_conversation.id,
            "title": self._current_conversation.title,
            "created_at": self._current_conversation.created_at,
            "updated_at": self._current_conversation.updated_at,
            "url": self._current_conversation.url,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp}
                for m in self._current_conversation.messages
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filepath
    
    async def list_saved_conversations(self) -> List[str]:
        """List all saved conversation files"""
        files = []
        for f in os.listdir(self.save_dir):
            if f.endswith('.json'):
                files.append(os.path.join(self.save_dir, f))
        return sorted(files, key=os.path.getmtime, reverse=True)
    
    async def load_conversation(self, filepath: str) -> bool:
        """Load a conversation from file and navigate to its URL"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            required = ['id', 'title', 'messages', 'created_at', 'updated_at']
            missing = [k for k in required if k not in data]
            if missing:
                log(f"Invalid conversation file: missing fields {missing}")
                return False
            
            self._current_conversation = Conversation(
                id=data['id'],
                title=data['title'],
                messages=[
                    Message(
                        role=m.get('role', 'unknown'),
                        content=m.get('content', ''),
                        timestamp=m.get('timestamp', '')
                    ) for m in data['messages']
                ],
                created_at=data['created_at'],
                updated_at=data['updated_at'],
                url=data.get('url')
            )
            
            if self._current_conversation.url:
                log(f"Opening conversation: {self._current_conversation.url}")
                await self.open_conversation_by_url(self._current_conversation.url)
            
            return True
        except json.JSONDecodeError as e:
            log(f"Invalid JSON in conversation file: {e}")
            return False
        except Exception as e:
            log(f"Error loading conversation: {e}")
            return False
    
    async def new_chat(self) -> None:
        """Start a fresh chat in browser (clears current thread)"""
        chatgpt = await self._ensure_browser()
        await chatgpt.start_new_chat()
        self.start_conversation()
    
    async def close(self, keep_browser_open: bool = True):
        """Close connection but keep browser running for reuse"""
        if self._chatgpt:
            try:
                if keep_browser_open:
                    await self._chatgpt.stop()
                    log("Disconnected (browser still running)")
                else:
                    await self._chatgpt.close_browser()
                    log("Browser closed")
            except Exception as e:
                log(f"Note: {e}")
        self._chatgpt = None
        self._browser_started = False
    
    async def close_browser(self):
        """Actually close the browser"""
        await self.close(keep_browser_open=False)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# Convenience sync wrapper for simple usage
class SyncChatManager:
    """Synchronous wrapper around ChatManager"""
    
    def __init__(self, **kwargs):
        self._async_manager = ChatManager(**kwargs)
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
    
    def _run(self, coro):
        """Run async coroutine in sync context"""
        return self._loop.run_until_complete(coro)
    
    def start_conversation(self, title: Optional[str] = None) -> str:
        return self._async_manager.start_conversation(title)
    
    def send(self, message: str, wait_for_response: bool = True) -> str:
        return self._run(self._async_manager.send(message, wait_for_response))
    
    def get_history(self) -> List[Dict[str, Any]]:
        return self._async_manager.get_history()
    
    def export_conversation(self, filepath: str) -> str:
        return self._run(self._async_manager.export_conversation(filepath))
    
    def list_saved_conversations(self) -> List[str]:
        return self._run(self._async_manager.list_saved_conversations())
    
    def load_conversation(self, filepath: str) -> bool:
        return self._run(self._async_manager.load_conversation(filepath))
    
    def new_chat(self) -> None:
        return self._run(self._async_manager.new_chat())
    
    def close(self):
        self._run(self._async_manager.close())
        self._loop.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
