#!/bin/bash
set -e

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip and install pip-tools
pip install --upgrade pip
pip install pip-tools

# Function to compile requirements
compile_requirements() {
    echo "Compiling $1..."
    pip-compile --output-file "$1.txt" "$1.in"
}

# Compile all requirements files
for file in *.in; do
    if [ -f "$file" ]; then
        compile_requirements "${file%.*}"
    fi
done

echo "All requirements have been compiled successfully!"
echo "Activate the virtual environment with: source venv/bin/activate"
echo "Install development requirements with: pip install -r requirements/dev.txt"
