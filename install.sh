#!/bin/bash

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null
then
    echo "Python 3 is not installed. Please install Python 3 before running this script."
    exit 1  # Exit the script with an error code
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null
then
    echo "pip is not installed. Installing..."
    python3 -m ensurepip --default-pip
fi

# Create the virtual environment
python3 -m venv coach 

# Activate the virtual environment
source coach/bin/activate

# Install dependencies
pip install -r requirements.txt

echo "Virtual environment created and dependencies installed successfully!"
echo "Activate the environment with: source coach/bin/activate"

