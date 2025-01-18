#!/bin/sh

# Enable error handling
set -e

# Function to display messages
log() {
  echo "[$(date +'%Y-%m-%d %H:%M:%S')] $@"
}

log "Starting setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
  log "Python3 is not installed. Installing Python3..."
  sudo apt update
  sudo apt install python3 python3-venv python3-pip -y
else
  log "Python3 is already installed."
fi

# Create a virtual environment
if [ ! -d "venv" ]; then
  log "Creating a virtual environment..."
  python3 -m venv venv
else
  log "Virtual environment already exists."
fi

# Activate the virtual environment
log "Activating the virtual environment..."
. venv/bin/activate

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
  log "Error: requirements.txt not found!"
  exit 1
fi

# Install dependencies
log "Installing dependencies..."
pip install -r requirements.txt

#install pip
pip install mcrcon


# Update the package list
log "Updating package list..."
sudo apt update -y

# Upgrade packages
log "Upgrading packages..."
sudo apt upgrade -y

# Check if app.py exists
if [ ! -f "app.py" ]; then
  log "Error: app.py not found!"
  exit 1
fi

# Run the Flask application
log "Running the Flask application..."
python app.py

log "Setup complete. Flask application is now running."
