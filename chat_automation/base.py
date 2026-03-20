"""
Base browser automation module with CDP support
"""

import asyncio
import os
import json
import subprocess
import time
import urllib.request
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from .config import ChatAutomationConfig
from .verbose import log

CDP_STATE_FILE = Path.home() / ".chat_automation" / "browser_cdp.json"
DAEMON_SCRIPT = Path(__file__).parent / "browser-daemon"
CDP_PORT = 9222


class BrowserAutomation(ABC):
    """Abstract base class for browser automation with CDP support"""

    def __init__(self, config: Optional[ChatAutomationConfig] = None):
        self.config = config or ChatAutomationConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def _is_cdp_running(self) -> bool:
        """Check if CDP endpoint is responding"""
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2) as response:
                return response.status == 200
        except:
            return False

    async def _start_daemon(self) -> bool:
        """Auto-start the browser daemon"""
        log("Browser daemon not running, auto-starting...")
        
        daemon_path = str(DAEMON_SCRIPT)
        if not os.path.exists(daemon_path):
            log(f"Daemon script not found: {daemon_path}")
            return False
        
        # Use setsid to create new session so daemon survives parent exit
        subprocess.Popen(
            ['setsid', daemon_path, "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        
        # Wait for daemon to be ready (up to 30 seconds)
        log("Waiting for daemon to start...")
        for i in range(30):
            await asyncio.sleep(1)
            if self._is_cdp_running():
                log("Daemon is ready")
                return True
        
        log("Daemon failed to start")
        return False

    async def start(self) -> None:
        """Start browser - connect to daemon via CDP, auto-start if needed"""
        self.playwright = await async_playwright().start()

        # Check if daemon is running
        if not self._is_cdp_running():
            # Auto-start daemon
            if not await self._start_daemon():
                raise RuntimeError("Failed to start browser daemon")

        # Connect via CDP
        log("Connecting to browser via CDP...")
        cdp_url = f"http://127.0.0.1:{CDP_PORT}"
        
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)

            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                self.context = await self.browser.new_context()

            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()

            # Save CDP endpoint
            CDP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CDP_STATE_FILE, 'w') as f:
                json.dump({'ws_endpoint': f"ws://127.0.0.1:{CDP_PORT}"}, f)

            log("Connected to browser daemon")
            
        except Exception as e:
            log(f"Failed to connect via CDP: {e}")
            raise

    def _setup_page_handlers(self):
        """Setup automatic handlers for common page events"""
        if self.page:
            self.page.on("dialog", lambda dialog: dialog.accept())
            self.page.on("popup", lambda popup: None)

    async def stop(self) -> None:
        """Close browser connection but keep daemon running"""
        # Just stop playwright - this closes the CDP connection
        # but leaves the browser/daemon running
        if self.playwright:
            await self.playwright.stop()
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def disconnect(self) -> None:
        """Alias for stop() - disconnect without closing browser"""
        await self.stop()

    async def close_browser(self) -> None:
        """Actually close the browser daemon"""
        # Stop connection first
        await self.stop()
        
        # Stop the daemon
        daemon_path = str(DAEMON_SCRIPT)
        if os.path.exists(daemon_path):
            subprocess.run([daemon_path, "stop"], capture_output=True)
        
        # Clear CDP state
        if CDP_STATE_FILE.exists():
            CDP_STATE_FILE.unlink()
        
        log("Browser daemon stopped")

    async def goto(self, url: str) -> None:
        """Navigate to URL"""
        await self.page.goto(url)

    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        """Wait for element to appear"""
        await self.page.wait_for_selector(selector, timeout=timeout or self.config.timeout)

    async def click(self, selector: str) -> None:
        """Click an element"""
        await self.page.click(selector)

    async def type_text(self, selector: str, text: str) -> None:
        """Type text into an input"""
        await self.page.fill(selector, text)

    async def get_text(self, selector: str) -> str:
        """Get text content from element"""
        return await self.page.text_content(selector)

    async def get_all_text(self, selector: str) -> List[str]:
        """Get all text contents matching selector"""
        elements = await self.page.query_selector_all(selector)
        return [await el.text_content() for el in elements]

    async def press_key(self, key: str) -> None:
        """Press a keyboard key"""
        await self.page.press("body", key)

    async def wait_for_load_state(self, state: str = "networkidle") -> None:
        """Wait for page to reach certain state"""
        await self.page.wait_for_load_state(state)

    async def scroll_to_bottom(self) -> None:
        """Scroll to bottom of page"""
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

    async def scroll_to_top(self) -> None:
        """Scroll to top of page"""
        await self.page.evaluate("window.scrollTo(0, 0)")

    @abstractmethod
    async def login(self) -> bool:
        """Handle login - override in subclasses"""
        pass

    @abstractmethod
    async def is_logged_in(self) -> bool:
        """Check if logged in - override in subclasses"""
        pass

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop()
