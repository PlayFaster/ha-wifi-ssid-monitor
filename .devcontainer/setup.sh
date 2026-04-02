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
npm install -g @google/gemini-cli markdown-link-check

# 4. Gemini CLI Configuration
# Fix shebang for node environments and ensure symlink exists
echo "Configuring Gemini CLI..."
sed -i '1s|.*|#!/usr/bin/node|' /usr/local/lib/node_modules/@google/gemini-cli/bin/gemini.js
ln -sf /usr/local/lib/node_modules/@google/gemini-cli/bin/gemini.js /usr/local/bin/gemini

echo "--- Setup Complete ---"
