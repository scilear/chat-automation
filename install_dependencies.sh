#!/bin/bash
# Install dependencies for Chat Automation tools
# Run: bash install_dependencies.sh

set -e

echo "📦 Installing Chat Automation dependencies..."

# Core Python dependencies (already in requirements.txt)
echo "Python packages..."
pip install -r requirements.txt 2>/dev/null || pip3 install -r requirements.txt 2>/dev/null || true

# Install prompt_toolkit for interactive TUI
echo "🔧 Installing prompt_toolkit..."
pip install prompt_toolkit 2>/dev/null || pip3 install prompt_toolkit 2>/dev/null || true

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
python -m playwright install chromium 2>/dev/null || python3 -m playwright install chromium 2>/dev/null || true

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Available tools:"
echo "  ./perplexity manage    # Interactive conversation manager"
echo "  ./chatgpt manage      # Interactive conversation manager"
