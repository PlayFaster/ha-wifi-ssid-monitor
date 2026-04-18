#!/bin/sh

# Ensure the directory exists
mkdir -p .reports/devcontainer ;

# 1. Git Configuration (Moved to start to ensure completion)
echo "--- Starting Post-Create Setup ---" | tee .reports/devcontainer/post_setup.log ;
echo "Configuring Git..." | tee -a .reports/devcontainer/post_setup.log ;
git config --global core.fileMode false 2>&1 | tee -a .reports/devcontainer/post_setup.log ;
git config --global core.autocrlf input 2>&1 | tee -a .reports/devcontainer/post_setup.log ;

# 2. System Packages
echo "Installing system packages (apk)..." | tee -a .reports/devcontainer/post_setup.log ;
apk update 2>&1 | tee -a .reports/devcontainer/post_setup.log ;
apk add nodejs npm bash libc6-compat ncurses coreutils 2>&1 | tee -a .reports/devcontainer/post_setup.log ;

# 3. Python Dependencies
echo "Installing Python test dependencies..." | tee -a .reports/devcontainer/post_setup.log ;
pip install -r .validate/requirements_test.txt 2>&1 | tee -a .reports/devcontainer/post_setup.log ;

# 4. Global NPM Tools
echo "Installing global NPM tools..." | tee -a .reports/devcontainer/post_setup.log ;
npm install -g @google/gemini-cli markdown-link-check markdownlint-cli prettier 2>&1 | tee -a .reports/devcontainer/post_setup.log ;

# 5. Gemini CLI Configuration
echo "Configuring Gemini CLI..." | tee -a .reports/devcontainer/post_setup.log ;
# Clean up path by stripping any carriage returns
NODE_ROOT=$(npm root -g | tr -d '\r') ;
REAL_GEMINI_PATH="$NODE_ROOT/@google/gemini-cli/bundle/gemini.js" ;

# Use series of && to avoid if/then/else/fi syntax errors with Windows line endings
[ -f "$REAL_GEMINI_PATH" ] && echo "Found Gemini at: $REAL_GEMINI_PATH" | tee -a .reports/devcontainer/post_setup.log ;
[ -f "$REAL_GEMINI_PATH" ] && sed -i '1s|.*|#!/usr/bin/node|' "$REAL_GEMINI_PATH" 2>&1 | tee -a .reports/devcontainer/post_setup.log ;
[ -f "$REAL_GEMINI_PATH" ] && ln -sf "$REAL_GEMINI_PATH" /usr/local/bin/gemini 2>&1 | tee -a .reports/devcontainer/post_setup.log ;
[ -f "$REAL_GEMINI_PATH" ] && chmod +x /usr/local/bin/gemini 2>&1 | tee -a .reports/devcontainer/post_setup.log ;
[ -f "$REAL_GEMINI_PATH" ] && echo "Gemini CLI configured successfully." | tee -a .reports/devcontainer/post_setup.log ;
[ -f "$REAL_GEMINI_PATH" ] || echo "Warning: gemini.js not found at $REAL_GEMINI_PATH. Manual check required." | tee -a .reports/devcontainer/post_setup.log ;

echo "--- Setup Complete ---" | tee -a .reports/devcontainer/post_setup.log ;
