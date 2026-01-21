#!/bin/bash
#
# Install MMG mesh refinement tool for bpy-geometries
#
# This script clones and builds MMG in the vendor/ directory.
# The mmgs binary will be available at vendor/mmg/build/bin/mmgs_O3
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
VENDOR_DIR="$REPO_ROOT/vendor"
MMG_DIR="$VENDOR_DIR/mmg"

echo "Installing MMG for bpy-geometries"
echo "================================="
echo ""

# Check for cmake
if ! command -v cmake &> /dev/null; then
    echo "Error: cmake is required but not installed."
    echo "Install cmake and try again."
    exit 1
fi

# Check for make
if ! command -v make &> /dev/null; then
    echo "Error: make is required but not installed."
    echo "Install make and try again."
    exit 1
fi

# Create vendor directory if needed
mkdir -p "$VENDOR_DIR"

# Clone or update MMG
if [ -d "$MMG_DIR" ]; then
    echo "MMG directory exists, updating..."
    cd "$MMG_DIR"
    git pull
else
    echo "Cloning MMG..."
    cd "$VENDOR_DIR"
    git clone https://github.com/MmgTools/mmg.git
fi

cd "$MMG_DIR"

# Build
echo ""
echo "Building MMG..."
mkdir -p build
cd build

cmake .. -DCMAKE_BUILD_TYPE=Release

# Detect number of cores
if command -v nproc &> /dev/null; then
    JOBS=$(nproc)
elif command -v sysctl &> /dev/null; then
    JOBS=$(sysctl -n hw.ncpu)
else
    JOBS=4
fi

make -j"$JOBS"

# Verify binary exists
MMGS_BIN="$MMG_DIR/build/bin/mmgs_O3"
if [ -f "$MMGS_BIN" ]; then
    echo ""
    echo "Done. MMG installed at:"
    echo "  $MMGS_BIN"
    echo ""
    echo "bpy-geometries will automatically find this binary."
else
    echo ""
    echo "Error: Build completed but mmgs_O3 binary not found."
    echo "Check the build output for errors."
    exit 1
fi
