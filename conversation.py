"""
Conversation management module
"""

import json
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

from .chatgpt import ChatGPTAutomation
from .config import ChatAutomationConfig


@dataclass
class Message:
    """Represents a chat message"""
    role: str
    content: str
    timestamp: Optional[str] = None

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Conversation:
    """Represents a conversation"""
    id: str
    title: str
    messages: List[Message]
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "title": self.title,
            "messages": [asdict(m) for m in self.messages],
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def to_markdown(self) -> str:
        lines = [f"# {self.title}\n", f"*Created: {self.created_at}*\n\n"]
        for msg in self.messages:
            lines.append(f"**{msg.role.upper()}:** {msg.content}\n\n")
        return "".join(lines)


class ConversationManager:
    """Manages chat conversations"""

    def __init__(self, automation: ChatGPTAutomation, storage_dir: str = "./conversations"):
        self.automation = automation
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_conversation(self, filename: Optional[str] = None) -> str:
        """Save current conversation to file"""
        messages = await self.automation.get_conversation_history()
        conv = Conversation(
            id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            title="ChatGPT Conversation",
            messages=[Message(**msg) for msg in messages],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

        if not filename:
            filename = f"conversation_{conv.id}.json"

        filepath = self.storage_dir / filename
        with open(filepath, "w") as f:
            json.dump(conv.to_dict(), f, indent=2)

        return str(filepath)

    async def load_conversation(self, filepath: str) -> Conversation:
        """Load conversation from file"""
        with open(filepath, "r") as f:
            data = json.load(f)
            data["messages"] = [Message(**msg) for msg in data["messages"]]
            return Conversation(**data)

    async def summarize_conversation(self) -> str:
        """Generate a summary of current conversation"""
        messages = await self.automation.get_conversation_history()
        if not messages:
            return "No messages in conversation."

        user_msgs = [m for m in messages if m["role"] == "user"]
        assistant_msgs = [m for m in messages if m["role"] == "assistant"]

        summary = [
            f"**Conversation Summary**",
            f"- Total messages: {len(messages)}",
            f"- User messages: {len(user_msgs)}",
            f"- Assistant responses: {len(assistant_msgs)}",
            "",
            "**Recent topics:**"
        ]

        for msg in user_msgs[-5:]:
            preview = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary.append(f"- {preview}")

        return "\n".join(summary)

    async def export_all_conversations(self) -> List[str]:
        """Export all visible conversations"""
        saved = []
        conversations = await self.automation.list_conversations()

        for conv in conversations:
            title = conv["title"][:30].replace("/", "_").replace(" ", "_")
            filename = f"{title}_{datetime.now().strftime('%Y%m%d')}.json"
            filepath = self.storage_dir / filename

            await conv["element"].click()
            await asyncio.sleep(1)

            messages = await self.automation.get_conversation_history()
            conversation = Conversation(
                id=datetime.now().strftime("%Y%m%d_%H%M%S"),
                title=conv["title"],
                messages=[Message(**msg) for msg in messages],
                created_at=conv.get("date", datetime.now().isoformat()),
                updated_at=datetime.now().isoformat()
            )

            with open(filepath, "w") as f:
                json.dump(conversation.to_dict(), f, indent=2)

            saved.append(str(filepath))

        return saved
