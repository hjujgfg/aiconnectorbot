#!/bin/bash

# Exit on error
set -e

# Configuration
PROJECT_DIR=$(pwd)
USER=$(whoami)
GROUP=$(id -gn)
EXEC_START="$PROJECT_DIR/env/bin/python3 bot.py"
SERVICE_NAME="aiconnectorbot.service"
TEMPLATE_FILE="$SERVICE_NAME.template"

echo "🚀 Deploying AI Connector Bot from $PROJECT_DIR..."

# 1. Generate the actual service file from template
echo "⚙️ Generating systemd service file..."
sed -e "s|{{USER}}|$USER|g" \
    -e "s|{{GROUP}}|$GROUP|g" \
    -e "s|{{WORKING_DIR}}|$PROJECT_DIR|g" \
    -e "s|{{EXEC_START}}|$EXEC_START|g" \
    "$TEMPLATE_FILE" > "$SERVICE_NAME"

# 2. Update permissions for security
if [ -f .env ]; then
    echo "🔒 Securing .env file..."
    chmod 600 .env
fi

# 3. Update dependencies
if [ -d "env" ]; then
    echo "📦 Updating python dependencies..."
    ./env/bin/pip install -r requirements.txt --quiet
else
    echo "❌ Virtual environment 'env' not found. Please create it first:"
    echo "   python3 -m venv env && ./env/bin/pip install -r requirements.txt"
    exit 1
fi

# 4. Install the service to systemd
echo "📂 Installing service to /etc/systemd/system/..."
sudo cp "$SERVICE_NAME" "/etc/systemd/system/$SERVICE_NAME"
sudo systemctl daemon-reload

# 5. Restart the bot
echo "🔄 Restarting service..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "✅ Deployment finished successfully!"
echo "📈 Monitor with: sudo journalctl -u $SERVICE_NAME -f"
