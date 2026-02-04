@echo off
REM VideoPress Production Server Startup Script
REM Run this script to start the server

cd /d C:\git\video-compressor
C:\git\video-compressor\venv\Scripts\python.exe C:\git\video-compressor\serve_production.py
pause
