#!/bin/bash
set -e

# Configuration
BUILD_DIR="/tmp/tepegoz-build"
SOURCE_DIR="$(pwd)"

echo "--- Preparing build directory: $BUILD_DIR ---"
mkdir -p "$BUILD_DIR"

# update the build copy with only necessary files
rsync -a --delete \
    --include='debian/***' \
    --include='engine/***' \
    --include='grafana/***' \
    --exclude='*' \
    "$SOURCE_DIR/" "$BUILD_DIR/"

# Fix permissions and line endings (crucial for WSL/Windows interop)
echo "--- Normalizing line endings and permissions ---"
find "$BUILD_DIR/debian" -type f -exec dos2unix {} + 2>/dev/null || true

# Ensure rules and maintainer scripts are executable
chmod +x "$BUILD_DIR/debian/rules"
chmod +x "$BUILD_DIR/debian/postinst"
chmod +x "$BUILD_DIR/debian/prerm"
chmod +x "$BUILD_DIR/debian/postrm"
chmod +x "$BUILD_DIR/debian/tepegoz"

# Ensure debhelper config files are NOT executable
chmod -x "$BUILD_DIR/debian/tepegoz-ids.install"
chmod -x "$BUILD_DIR/debian/control"

# Build the package
echo "--- Starting dpkg-buildpackage ---"
cd "$BUILD_DIR"
dpkg-buildpackage -us -uc -b

echo "--- Build Complete ---"
ls -lh ../tepegoz-ids_*.deb
