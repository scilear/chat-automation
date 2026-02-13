#!/home/fabien/clawd/chat_automation/.venv/bin/python3
"""Robust numbered input for conversation management - no TTY needed"""

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


def select_items(items, title="Select items"):
    """Numbered input selection - works without TTY"""
    print(f"\n{title}")
    print("=" * 60)
    
    for i, (key, display) in enumerate(items, 1):
        print(f"  {i}. {display}")
    
    print("\nEnter numbers separated by spaces (e.g., '1 3 5'), or:")
    print("  - 'a' or 'all' to select all")
    print("  - 'q' or 'c' to cancel")
    
    while True:
        try:
            selection = input("\nSelection: ").strip().lower()
            
            if selection in ['q', 'c', 'cancel', 'quit']:
                print("Cancelled")
                return []
            
            if selection in ['a', 'all']:
                print(f"Selected all {len(items)} items")
                return [key for key, _ in items]
            
            # Parse numbers
            indices = []
            for num_str in selection.split():
                try:
                    idx = int(num_str) - 1
                    if 0 <= idx < len(items):
                        indices.append(idx)
                    else:
                        print(f"  ⚠️  Invalid number: {num_str} (1-{len(items)})")
                except ValueError:
                    print(f"  ⚠️  Not a number: {num_str}")
            
            if indices:
                selected = [items[i][0] for i in indices]
                print(f"\n✅ Selected {len(selected)} item(s): {', '.join(str(s) for s in selected)}")
                return selected
            else:
                print("  No valid selection, try again")
                
        except KeyboardInterrupt:
            print("\nCancelled")
            return []
        except EOFError:
            # No TTY available
            print("\n❌ No interactive input available")
            return []


def test_numbered_selection():
    """Test numbered selection with dummy data"""
    print("=" * 60)
    print("Testing numbered input selection")
    print("=" * 60)
    
    # Test conversations
    selected = select_items(
        DUMMY_CONVERSATIONS,
        title="Manage Perplexity Conversations"
    )
    
    print(f"\nSelected: {selected}")
    
    # Test spaces
    selected = select_items(
        DUMMY_SPACES,
        title="Manage Perplexity Spaces"
    )
    
    print(f"\nSelected: {selected}")
    
    return selected


if __name__ == "__main__":
    test_numbered_selection()
    print("\n✅ Numbered input POC completed!")
