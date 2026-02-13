#!/usr/bin/env python3
"""Test if browser stays running after close()"""
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

# Run the test
asyncio.run(test())
print("✓ Script completed")

# Check if browser is still running
time.sleep(2)
print("\n=== Checking browser status ===")
try:
    with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2) as response:
        if response.status == 200:
            print("✓ SUCCESS: Browser is still running!")
        else:
            print(f"✗ CDP returned status {response.status}")
except Exception as e:
    print(f"✗ FAILED: Browser was closed")
    print(f"   Error: {e}")
