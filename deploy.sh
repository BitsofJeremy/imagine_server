#!/bin/bash

# Deployment script for Imagine Server Flask Application

# Exit immediately if a command exits with a non-zero status
set -e

# Configuration
APP_DIR="/opt/imagine_server"
VENV_DIR="$APP_DIR/venv"
GITHUB_REPO="https://github.com/BitsofJeremy/imagine_server.git"
BRANCH="main"
SERVICE_NAME="imagineserver"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
USER_NAME="imagineserver"
USER_HOME="/home/$USER_NAME"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
   log "This script must be run as root"
   exit 1
fi

# Create user if it doesn't exist
if ! id "$USER_NAME" &>/dev/null; then
    log "Creating system user $USER_NAME..."
    adduser --system --group --home $USER_HOME $USER_NAME
    chown $USER_NAME:$USER_NAME $USER_HOME
    chmod 750 $USER_HOME
fi

# Ensure application directory exists and set correct ownership
mkdir -p $APP_DIR
chown $USER_NAME:$USER_NAME $APP_DIR

# Navigate to the application directory
cd $APP_DIR

# Pull the latest changes from the Git repository
log "Pulling latest changes from Git repository..."
if [ -d ".git" ]; then
    sudo -u $USER_NAME git fetch origin $BRANCH
    sudo -u $USER_NAME git reset --hard origin/$BRANCH
else
    sudo -u $USER_NAME git clone $GITHUB_REPO .
    sudo -u $USER_NAME git checkout $BRANCH
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    sudo -u $USER_NAME python3 -m venv $VENV_DIR
fi

# Activate virtual environment
source $VENV_DIR/bin/activate

# Install or update dependencies
log "Installing/updating dependencies..."
sudo -u $USER_NAME $VENV_DIR/bin/pip install -r requirements.txt

# Run tests
log "Running tests..."
sudo -u $USER_NAME $VENV_DIR/bin/pytest

# If tests pass, proceed with deployment
if [ $? -eq 0 ]; then
    # Create or update the systemd service file
    log "Creating/updating systemd service file..."
    cat > $SERVICE_FILE << EOL
[Unit]
Description=Imagine Server Flask Application
After=network.target

[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=/bin/bash -c 'set -a; source $APP_DIR/.env; set +a; $VENV_DIR/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app'
Restart=always
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="HOME=$USER_HOME"

[Install]
WantedBy=multi-user.target
EOL

    # Reload systemd to recognize the new service
    log "Reloading systemd..."
    systemctl daemon-reload

    # Enable and restart the service
    log "Enabling and restarting the service..."
    systemctl enable $SERVICE_NAME
    systemctl restart $SERVICE_NAME

    # Check if the service is running
    if systemctl is-active --quiet $SERVICE_NAME; then
        log "Deployment successful. Imagine Server is running."
    else
        log "Error: Imagine Server failed to start. Check the logs with 'journalctl -u $SERVICE_NAME'"
        exit 1
    fi
else
    log "Tests failed. Aborting deployment."
    exit 1
fi

# Deactivate virtual environment
deactivate

log "Deployment completed successfully."