# -*- coding: utf-8 -*-
# PowerShell Setup Script for Hybrid Trading System
# Encoding: UTF-8

# Force UTF-8 output encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Hybrid Trading System - Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if python is available
Write-Host "[1/5] Checking Python installation..." -ForegroundColor White
if (-not (Get-Command "python" -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Please install Python and add it to PATH." -ForegroundColor Red
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "      Found: $pythonVersion" -ForegroundColor Green

# Create virtual environment if it doesn't exist
Write-Host "[2/5] Creating virtual environment (venv)..." -ForegroundColor White
if (-not (Test-Path "venv")) {
    try {
        python -m venv venv
        if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
            Write-Host "ERROR: Failed to create venv. Trying alternative method..." -ForegroundColor Yellow
            python.exe -m venv venv --clear
        }
    } catch {
        Write-Host "ERROR: Failed to create virtual environment: $_" -ForegroundColor Red
        exit 1
    }
}

# Verify venv was created successfully
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment creation failed." -ForegroundColor Red
    Write-Host "       Please try manually: python -m venv venv" -ForegroundColor Yellow
    exit 1
}
Write-Host "      venv created successfully." -ForegroundColor Green

# Activate virtual environment
Write-Host "[3/5] Activating virtual environment..." -ForegroundColor White
try {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "      Activated." -ForegroundColor Green
} catch {
    Write-Host "ERROR: Failed to activate venv: $_" -ForegroundColor Red
    Write-Host "       Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

# Upgrade pip
Write-Host "[4/5] Upgrading pip..." -ForegroundColor White
python -m pip install --upgrade pip --quiet
Write-Host "      pip upgraded." -ForegroundColor Green

# Install GPU PyTorch (CUDA 11.8)
Write-Host "[5/5] Installing dependencies..." -ForegroundColor White
Write-Host "      Installing PyTorch (GPU/CUDA 11.8)..." -ForegroundColor Gray
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 --quiet

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "      Installing packages from requirements.txt..." -ForegroundColor Gray
    pip install -r requirements.txt --quiet
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "To activate this environment later, run:" -ForegroundColor White
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Cyan
Write-Host ""
