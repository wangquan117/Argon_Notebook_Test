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

# Check and install necessary tools
if ! command -v unzip &> /dev/null; then
    echo "Installing unzip..."
    sudo apt update
    sudo apt install unzip -y
fi

# Create installation directory
echo "Creating installation directory: $INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

# Download the repository
echo "Downloading script library..."
wget -q --show-progress "$ZIP_URL" -O /tmp/argon-scripts.zip

# Check if the download was successful
if [ $? -ne 0 ]; then
    echo "Error: Download failed! Please check your network connection."
    exit 1
fi

# Unzip the file
echo "Unzipping file..."
unzip -q -o /tmp/argon-scripts.zip -d "$INSTALL_DIR"

# Set execution permissions
echo "Setting script permissions..."
find "$INSTALL_DIR" -name "*.sh" -exec chmod +x {} \;

# Clean up temporary files
echo "Cleaning up temporary files..."
rm /tmp/argon-scripts.zip

# Execute the additional setup script
echo "Executing additional setup script..."
curl http://files.iamnet.com.ph/argon/setup/argononeup.sh | bash

echo "========================================"
echo "Installation successful!"
echo "Scripts have been saved to: $INSTALL_DIR/Argon_Notebook_Test-$BRANCH"
echo ""
echo "Instructions for use:"
echo "1. Navigate to directory: cd $INSTALL_DIR/Argon_Notebook_Test-$BRANCH"
echo "2. Run the main script: ./argon.sh"
echo "========================================"
