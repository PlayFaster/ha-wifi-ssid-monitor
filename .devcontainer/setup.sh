#!/bin/sh
set -e

echo "--- Starting Post-Create Setup ---"

# 1. System Packages
echo "Installing system packages (apk)..."
apk update
apk add nodejs npm bash libc6-compat ncurses coreutils

# 2. Python Dependencies
echo "Installing Python test dependencies..."
pip install -r .validate/requirements_test.txt

# 3. Global NPM Tools
echo "Installing global NPM tools..."
npm install -g @google/gemini-cli markdown-link-check markdownlint-cli prettier

# 4. Gemini CLI Configuration
echo "Configuring Gemini CLI..."

# Find the real bundle file (handles path variations in Alpine/Node)
REAL_GEMINI_PATH=$(find /usr/local/lib/node_modules /usr/lib/node_modules -name "gemini.js" 2>/dev/null | head -n 1)

if [ -n "$REAL_GEMINI_PATH" ]; then
    echo "Found Gemini at: $REAL_GEMINI_PATH"
    # Fix the shebang to use Alpine's node path directly
    sed -i '1s|.*|#!/usr/bin/node|' "$REAL_GEMINI_PATH"
    # Create the global symlink
    ln -sf "$REAL_GEMINI_PATH" /usr/local/bin/gemini
    chmod +x /usr/local/bin/gemini
    echo "Gemini CLI configured successfully."
else
    echo "Warning: gemini.js not found. Manual check required."
fi

# 5. Git Configuration
echo "Configuring Git..."
git config --global core.fileMode false
git config --global core.autocrlf input

echo "--- Setup Complete ---"
