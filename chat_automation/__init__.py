"""
Chat Automation Framework
Automates interactions with AI chat services (ChatGPT, Claude, etc.)
"""

from .base import BrowserAutomation
from .chatgpt import ChatGPTAutomation
from .perplexity import PerplexityAutomation
from .conversation import ConversationManager
from .config import ChatAutomationConfig, DEFAULT_CONFIG
from .manager import ChatManager, SyncChatManager

__version__ = "1.0.0"
__all__ = [
    "BrowserAutomation", 
    "ChatGPTAutomation", 
    "PerplexityAutomation",
    "ConversationManager", 
    "ChatAutomationConfig", 
    "DEFAULT_CONFIG",
    "ChatManager",
    "SyncChatManager"
]
