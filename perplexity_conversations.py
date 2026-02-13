"""
Perplexity Conversation Management Module

Provides functionality to:
- List conversations from perplexity.ai/library
- List spaces from perplexity.ai/spaces
- Delete conversations
- Move conversations to spaces
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum

from .base import BrowserAutomation
from .config import ChatAutomationConfig
from .verbose import log


class ConversationType(Enum):
    CHAT = "chat"
    SEARCH = "search"


@dataclass
class PerplexityConversation:
    id: str
    title: str
    type: ConversationType
    url: str
    preview: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    space_id: Optional[str] = None
    space_name: Optional[str] = None


@dataclass
class PerplexitySpace:
    id: str
    name: str
    url: str
    description: Optional[str] = None
    conversation_count: int = 0
    created_at: Optional[str] = None


@dataclass
class SelectionState:
    selected_ids: List[str] = field(default_factory=list)
    selection_mode: bool = False


class PerplexityConversations(BrowserAutomation):
    """Manages Perplexity conversations and spaces via browser automation"""

    def __init__(self, config: Optional[ChatAutomationConfig] = None):
        super().__init__(config)
        self._selection_state = SelectionState()
        self._connected = False

    async def ensure_connection(self):
        """Start browser connection if not already connected"""
        if not self._connected:
            await self.start()
            self._connected = True

    async def is_logged_in(self) -> bool:
        """Check if logged into Perplexity"""
        try:
            await self.page.wait_for_selector("[data-testid='user-menu'], button[aria-label*='profile'], nav", timeout=5000)
            login_btn = await self.page.query_selector("button:has-text('Sign In'), a:has-text('Sign In')")
            return login_btn is None
        except:
            return False

    async def login(self) -> bool:
        """Navigate to login page"""
        await self.goto(self.config.perplexity_url)
        await self.wait_for_load_state("networkidle")
        return True

    async def close(self):
        """Close browser connection"""
        if self._connected:
            await self.stop()
            self._connected = False

    async def _navigate_if_needed(self, url: str) -> bool:
        """Navigate to URL only if not already there"""
        current = self.page.url if self.page else ""
        if current == url or current.startswith(url + "?"):
            log(f"Already on {url}, skipping navigation")
            return True

        await self.goto(url)
        await self.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        return True

    async def list_conversations_via_fetch(self, limit: int = 30) -> List[PerplexityConversation]:
        """Fetch conversations via browser fetch API - bypasses auth"""
        conversations = []
        try:
            await self.ensure_connection()

            await self._navigate_if_needed("https://www.perplexity.ai/library")
            await asyncio.sleep(2)

            result = await self.page.evaluate('''async (limit) => {
                try {
                    const response = await fetch(
                        "https://www.perplexity.ai/rest/thread/list_ask_threads?version=2.18&source=default",
                        {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ limit: limit, ascending: false, offset: 0, search_term: "" })
                        }
                    );
                    if (response.ok) {
                        return { success: true, text: await response.text() };
                    }
                    return { success: false, error: "HTTP " + response.status };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
            ''', arg=limit)

            if result and result.get('success'):
                import json
                threads = json.loads(result.get('text', '[]'))
                for thread in threads:
                    title = thread.get('last_query', '') or thread.get('title', 'Untitled')
                    if len(title) > 40:
                        title = title[:40] + "..."
                    conv = PerplexityConversation(
                        id=thread.get('uuid', ''),
                        title=title,
                        type=ConversationType.CHAT,
                        url=f"https://www.perplexity.ai/chat/{thread.get('uuid', '')}",
                        preview='',
                        created_at=thread.get('created_at', ''),
                        updated_at=thread.get('last_query_datetime', '')
                    )
                    conversations.append(conv)
            else:
                log(f"Fetch error: {result.get('error', 'Unknown')}")

        except Exception as e:
            log(f"Error fetching conversations: {e}")

        return conversations

    async def list_spaces_via_fetch(self, limit: int = 30) -> List[PerplexitySpace]:
        """Fetch spaces via browser fetch API - bypasses auth"""
        spaces = []
        try:
            await self.ensure_connection()

            # Navigate to spaces page first (needed for auth cookies)
            await self._navigate_if_needed("https://www.perplexity.ai/spaces")
            await asyncio.sleep(2)

            result = await self.page.evaluate('''async (limit) => {
                try {
                    const response = await fetch(
                        "https://www.perplexity.ai/rest/collections/list_user_collections?limit=" + limit + "&offset=0&version=2.18&source=default",
                        { method: "GET" }
                    );
                    if (response.ok) {
                        const text = await response.text();
                        return { success: true, text: text };
                    }
                    return { success: false, error: "HTTP " + response.status };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
            ''', arg=limit)

            if result and result.get('success'):
                import json
                collections = json.loads(result.get('text', '[]'))
                for coll in collections:
                    space = PerplexitySpace(
                        id=coll.get('uuid', ''),
                        name=coll.get('title', 'Unnamed Space'),
                        description=coll.get('description', ''),
                        url=f"https://www.perplexity.ai/space/{coll.get('uuid', '')}",
                        conversation_count=coll.get('thread_count', 0),
                        created_at=coll.get('updated_datetime', '')
                    )
                    spaces.append(space)
            else:
                log(f"Fetch error: {result.get('error', 'Unknown')}")

        except Exception as e:
            log(f"Error fetching spaces: {e}")

        return spaces

    async def list_conversations(self, limit: int = 30) -> List[PerplexityConversation]:
        """Get conversations via browser fetch API"""
        return await self.list_conversations_via_fetch(limit=limit)

    async def open_conversation(self, conversation_id: str) -> bool:
        """Open a conversation by ID"""
        await self.ensure_connection()
        url = f"https://www.perplexity.ai/chat/{conversation_id}"
        return await self._navigate_if_needed(url)

    async def open_space(self, space_id: str) -> bool:
        """Open a space by ID"""
        await self.ensure_connection()
        url = f"https://www.perplexity.ai/space/{space_id}"
        return await self._navigate_if_needed(url)

    async def list_spaces(self, limit: int = 30) -> List[PerplexitySpace]:
        """Get spaces via browser fetch API"""
        return await self.list_spaces_via_fetch(limit=limit)

    def clear_selection(self):
        """Clear conversation selection state"""
        self._selection_state = SelectionState()

    def select_conversation(self, conversation_id: str):
        """Add conversation to selection"""
        if conversation_id not in self._selection_state.selected_ids:
            self._selection_state.selected_ids.append(conversation_id)
            self._selection_state.selection_mode = True

    def deselect_conversation(self, conversation_id: str):
        """Remove conversation from selection"""
        if conversation_id in self._selection_state.selected_ids:
            self._selection_state.selected_ids.remove(conversation_id)
        if not self._selection_state.selected_ids:
            self._selection_state.selection_mode = False

    def toggle_selection(self, conversation_id: str):
        """Toggle conversation selection"""
        if conversation_id in self._selection_state.selected_ids:
            self.deselect_conversation(conversation_id)
        else:
            self.select_conversation(conversation_id)

    def get_selected_ids(self) -> List[str]:
        """Get currently selected conversation IDs"""
        return self._selection_state.selected_ids.copy()

    def is_in_selection_mode(self) -> bool:
        """Check if selection mode is active"""
        return self._selection_state.selection_mode

    async def delete_conversation_via_api(self, conversation_id: str) -> bool:
        """Delete a conversation via browser fetch API"""
        try:
            print(f"[DEBUG] Attempting to delete conversation: {conversation_id}")
            await self.ensure_connection()

            result = await self.page.evaluate('''async (thread_id) => {
                try {
                    const response = await fetch(
                        "https://www.perplexity.ai/rest/thread/delete",
                        {
                            method: "POST",
                            headers: { 
                                "Content-Type": "application/json",
                                "Accept": "application/json"
                            },
                            body: JSON.stringify({ thread_id: thread_id })
                        }
                    );
                    const responseText = await response.text();
                    if (response.ok) {
                        return { success: true, response: responseText };
                    }
                    return { success: false, error: "HTTP " + response.status + ": " + responseText };
                } catch (e) {
                    return { success: false, error: e.message };
                }
            }
            ''', arg=conversation_id)

            if result and result.get('success'):
                log(f"Deleted conversation: {conversation_id}")
                return True
            else:
                error_msg = result.get('error', 'Unknown') if result else 'No result'
                print(f"[ERROR] Delete failed for {conversation_id}: {error_msg}")
                return False

        except Exception as e:
            log(f"Error deleting conversation: {e}")
            return False
