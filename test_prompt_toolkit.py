#!/home/fabien/clawd/chat_automation/.venv/bin/python3
"""POC: Test prompt_toolkit for interactive selection using dialogs"""
from prompt_toolkit.shortcuts import checkboxlist_dialog

# Dummy conversation data
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


def test_checkbox_dialog():
    """Test checkboxlist_dialog with dummy data"""
    print("=" * 60)
    print("Testing prompt_toolkit checkbox dialog")
    print("=" * 60)

    # Test conversations - select multiple
    result = checkboxlist_dialog(
        title="Manage Perplexity Conversations",
        text="Select conversations (SPACE to toggle, ENTER to confirm):",
        values=DUMMY_CONVERSATIONS,
    ).run()

    if result:
        print(f"\n✅ Selected conversations: {result}")
    else:
        print("\n❌ Cancelled or no selection")

    # Test spaces - select multiple
    result = checkboxlist_dialog(
        title="Manage Perplexity Spaces",
        text="Select spaces (SPACE to toggle, ENTER to confirm):",
        values=DUMMY_SPACES,
    ).run()

    if result:
        print(f"\n✅ Selected spaces: {result}")
    else:
        print("\n❌ Cancelled or no selection")

    return result


if __name__ == "__main__":
    test_checkbox_dialog()
    print("\n✅ prompt_toolkit POC completed successfully!")
