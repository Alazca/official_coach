#!/usr/bin/env bash
# Cross-platform installation script for Windows and Linux
# For Windows, run this with Git Bash or WSL

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Detect OS
case "$(uname -s)" in
    Linux*|Darwin*)
        echo "Linux/Unix system detected"
        PYTHON_CMD="python3"
        PIP_CMD="pip3"
        VENV_ACTIVATE="coach/bin/activate"
        ;;
    MINGW*|MSYS*|CYGWIN*)
        echo "Windows system detected"
        PYTHON_CMD="python"
        PIP_CMD="pip"
        VENV_ACTIVATE="coach/Scripts/activate"
        ;;
    *)
        echo "Unknown operating system. This script supports Windows, Linux, and macOS."
        exit 1
        ;;
esac

# Check if Python is installed
if ! command_exists $PYTHON_CMD; then
    echo "$PYTHON_CMD is not installed. Please install Python before running this script."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Python version $PYTHON_VERSION detected"

# Check if pip is installed
if ! command_exists $PIP_CMD; then
    echo "pip is not installed. Installing..."
    $PYTHON_CMD -m ensurepip --default-pip
fi

# Create the virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv coach

# Activate the virtual environment
echo "Activating virtual environment..."
if [[ "$(uname -s)" == MINGW* || "$(uname -s)" == MSYS* || "$(uname -s)" == CYGWIN* ]]; then
    source $VENV_ACTIVATE || . $VENV_ACTIVATE
else
    source $VENV_ACTIVATE
fi

# Verify activation
echo "Using Python from: $(which python)"

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "Virtual environment created and dependencies installed successfully!"
echo ""
echo "To activate the environment in the future:"
echo "• On Linux/Mac: source $VENV_ACTIVATE"
echo "• On Windows: $VENV_ACTIVATE"
