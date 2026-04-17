#!/bin/bash
# Golf Modeling Suite - Quick Install Script
# Usage: curl -fsSL https://golf-suite.io/install.sh | bash
#
# SECURITY / THREAT MODEL
# -----------------------
# This script installs from the local checkout (pip install .) rather
# than from PyPI, so supply-chain risk is bounded to the state of this
# repository on your machine.
#
# pipx (preferred) creates an isolated virtualenv so the package and
# its transitive dependencies cannot pollute system or user site-packages.
#
# pip3 installs into the active environment without hash verification.
# If you require a reproducible, hash-pinned install run:
#   pip install --require-hashes -r requirements.lock
# and review requirements.lock before running.
#
# To verify the source before installing, inspect the diff since the
# last release tag:
#   git log --oneline $(git describe --tags --abbrev=0)..HEAD
#
# This script does NOT download binaries from the internet; all package
# resolution happens through your configured pip index.

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║         Golf Modeling Suite - Installation Script             ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo

# Detect OS
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected: $OS $ARCH"

# Check for Python 3.11+
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PY_MAJOR=$(echo $PY_VERSION | cut -d. -f1)
    PY_MINOR=$(echo $PY_VERSION | cut -d. -f2)

    if [ "$PY_MAJOR" -ge 3 ] && [ "$PY_MINOR" -ge 11 ]; then
        echo "✓ Python $PY_VERSION found"
    else
        echo "✗ Python 3.11+ required (found $PY_VERSION)"
        echo "  Please install Python 3.11 or newer"
        exit 1
    fi
else
    echo "✗ Python 3 not found"
    echo "  Please install Python 3.11 or newer"
    exit 1
fi

# Check for pipx (recommended) or pip
if command -v pipx &> /dev/null; then
    echo "✓ pipx found - using isolated installation"
    INSTALL_CMD="pipx install ."
elif command -v pip3 &> /dev/null; then
    echo "⚠ pipx not found - using pip (consider installing pipx)"
    INSTALL_CMD="pip3 install ."
else
    echo "✗ Neither pipx nor pip found"
    exit 1
fi

echo
echo "Installing Golf Modeling Suite..."
echo "  Command: $INSTALL_CMD"
echo

$INSTALL_CMD

echo
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                    Installation Complete!                     ║"
echo "╠═══════════════════════════════════════════════════════════════╣"
echo "║                                                               ║"
echo "║   To start:   upstream-drift                                      ║"
echo "║   Help:       upstream-drift --help                               ║"
echo "║                                                               ║"
echo "║   The app will open in your browser at localhost:8000         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
