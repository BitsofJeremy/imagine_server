#!/bin/bash

# Deployment script for Imagine Server Flask Application

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
APP_DIR="/path/to/your/flask/app"
VENV_DIR="$APP_DIR/venv"
GITHUB_REPO="https://github.com/yourusername/imagine-server.git"
BRANCH="main"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Navigate to the application directory
cd $APP_DIR

# Pull the latest changes from the Git repository
log "Pulling latest changes from Git repository..."
git fetch origin $BRANCH
git reset --hard origin/$BRANCH

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install or update dependencies
log "Installing/updating dependencies..."
pip install -r requirements.txt

# Run tests
log "Running tests..."
pytest

# If tests pass, proceed with deployment
if [ $? -eq 0 ]; then
    # Restart the Flask application service
    log "Restarting Imagine Server service..."
    sudo systemctl restart imagineserver.service

    # Check if the service is running
    if sudo systemctl is-active --quiet imagineserver.service; then
        log "Deployment successful. Imagine Server is running."
    else
        log "Error: Imagine Server failed to start. Check the logs with 'sudo journalctl -u imagineserver.service'"
        exit 1
    fi
else
    log "Tests failed. Aborting deployment."
    exit 1
fi

# Deactivate virtual environment
deactivate

log "Deployment completed successfully."