"""
VideoPress HTTPS Production Server
==================================
Serves the application over HTTPS with SSL certificates using Waitress.
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

# SSL Certificate paths
CERT_DIR = os.path.join(os.path.dirname(__file__), 'certs')
SSL_CERT = os.path.join(CERT_DIR, 'server.crt')
SSL_KEY = os.path.join(CERT_DIR, 'server.key')

if __name__ == '__main__':
    # Configuration
    HOST = '0.0.0.0'
    HTTP_PORT = 5001
    HTTPS_PORT = int(os.environ.get('HTTPS_PORT', 8443))  # Use 8443 (no admin required)
    THREADS = int(os.environ.get('THREADS', 8))
    
    print("=" * 60)
    print("  VideoPress - HTTPS Production Server")
    print("=" * 60)
    
    # Check if certificates exist
    if os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY):
        print(f"  SSL Certificate: {SSL_CERT}")
        print(f"  SSL Key: {SSL_KEY}")
        print(f"  Threads: {THREADS}")
        print("=" * 60)
        print(f"  HTTPS Access: https://102.34.160.47:{HTTPS_PORT}")
        print(f"  HTTP Access:  http://102.34.160.47:{HTTP_PORT}")
        print("=" * 60)
        print("  Note: Browser may warn about self-signed certificate.")
        print("  Click 'Advanced' -> 'Proceed' to continue.")
        print("=" * 60)
        
        # Run Waitress with SSL
        serve(
            app,
            host=HOST,
            port=HTTPS_PORT,
            threads=THREADS,
            url_scheme='https',
            ident=None
        )
    else:
        print("  ERROR: SSL certificates not found!")
        print(f"  Expected: {SSL_CERT}")
        print(f"  Expected: {SSL_KEY}")
        sys.exit(1)
