#!/usr/bin/env python3
import sys
sys.path.insert(0, '/home/fabien/clawd')
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def test():
    print('Starting playwright...', flush=True)
    playwright = await async_playwright().start()
    
    user_data_dir = Path.home() / '.config/BraveSoftware/Brave-Automation'
    print(f'Launching browser...', flush=True)
    
    try:
        browser = await playwright.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            viewport={'width': 1280, 'height': 800},
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-automation',
                '--remote-debugging-port=9222',
                '--no-sandbox',
            ],
        )
        print('Browser launched!', flush=True)
        
        import time
        time.sleep(3)
        print('Closing...', flush=True)
        await browser.close()
    except Exception as e:
        print(f'Error: {e}', flush=True)
        import traceback
        traceback.print_exc()
    
    await playwright.stop()
    print('Done', flush=True)

asyncio.run(test())
