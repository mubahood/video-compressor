"""
MediaPress Background Service
=============================
This script is designed to run as a Windows Service.
Serves the MediaPress application at http://compress.ugnews24.info:5001
"""

import os
import sys
import logging

# Setup logging to file
LOG_FILE = r'C:\git\video-compressor\service.log'
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Add FFmpeg to PATH
FFMPEG_PATH = r'C:\ffmpeg\bin'
if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')
    logging.info(f"Added FFmpeg to PATH: {FFMPEG_PATH}")

# Set production environment
os.environ['FLASK_ENV'] = 'production'

# Change to project directory
PROJECT_DIR = r'C:\git\video-compressor'
os.chdir(PROJECT_DIR)
sys.path.insert(0, PROJECT_DIR)

logging.info("Starting MediaPress service...")

try:
    from waitress import serve
    from app import app
    
    HOST = '0.0.0.0'
    PORT = 5001  # Custom port to avoid conflict with main domain
    THREADS = 8
    
    logging.info(f"Server starting on {HOST}:{PORT} with {THREADS} threads")
    print(f"MediaPress running on http://compress.ugnews24.info:{PORT}")
    
    serve(app, host=HOST, port=PORT, threads=THREADS)
    
except Exception as e:
    logging.error(f"Service error: {e}")
    raise
