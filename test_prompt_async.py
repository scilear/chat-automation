#!/home/fabien/clawd/chat_automation/.venv/bin/python3
"""POC: Test prompt_toolkit in async context (the real issue)"""
import asyncio
from prompt_toolkit.shortcuts import checkboxlist_dialog, radiolist_dialog
from prompt_toolkit.application import get_app

# Dummy data
DUMMY_CONVERSATIONS = [
    ("abc123", "Python asyncio patterns"),
    ("def456", "Machine learning basics"),
    ("ghi789", "Docker compose tutorial"),
    ("jkl012", "React hooks explained"),
    ("mno345", "PostgreSQL optimization"),
]

DUMMY_SPACES = [
    ("spc001", "AI Research"),
    ("spc002", "Coding Projects"),
    ("spc003", "Personal Notes"),
]


async def select_conversations_dialog():
    """Multi-select conversations - returns list of IDs"""
    print("\n=== Opening conversation selection dialog ===")
    
    # Use run_async() instead of run() to avoid nested event loop
    result = await checkboxlist_dialog(
        title="Select Conversations",
        text="Press SPACE to toggle, ENTER to confirm:",
        values=DUMMY_CONVERSATIONS,
    ).run_async()
    
    if result is None:
        print("Cancelled")
        return []
    
    print(f"Selected: {result}")
    return result


async def select_action_dialog():
    """Single-select action - returns action string"""
    print("\n=== Opening action selection dialog ===")
    
    result = await radiolist_dialog(
        title="Choose Action",
        text="Select what to do:",
        values=[
            ("open", "Open in browser"),
            ("delete", "Delete selected"),
            ("back", "Back to menu"),
        ]
    ).run_async()
    
    if result is None:
        print("Cancelled")
        return None
    
    print(f"Action: {result}")
    return result


async def main():
    """Simulate the manage_interactive flow"""
    print("=" * 60)
    print("POC: prompt_toolkit async dialog flow")
    print("=" * 60)
    
    # Step 1: Select conversations
    selected_ids = await select_conversations_dialog()
    
    if not selected_ids:
        print("No selection, exiting")
        return
    
    # Step 2: Choose action
    action = await select_action_dialog()
    
    if action:
        print(f"\n✅ Would execute: {action} on {selected_ids}")
    else:
        print("\n❌ No action selected")
    
    print("\n=== POC completed successfully ===")


if __name__ == "__main__":
    asyncio.run(main())
