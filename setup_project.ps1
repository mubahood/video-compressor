# VideoPress Project Setup Script for Windows
# Run this after installing Python and FFmpeg

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  VideoPress - Project Setup Script" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/5] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "  ✗ Python not found! Please install Python and add to PATH." -ForegroundColor Red
    Write-Host "    Download from: https://www.python.org/downloads/" -ForegroundColor Gray
    exit 1
}

# Check FFmpeg
Write-Host "[2/5] Checking FFmpeg installation..." -ForegroundColor Yellow
$ffmpegVersion = ffmpeg -version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ FFmpeg installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ FFmpeg not found! Please install FFmpeg and add to PATH." -ForegroundColor Red
    Write-Host "    Download from: https://ffmpeg.org/download.html" -ForegroundColor Gray
    exit 1
}

# Create virtual environment
Write-Host "[3/5] Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "  → Virtual environment already exists, skipping..." -ForegroundColor Gray
} else {
    python -m venv venv
    Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[4/5] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "  ✓ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "[5/5] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Dependencies installed" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To run the application:" -ForegroundColor White
Write-Host "  1. Activate venv:  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
Write-Host "  2. Run server:     python app.py" -ForegroundColor Gray
Write-Host ""
Write-Host "The app will be available at: http://localhost:5000" -ForegroundColor Cyan
