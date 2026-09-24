#!/bin/bash
# NestExecutor Build Script for Windows
# Cross-compilation setup

set -e

echo "═══════════════════════════════════════════════════════════"
echo "  NestExecutor Windows Builder"
echo "═══════════════════════════════════════════════════════════"
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/WindowsExecutor"
OUTPUT_DIR="$PROJECT_DIR/bin/Release/net6.0-windows"

# Check if .NET SDK is installed
if ! command -v dotnet &> /dev/null; then
    echo "[ERROR] .NET SDK not found. Install from: https://dotnet.microsoft.com/download"
    exit 1
fi

echo "[*] .NET SDK version: $(dotnet --version)"
echo ""

# Restore dependencies
echo "[*] Restoring NuGet packages..."
dotnet restore "$PROJECT_DIR/NestExecutor.csproj"

# Build
echo "[*] Building..."
dotnet build "$PROJECT_DIR/NestExecutor.csproj" --configuration Release

# Copy to output
mkdir -p "$OUTPUT_DIR"
cp "$PROJECT_DIR/bin/Release/net6.0-windows/NestExecutor.dll" "$OUTPUT_DIR/" 2>/dev/null || true
cp "$PROJECT_DIR/bin/Release/net6.0-windows/NestExecutor.exe" "$OUTPUT_DIR/" 2>/dev/null || true

echo ""
echo "[+] Build completed!"
echo "[+] Output: $OUTPUT_DIR"
echo ""
echo "To run:"
echo "  cd $OUTPUT_DIR"
echo "  ./NestExecutor.exe"
echo ""
