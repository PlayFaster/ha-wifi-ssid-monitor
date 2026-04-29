#!/bin/sh

# Setup log directory
mkdir -p .reports/devcontainer
LOG_FILE=".reports/devcontainer/post_setup.log"

# Use a subshell to capture all output to the log file
(
    echo "--- Starting Post-Create Setup ---"
    
    echo "Configuring Git..."
    git config --global core.fileMode false
    git config --global core.autocrlf input

    echo "Environment: ha-dev-base:latest"
    echo "Gemini CLI: $(which gemini || echo 'Not found in path')"

    echo "--- Setup Complete ---"
) 2>&1 | tee "$LOG_FILE"
