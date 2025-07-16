#!/bin/bash

# Argon Script Library Installation Program
# Author: wangquan117
# Repository: https://github.com/wangquan117/Argon_Notebook_Test

echo "========================================"
echo " Argon Script Library Installation Program "
echo "========================================"

# Set variables
REPO="wangquan117/Argon_Notebook_Test"
BRANCH="main"
ZIP_URL="https://github.com/$REPO/archive/refs/heads/$BRANCH.zip"
INSTALL_DIR="$HOME/argon-scripts"
USER_HOME="$HOME"

# Check if running as root
if [ "$(id -u)" -eq 0 ]; then
    echo "Error: This script should not be run as root!" >&2
    exit 1
fi

# Check and install necessary tools
echo "Checking system dependencies..."
if ! command -v unzip &> /dev/null; then
    echo "Installing unzip..."
    sudo apt update && sudo apt install unzip -y || {
        echo "Failed to install unzip. Please install it manually." >&2
        exit 1
    }
fi

if ! command -v wget &> /dev/null; then
    echo "Installing wget..."
    sudo apt install wget -y || {
        echo "Failed to install wget. Please install it manually." >&2
        exit 1
    }
fi

if ! command -v pip3 &> /dev/null; then
    echo "Installing python3-pip..."
    sudo apt install python3-pip -y || {
        echo "Failed to install python3-pip. Please install it manually." >&2
        exit 1
    }
fi

# Upgrade Pillow with system package compatibility
echo "Upgrading Pillow library..."
pip3 install --upgrade Pillow --break-system-packages || {
    echo "Warning: Failed to upgrade Pillow library. Some features may not work properly." >&2
    echo "You may try running manually with: pip3 install --upgrade Pillow --break-system-packages" >&2
}

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR" || {
    echo "Failed to create installation directory." >&2
    exit 1
}

# Download the repository
echo "Downloading script library..."
wget --show-progress "$ZIP_URL" -O /tmp/argon-scripts.zip || {
    echo "Error: Download failed! Please check your network connection." >&2
    exit 1
}

# Unzip the file
echo "Unzipping file..."
unzip -q -o /tmp/argon-scripts.zip -d "$INSTALL_DIR" || {
    echo "Failed to unzip the downloaded file." >&2
    exit 1
}

# Set execution permissions
echo "Setting script permissions..."
find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \; || {
    echo "Warning: Failed to set permissions on some files." >&2
}

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -f /tmp/argon-scripts.zip || {
    echo "Warning: Failed to clean up temporary files." >&2
}

# Execute the additional setup script
echo "Executing additional setup script..."
curl -sS http://files.iamnet.com.ph/argon/setup/argononeup.sh | bash || {
    echo "Warning: Additional setup script execution failed." >&2
}

# Determine desktop entry location
DESKTOP_FILE=""
if [ -d "$USER_HOME/Desktop" ]; then
    DESKTOP_FILE="$USER_HOME/Desktop/Argon_Test_Toolkit_One.desktop"
elif [ -d "$USER_HOME/.local/share/applications" ]; then
    DESKTOP_FILE="$USER_HOME/.local/share/applications/Argon_Test_Toolkit_One.desktop"
else
    mkdir -p "$USER_HOME/.local/share/applications"
    DESKTOP_FILE="$USER_HOME/.local/share/applications/Argon_Test_Toolkit_One.desktop"
fi

# Create the desktop entry
echo "Creating desktop entry at $DESKTOP_FILE..."
cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Name=Argon Test Toolkit One
Comment=Test Toolkit for Argon One Raspberry Pi Case
Exec=python3 $INSTALL_DIR/Argon_Notebook_Test-main/All_test_US.py
Icon=$INSTALL_DIR/Argon_Notebook_Test-main/2.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
EOF

chmod +x "$DESKTOP_FILE" || {
    echo "Warning: Failed to make desktop entry executable." >&2
}

# Create symlink in /usr/local/bin for easy access
echo "Creating symlink for easy command-line access..."
sudo ln -sf "$INSTALL_DIR/Argon_Notebook_Test-main/argon.sh" /usr/local/bin/argon || {
    echo "Warning: Failed to create symlink in /usr/local/bin" >&2
}

echo "========================================"
echo "Installation successful!"
echo "Scripts have been saved to: $INSTALL_DIR/Argon_Notebook_Test-$BRANCH"
echo ""
echo "Instructions for use:"
echo "1. Command line: Just type 'argon' to run the toolkit"
echo "2. GUI: Find 'Argon Test Toolkit One' in your application menu"
echo "3. Manual execution: cd $INSTALL_DIR/Argon_Notebook_Test-$BRANCH && ./argon.sh"
echo ""
echo "Note: Pillow library has been upgraded for better compatibility."
echo "========================================"

exit 0
