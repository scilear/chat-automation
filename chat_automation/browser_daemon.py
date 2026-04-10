#!/usr/bin/env python3
"""
ChatGPT Browser Daemon
Keeps browser running for fast CLI connections

Usage:
    python browser_daemon.py start  # Start daemon
    python browser_daemon.py stop   # Stop daemon
    python browser_daemon.py status # Check status
"""

import asyncio
import sys
import os
import json
import subprocess
import signal
from pathlib import Path

PID_FILE = Path.home() / ".chat_automation" / "browser_daemon.pid"
CDP_FILE = Path.home() / ".chat_automation" / "browser_cdp.json"


def get_pid():
    """Get daemon PID if running"""
    if PID_FILE.exists():
        try:
            with open(PID_FILE) as f:
                return int(f.read().strip())
        except:
            pass
    return None


def is_running(pid):
    """Check if process is running"""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


def is_cdp_responding():
    """Check if CDP port is responding"""
    try:
        import urllib.request

        req = urllib.request.Request(f"http://127.0.0.1:{CDP_PORT}/json")
        urllib.request.urlopen(req, timeout=2)
        return True
    except:
        return False


def cleanup_stale_daemon():
    """Detect and kill stale daemon process"""
    pid = get_pid()
    if not pid:
        return False

    # Check if process exists
    if not is_running(pid):
        print("Cleaning up stale PID file...")
        PID_FILE.unlink(missing_ok=True)
        CDP_FILE.unlink(missing_ok=True)
        return False

    # Check if CDP is responding
    if is_cdp_responding():
        return True  # Daemon is healthy

    # Stale process - kill it
    print(f"Found stale daemon process (PID: {pid})")
    print("Killing stale process...")
    try:
        os.kill(pid, signal.SIGTERM)
    except:
        pass

    # Wait briefly then force kill if still running
    import time

    time.sleep(1)
    if is_running(pid):
        try:
            os.kill(pid, signal.SIGKILL)
        except:
            pass

    # Clean up files
    PID_FILE.unlink(missing_ok=True)
    CDP_FILE.unlink(missing_ok=True)
    return False


async def start_daemon():
    """Start browser daemon"""
    # Check for stale processes first
    if cleanup_stale_daemon():
        print("Browser daemon already running")
        return

    print("Starting browser daemon...")
    print("(This will keep browser running for fast CLI access)")

    # Start in background
    script = """
import asyncio
import sys
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation import ChatManager
import json
from pathlib import Path

PID_FILE = Path.home() / ".chat_automation" / "browser_daemon.pid"
CDP_FILE = Path.home() / ".chat_automation" / "browser_cdp.json"

async def main():
    chat = ChatManager()
    await chat._ensure_browser()
    await chat._chatgpt.goto("https://chatgpt.com")
    
    # Save PID
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    print("Browser daemon started")
    print("Browser is ready for CLI connections")
    print("Press Ctrl+C to stop")
    
    # Keep running
    while True:
        await asyncio.sleep(60)

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\\nStopping daemon...")
"""

    # Write temporary script
    script_file = Path.home() / ".chat_automation" / "daemon_runner.py"
    with open(script_file, "w") as f:
        f.write(script)

    # Run in background
    proc = subprocess.Popen(
        [sys.executable, str(script_file)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )

    # Wait a moment for it to start
    await asyncio.sleep(3)

    # Check if it started
    pid = get_pid()
    if pid and is_running(pid):
        print("✓ Daemon started successfully")
        print(f"PID: {pid}")
        print("\nNow you can use:")
        print('  ./chatgpt chat "Your message"  (fast!)')
    else:
        print("✗ Failed to start daemon")


def stop_daemon():
    """Stop browser daemon"""
    pid = get_pid()
    if not pid:
        print("Daemon not running")
        return

    if not is_running(pid):
        print("Daemon not running (stale PID file)")
        PID_FILE.unlink(missing_ok=True)
        return

    print(f"Stopping daemon (PID: {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        PID_FILE.unlink(missing_ok=True)
        print("✓ Daemon stopped")
    except Exception as e:
        print(f"✗ Error stopping daemon: {e}")


def check_status():
    """Check daemon status"""
    pid = get_pid()
    if pid and is_running(pid):
        print("✓ Browser daemon is running")
        print(f"  PID: {pid}")
        print("\nCLI commands will connect instantly!")
    else:
        print("✗ Browser daemon is not running")
        print("\nStart it with:")
        print("  python browser_daemon.py start")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python browser_daemon.py start")
        print("  python browser_daemon.py stop")
        print("  python browser_daemon.py status")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "start":
        asyncio.run(start_daemon())
    elif command == "stop":
        stop_daemon()
    elif command == "status":
        check_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
