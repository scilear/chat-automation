#!/usr/bin/env python3
"""Test if browser stays running without exiting Python"""
import sys
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation import ChatManager
import asyncio
import urllib.request
import time

async def test():
    print("Creating ChatManager...")
    chat = ChatManager()
    
    print("Starting browser...")
    await chat._ensure_browser()
    print("✓ Browser started")
    
    print("Calling close()...")
    await chat.close()
    print("✓ close() returned")
    
    # Keep Python running for a bit
    print("Waiting 5 seconds before exiting Python...")
    await asyncio.sleep(5)
    
    # Check if browser is still running while Python is still running
    print("\n=== Checking browser while Python is still running ===")
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2) as response:
            if response.status == 200:
                print("✓ Browser is still running!")
            else:
                print(f"✗ CDP returned status {response.status}")
    except Exception as e:
        print(f"✗ Browser was closed: {e}")

asyncio.run(test())

# Now Python is about to exit
print("\n=== Python about to exit ===")
print("Sleeping 2 more seconds...")
time.sleep(2)

print("\n=== Final check before exit ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2) as response:
        if response.status == 200:
            print("✓ Browser still running before Python exit!")
        else:
            print(f"✗ CDP returned status {response.status}")
except Exception as e:
    print(f"✗ Browser closed: {e}")
