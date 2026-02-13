#!/bin/bash
pkill -f "Brave.*9222" 2>/dev/null
sleep 2
cd /home/fabien/clawd/chat_automation
source .venv/bin/activate

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation import ChatManager
import asyncio

async def test():
    print("Creating ChatManager", flush=True)
    chat = ChatManager()
    print("Ensuring browser", flush=True)
    await chat._ensure_browser()
    print("Browser started", flush=True)
    await chat.close()
    print("Closed", flush=True)

asyncio.run(test())
print("Done", flush=True)
PYEOF

echo "Python script finished"
sleep 2
echo "Checking browser..."
if curl -s http://127.0.0.1:9222/json > /dev/null 2>&1; then
    echo "SUCCESS: Browser is still running!"
else
    echo "FAILED: Browser was closed"
fi