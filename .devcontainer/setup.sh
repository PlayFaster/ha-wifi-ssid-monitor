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

    echo "Refreshing .validate/ config files from shared..."
    if [ -d ".shared/validate-configs" ]; then
        cp .shared/validate-configs/.yamllint .validate/
        cp .shared/validate-configs/.markdownlint.json .validate/
        cp .shared/validate-configs/.prettierrc.js .validate/
        cp .shared/validate-configs/ha_manifest_schema.json .validate/
        cp .shared/validate-configs/hacs_schema.json .validate/
        echo ".validate/ refreshed."
    else
        echo "Warning: .shared/validate-configs not found — .validate/ not updated."
    fi

    echo "Pre-warming pre-commit hook environments..."
    pre-commit install-hooks

    echo "--- Setup Complete ---"
) 2>&1 | tee "$LOG_FILE"
