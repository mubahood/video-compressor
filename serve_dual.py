"""
Dual HTTP/HTTPS Server for VideoPress
======================================
Runs both HTTP (5001) and HTTPS (8443) servers simultaneously.
HTTPS uses self-signed certificate.
"""

import os
import sys
import ssl
import threading

# Add FFmpeg to PATH
FFMPEG_PATH = r'C:\ffmpeg\bin'
if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')

os.environ['FLASK_ENV'] = 'production'

from waitress import serve
from app import app
from werkzeug.serving import make_ssl_devcert

# SSL Certificate paths
CERT_DIR = os.path.join(os.path.dirname(__file__), 'certs')
SSL_CERT = os.path.join(CERT_DIR, 'server.crt')
SSL_KEY = os.path.join(CERT_DIR, 'server.key')

def run_http_server():
    """Run HTTP server on port 5001"""
    print("  [HTTP] Starting on port 5001...")
    serve(app, host='0.0.0.0', port=5001, threads=4, ident=None)

def run_https_server():
    """Run HTTPS server on port 8443"""
    print("  [HTTPS] Starting on port 8443...")
    
    # Create SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(SSL_CERT, SSL_KEY)
    
    # Use Flask's built-in server for HTTPS (only for HTTPS endpoint)
    from werkzeug.serving import run_simple
    run_simple(
        '0.0.0.0',
        8443,
        app,
        ssl_context=ssl_context,
        threaded=True,
        use_reloader=False,
        use_debugger=False
    )

if __name__ == '__main__':
    print("=" * 60)
    print("  VideoPress - Dual HTTP/HTTPS Server")
    print("=" * 60)
    
    if not (os.path.exists(SSL_CERT) and os.path.exists(SSL_KEY)):
        print("  ERROR: SSL certificates not found!")
        sys.exit(1)
    
    print(f"  HTTP:  http://102.34.160.47:5001")
    print(f"  HTTPS: https://102.34.160.47:8443")
    print("=" * 60)
    print("  Note: HTTPS uses self-signed certificate.")
    print("  Browser will warn - click 'Advanced' -> 'Proceed'")
    print("=" * 60)
    
    # Start HTTP server in background thread
    http_thread = threading.Thread(target=run_http_server, daemon=True)
    http_thread.start()
    
    # Start HTTPS server in main thread
    run_https_server()
