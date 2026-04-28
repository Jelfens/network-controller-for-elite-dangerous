#!/bin/bash

# Elite Dangerous Network Controller - Linux Setup Script

echo "🎮 Elite Dangerous Network Controller - Linux Setup"
echo "=================================================="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install it first:"
    echo "   sudo apt update && sudo apt install python3 python3-venv python3-pip"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check for xdotool
if ! command -v xdotool &> /dev/null; then
    echo ""
    echo "⚠️  xdotool not found (required for keyboard control)"
    echo "   Installing xdotool..."
    sudo apt update
    sudo apt install -y xdotool
    if [ $? -eq 0 ]; then
        echo "✓ xdotool installed successfully"
    else
        echo "❌ Failed to install xdotool. Install manually with:"
        echo "   sudo apt install xdotool"
        exit 1
    fi
fi

echo "✓ xdotool found"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo ""
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "✓ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Find your Elite Dangerous Status.json location:"
echo "      - For Proton/Steam: ~/.steam/root/drive_c/users/steamuser/Saved Games/Frontier Developments/Elite Dangerous/"
echo "      - For native Linux: Check your Elite Dangerous config folder"
echo ""
echo "   2. Run the controller:"
echo "      source .venv/bin/activate"
echo "      python elite-control.py"
echo ""
echo "   3. Open your browser and go to http://localhost:5000"
echo "      (or use your machine's IP for remote access)"
echo ""
echo "🎮 Make sure Elite Dangerous is running in the foreground for keyboard control to work!"
