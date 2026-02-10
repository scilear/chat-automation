"""
Base browser automation module with CDP support
"""

import asyncio
import os
import json
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod

from .config import ChatAutomationConfig
from .verbose import log

CDP_STATE_FILE = Path.home() / ".chat_automation" / "browser_cdp.json"

class BrowserAutomation(ABC):
    """Abstract base class for browser automation with CDP support"""

    def __init__(self, config: Optional[ChatAutomationConfig] = None):
        self.config = config or ChatAutomationConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._cdp_ws_endpoint: Optional[str] = None

    def _get_cdp_endpoint(self) -> Optional[str]:
        """Get saved CDP endpoint if browser is still running"""
        if CDP_STATE_FILE.exists():
            try:
                with open(CDP_STATE_FILE) as f:
                    data = json.load(f)
                return data.get('ws_endpoint')
            except:
                pass
        return None

    def _save_cdp_endpoint(self, ws_endpoint: str):
        """Save CDP endpoint for reconnection"""
        CDP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CDP_STATE_FILE, 'w') as f:
            json.dump({'ws_endpoint': ws_endpoint}, f)

    def _clear_cdp_endpoint(self):
        """Clear saved CDP endpoint"""
        if CDP_STATE_FILE.exists():
            CDP_STATE_FILE.unlink()

    async def start(self) -> None:
        """Start browser - try CDP first, then launch new"""
        self.playwright = await async_playwright().start()

        cdp_port = 9222
        cdp_url = f"http://127.0.0.1:{cdp_port}"
        
        try:
            log("Connecting to browser daemon...")
            self.browser = await self.playwright.chromium.connect_over_cdp(cdp_url)
            
            if self.browser.contexts:
                self.context = self.browser.contexts[0]
            else:
                self.context = await self.browser.new_context()
            
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()
            
            log("Connected to daemon")
            return
        except Exception as e:
            log(f"Daemon not running: {e}")
            raise RuntimeError("Browser daemon not running. Start it with: ./chatgpt-daemon start")

    async def _launch_new_browser(self) -> None:
        """Launch new browser with CDP enabled"""
        log("Starting new browser...")

        Brave_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

        # CDP port for reconnection
        CDP_PORT = 9222

        ANTI_DETECTION_ARGS = [
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-gpu",
            "--window-size=1280,800",
            f"--remote-debugging-port={CDP_PORT}",
        ]

        if self.config.user_data_dir:
            browser = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=self.config.user_data_dir,
                headless=self.config.headless,
                viewport={"width": 1280, "height": 800},
                user_agent=Brave_USER_AGENT,
                args=ANTI_DETECTION_ARGS,
            )
            # For persistent context, the browser is the context
            self.browser = browser
            self.context = browser
            self.page = browser.pages[0] if browser.pages else None
            
            # Save CDP endpoint
            ws_endpoint = f"ws://127.0.0.1:{CDP_PORT}"
            self._save_cdp_endpoint(ws_endpoint)
        else:
            browser_args: Dict[str, Any] = {
                "headless": self.config.headless,
                "args": ANTI_DETECTION_ARGS,
            }

            if self.config.browser_channel:
                browser_args["channel"] = self.config.browser_channel
            if self.config.browser_executable_path:
                browser_args["executable_path"] = self.config.browser_executable_path

            self.browser = await self.playwright.chromium.launch(**browser_args)

            self.context = await self.browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent=Brave_USER_AGENT,
            )
            self.page = await self.context.new_page()

            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'automation', {get: () => undefined});
            """)
            
            # Save CDP endpoint
            ws_endpoint = f"ws://127.0.0.1:{CDP_PORT}"
            self._save_cdp_endpoint(ws_endpoint)

        if self.page:
            self.page.set_default_timeout(self.config.timeout)
            self._setup_page_handlers()
        
        log(f"Browser started with CDP on port {CDP_PORT}")

    def _setup_page_handlers(self):
        """Setup automatic handlers for common page events"""
        self.page.on("dialog", lambda dialog: dialog.accept())
        self.page.on("popup", lambda popup: None)

    async def stop(self) -> None:
        """Close browser and cleanup - but don't clear CDP endpoint"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        # Don't clear CDP endpoint - browser stays open for reconnection

    async def close_browser(self) -> None:
        """Actually close the browser and clear CDP endpoint"""
        await self.stop()
        self._clear_cdp_endpoint()
        log("Browser closed")

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
