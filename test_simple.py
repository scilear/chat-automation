#!/usr/bin/env python3
"""Simple test of browser persistence"""
import sys
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation.config import ChatAutomationConfig
from chat_automation.chatgpt import ChatGPTAutomation
import asyncio
import urllib.request

async def test():
    print("Creating automation...", flush=True)
    config = ChatAutomationConfig.brave_automation()
    auto = ChatGPTAutomation(config)
    
    print("Starting browser...", flush=True)
    await auto.start()
    print(f"Browser started! URL: {auto.page.url}", flush=True)
    
    print("Disconnecting...", flush=True)
    await auto.disconnect()
    print("Disconnected!", flush=True)
    
    # Check if browser is still running
    print("\nChecking browser in 2 seconds...", flush=True)
    await asyncio.sleep(2)
    
    try:
        with urllib.request.urlopen("http://127.0.0.1:9222/json", timeout=2) as response:
            if response.status == 200:
                print("✓ SUCCESS: Browser is still running while Python is alive!", flush=True)
            else:
                print(f"✗ CDP returned status {response.status}", flush=True)
    except Exception as e:
        print(f"✗ Browser was closed: {e}", flush=True)

asyncio.run(test())
print("Python script ending...", flush=True)
