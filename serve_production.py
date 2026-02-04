"""
Production Server for VideoPress
=================================
Uses Waitress WSGI server for Windows production deployment.
"""

import os
import sys

# Add FFmpeg to PATH
FFMPEG_PATH = os.environ.get('FFMPEG_PATH', r'C:\ffmpeg\bin')
if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')

# Set production environment
os.environ['FLASK_ENV'] = 'production'

from waitress import serve
from app import app

if __name__ == '__main__':
    # Configuration
    HOST = '0.0.0.0'  # Listen on all interfaces (allows external access)
    PORT = int(os.environ.get('PORT', 5001))
    THREADS = int(os.environ.get('THREADS', 8))
    
    print("=" * 60)
    print("  VideoPress - Production Server")
    print("=" * 60)
    print(f"  Host: {HOST}")
    print(f"  Port: {PORT}")
    print(f"  Threads: {THREADS}")
    print("=" * 60)
    print(f"  Access locally:    http://127.0.0.1:{PORT}")
    print(f"  Access externally: http://<YOUR_PUBLIC_IP>:{PORT}")
    print("=" * 60)
    print("  Press Ctrl+C to stop the server")
    print("=" * 60)
    
    serve(app, host=HOST, port=PORT, threads=THREADS)
