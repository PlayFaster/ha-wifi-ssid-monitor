#!/bin/sh

# Setup log directory
mkdir -p .reports/devcontainer
LOG_FILE=".reports/devcontainer/post_setup.log"

# Use a subshell to capture all output to the log file
(
    echo "--- Starting Post-Create Setup ---"
    
    echo "Environment: ha-dev-base:latest"

    echo "Refreshing shared config files..."
    if [ -f ".shared/validate-configs/sync_shared_files.sh" ]; then
        RUNNING_FROM_SETUP=1 sh .shared/validate-configs/sync_shared_files.sh
    else
        echo "Warning: sync_shared_files.sh not found — shared files not updated."
    fi

    if [ -f ".pre-commit-config.yaml" ]; then
        echo "Pre-warming pre-commit hook environments..."
        pre-commit install-hooks
    else
        echo "No .pre-commit-config.yaml found — skipping pre-commit pre-warm."
    fi

    # Highly visible success banner
    GREEN='\033[1;32m'
    NC='\033[0m' # No Color
    echo ""
    echo -e "${GREEN}######################################################${NC}"
    echo -e "${GREEN}#                                                    #${NC}"
    echo -e "${GREEN}#   THE DEVCONTAINER IS FULLY SET-UP AND RUNNING!    #${NC}"
    echo -e "${GREEN}#                                                    #${NC}"
    echo -e "${GREEN}######################################################${NC}"
    echo ""
) 2>&1 | tee "$LOG_FILE"

