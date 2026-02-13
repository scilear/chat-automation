#!/bin/bash
pkill -f "Brave.*9222" 2>/dev/null
sleep 2

cd /home/fabien/clawd/chat_automation
source .venv/bin/activate

echo "Starting test..." > /tmp/browser_test.log

python3 << 'PYEOF' >> /tmp/browser_test.log 2>&1
import sys
sys.path.insert(0, '/home/fabien/clawd')
from chat_automation.config import ChatAutomationConfig
from chat_automation.chatgpt import ChatGPTAutomation
import asyncio

async def test():
    config = ChatAutomationConfig.brave_automation()
    auto = ChatGPTAutomation(config)
    print('Starting browser', flush=True)
    await auto.start()
    print('Started, disconnecting...', flush=True)
    await auto.disconnect()
    print('Disconnected!', flush=True)

asyncio.run(test())
print('Python script done', flush=True)
PYEOF

echo "Sleeping 2 seconds..." >> /tmp/browser_test.log
sleep 2

echo "Checking browser..." >> /tmp/browser_test.log
if curl -s http://127.0.0.1:9222/json > /dev/null 2>&1; then
    echo "SUCCESS: Browser is still running!" >> /tmp/browser_test.log
else
    echo "FAILED: Browser was closed" >> /tmp/browser_test.log
fi

cat /tmp/browser_test.log