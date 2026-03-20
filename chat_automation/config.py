"""
Configuration for chat automation
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ChatAutomationConfig:
    """Configuration for chat automation"""
    headless: bool = False
    browser_type: str = "chromium"
    browser_channel: Optional[str] = None
    browser_executable_path: Optional[str] = None
    browser_args: Optional[list] = None
    timeout: int = 30000
    user_data_dir: Optional[str] = None

    chatgpt_url: str = "https://chatgpt.com"
    claude_url: str = "https://claude.ai"
    deepseek_url: str = "https://chat.deepseek.com"
    perplexity_url: str = "https://www.perplexity.ai"

    @classmethod
    def brave(cls, profile_directory: Optional[str] = None, user_data_dir: Optional[str] = None) -> "ChatAutomationConfig":
        """Create config for Brave browser"""
        browser_args = None
        browser_channel = "brave"
        executable_path = "/usr/bin/brave-browser"

        if user_data_dir:
            browser_args = [f"--profile-directory=Automation Profile"]
        elif profile_directory:
            browser_args = [f"--profile-directory={profile_directory}"]

        return cls(
            headless=False,
            browser_type="chromium",
            browser_channel=browser_channel,
            browser_executable_path=executable_path,
            browser_args=browser_args,
            timeout=60000,
            user_data_dir=user_data_dir,
        )

    @classmethod
    def brave_automation(cls) -> "ChatAutomationConfig":
        """Create config for Brave browser with separate automation profile"""
        automation_dir = os.path.expanduser("~/.config/BraveSoftware/Brave-Automation")
        os.makedirs(automation_dir, exist_ok=True)

        return cls(
            headless=False,
            browser_type="chromium",
            browser_channel="brave",
            browser_executable_path="/usr/bin/brave-browser",
            timeout=60000,
            user_data_dir=automation_dir,
        )

    @classmethod
    def chromium(cls, user_data_dir: Optional[str] = None) -> "ChatAutomationConfig":
        """Create config for Chromium browser"""
        return cls(
            headless=False,
            browser_type="chromium",
            browser_channel="chromium",
            timeout=60000,
            user_data_dir=user_data_dir,
        )

    @classmethod
    def from_env(cls) -> "ChatAutomationConfig":
        """Load config from environment variables"""
        browser = os.getenv("CHAT_AUTO_BROWSER", "chromium").lower()
        if browser == "brave":
            return cls.brave(os.getenv("CHAT_AUTO_USER_DATA", None))
        return cls.chromium(os.getenv("CHAT_AUTO_USER_DATA", None))


DEFAULT_CONFIG = ChatAutomationConfig()
