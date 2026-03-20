#!/usr/bin/env bash
# Setup script for chat_automation virtual environment
# Run this once to initialize the isolated environment

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo "========================================="
echo "Chat Automation Setup"
echo "========================================="
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
    echo "Virtual environment created"
else
    echo "Virtual environment already exists"
fi

# Activate and install dependencies
echo ""
echo "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"

# Install Playwright browsers
echo ""
echo "Installing Playwright browsers (this may take a few minutes)..."
playwright install chromium

echo ""
echo "Installing CLI wrappers to ~/.local/bin..."
LOCAL_BIN="$HOME/.local/bin"
mkdir -p "$LOCAL_BIN"

cat > "$LOCAL_BIN/chatgpt" <<EOF
#!/usr/bin/env bash
set -euo pipefail

REPO="${SCRIPT_DIR}"
VENV="${VENV_DIR}"

if [ ! -d "\$VENV" ]; then
  echo "Missing venv at \$VENV" >&2
  echo "Run: bash \$REPO/setup.sh" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "\$VENV/bin/activate"
export PYTHONPATH="\$REPO\${PYTHONPATH:+:\$PYTHONPATH}"
exec python "\$REPO/chatgpt" "\$@"
EOF

cat > "$LOCAL_BIN/perplexity" <<EOF
#!/usr/bin/env bash
set -euo pipefail

REPO="${SCRIPT_DIR}"
VENV="${VENV_DIR}"

if [ ! -d "\$VENV" ]; then
  echo "Missing venv at \$VENV" >&2
  echo "Run: bash \$REPO/setup.sh" >&2
  exit 1
fi

# shellcheck source=/dev/null
source "\$VENV/bin/activate"
export PYTHONPATH="\$REPO\${PYTHONPATH:+:\$PYTHONPATH}"
exec python "\$REPO/perplexity" "\$@"
EOF

chmod +x "$LOCAL_BIN/chatgpt" "$LOCAL_BIN/perplexity"

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "To activate the environment:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To run examples:"
echo "  cd $SCRIPT_DIR"
echo "  python examples/interactive_chat.py"
echo ""
echo "CLI wrappers installed:"
echo "  $LOCAL_BIN/chatgpt"
echo "  $LOCAL_BIN/perplexity"
echo ""
