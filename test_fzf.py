#!/home/fabien/clawd/chat_automation/.venv/bin/python3
"""Test fzf integration - various approaches"""

import subprocess
import os
import sys
import pty
import select

items = [
    {"id": "1", "title": "Option one"},
    {"id": "2", "title": "Option two"},
    {"id": "3", "title": "Option three"},
]

print(f"stdin isatty: {os.isatty(0)}")
print(f"stdout isatty: {os.isatty(1)}")
sys.stdout.flush()

lines = [f"{item['title']}\t{item['id']}" for item in items]
input_data = "\n".join(lines)

print("\n=== Test 1: Basic Popen (likely fails) ===")
sys.stdout.flush()

proc = subprocess.Popen(
    ["fzf", "--multi", "--header", "Select (TAB: select | ENTER: confirm)"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
stdout, stderr = proc.communicate(input=input_data)
print(f"Returncode: {proc.returncode}")
print(f"stdout: '{stdout.strip()}'")
if stderr:
    print(f"stderr: '{stderr.strip()}'")
sys.stdout.flush()

print("\n=== Test 2: PTY approach ===")
sys.stdout.flush()

master, slave = pty.openpty()
proc = subprocess.Popen(
    ["fzf", "--multi"],
    stdin=slave,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)
os.close(slave)

# Write input to fzf
os.write(master, input_data.encode())
os.close(master)

# Read output with timeout
select_timeout = 2
data = b""
while True:
    ready, _, _ = select.select([proc.stdout], [], [], select_timeout)
    if not ready:
        print("Timeout waiting for fzf")
        proc.kill()
        break
    chunk = proc.stdout.read(1024)
    if not chunk:
        break
    data += chunk

proc.wait()
stdout = data.decode()
print(f"Returncode: {proc.returncode}")
print(f"stdout: '{stdout.strip()}'")
sys.stdout.flush()

print("\n=== Test 3: Just use stdin as file (no subprocess) ===")
print("This test just shows items, you enter number manually:")
for i, item in enumerate(items, 1):
    print(f"  {i}. {item['title']}")
selection = input("Enter numbers (1,3): ").strip()
print(f"You selected: {selection}")
