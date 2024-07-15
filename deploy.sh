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
DOMAIN="imagineserver.home.test"  # Add this line for domain configuration

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check if script is run as root
if [[ $EUID -ne 0 ]]; then
   log "This script must be run as root"
   exit 1
fi

# Function to install dependencies
install_dependencies() {
    log "Installing dependencies..."
    apt-get update
    apt-get install -y python3 python3-venv python3-pip nginx
}

# Function to create user and set up directories
setup_user_and_directories() {
    log "Setting up user and directories..."
    if ! id "$USER_NAME" &>/dev/null; then
        adduser --system --group --home $USER_HOME $USER_NAME
        chown $USER_NAME:$USER_NAME $USER_HOME
        chmod 750 $USER_HOME
    fi

    mkdir -p $APP_DIR
    chown $USER_NAME:$USER_NAME $APP_DIR
}

# Function to clone or update repository
clone_or_update_repo() {
    log "Cloning or updating repository..."
    if [ -d "$APP_DIR/.git" ]; then
        cd $APP_DIR
        sudo -u $USER_NAME git fetch origin $BRANCH
        sudo -u $USER_NAME git reset --hard origin/$BRANCH
    else
        sudo -u $USER_NAME git clone $GITHUB_REPO $APP_DIR
        cd $APP_DIR
        sudo -u $USER_NAME git checkout $BRANCH
    fi
}

# Function to set up virtual environment and install requirements
setup_venv() {
    log "Setting up virtual environment..."
    if [ ! -d "$VENV_DIR" ]; then
        sudo -u $USER_NAME python3 -m venv $VENV_DIR
    fi
    sudo -u $USER_NAME $VENV_DIR/bin/pip install -r $APP_DIR/requirements.txt
}

# Function to create or update systemd service
create_systemd_service() {
    log "Creating systemd service..."
    cat > $SERVICE_FILE << EOL
[Unit]
Description=Imagine Server Flask Application
After=network.target

[Service]
User=$USER_NAME
Group=$USER_NAME
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
Restart=always
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOL

    systemctl daemon-reload
    systemctl enable $SERVICE_NAME
    systemctl restart $SERVICE_NAME
}

# Function to set up Nginx
setup_nginx() {
    log "Setting up Nginx..."
    cat > /etc/nginx/sites-available/imagineserver << EOL
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

    ln -sf /etc/nginx/sites-available/imagineserver /etc/nginx/sites-enabled/
    nginx -t && systemctl reload nginx
}

# Function to run tests
run_tests() {
    log "Running tests..."
    sudo -u $USER_NAME $VENV_DIR/bin/pytest $APP_DIR
}

# Function to update application
update_app() {
    log "Updating application..."
    clone_or_update_repo
    setup_venv
    run_tests
    systemctl restart $SERVICE_NAME
    log "Update completed successfully."
}

# Main deployment function
deploy() {
    install_dependencies
    setup_user_and_directories
    clone_or_update_repo
    setup_venv
    create_systemd_service
    setup_nginx
    run_tests
    log "Deployment completed successfully."
}

# Check for update flag
if [ "$1" == "--update" ]; then
    update_app
else
    deploy
fi

log "Script execution completed."