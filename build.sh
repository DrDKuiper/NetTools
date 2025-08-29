#!/bin/bash

echo "Building NetTools executable..."

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/

# Create executable
echo "Creating executable with PyInstaller..."
pyinstaller NetTools.spec

# Check if build was successful
if [ -f "dist/NetTools.exe" ]; then
    echo "Build successful! Executable created at dist/NetTools.exe"
    echo "File size: $(du -h dist/NetTools.exe | cut -f1)"
else
    echo "Build failed!"
    exit 1
fi

echo "Build complete!"
