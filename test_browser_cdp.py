#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/fabien/clawd')
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test():
    print("Starting playwright...")
    playwright = await async_playwright().start()
    
    user_data_dir = Path.home() / ".config/BraveSoftware/Brave-Automation"
    print(f"User data dir: {user_data_dir}")
    
    print("Launching browser...")
    browser = await playwright.chromium.launch_persistent_context(
        user_data_dir=str(user_data_dir),
        headless=False,
        viewport={"width": 1280, "height": 800},
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-automation",
            "--remote-debugging-port=9222",
            "--no-sandbox",
        ],
    )
    
    print("Browser launched! Checking CDP...")
    
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:9222/json", timeout=2) as response:
            if response.status == 200:
                print("✓ CDP is responding!")
    except Exception as e:
        print(f"✗ CDP error: {e}")
    
    await browser.close()
    await playwright.stop()
    print("Done")

asyncio.run(test())
