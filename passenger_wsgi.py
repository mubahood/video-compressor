"""
Passenger WSGI Entry Point for cPanel Deployment
=================================================
"""

import sys
import os

# PATHS - Update these for your cPanel environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = '/home/whatsinu/virtualenv/africa.ugnews24.info/3.8'

# Add virtual environment site-packages
venv_packages = os.path.join(VENV_DIR, 'lib', 'python3.8', 'site-packages')
if os.path.exists(venv_packages):
    sys.path.insert(0, venv_packages)

# Add application directory
sys.path.insert(0, CURRENT_DIR)

# Try to import the app with error handling
try:
    from app import app as application
except Exception as e:
    # If app fails to load, create a simple error page
    def application(environ, start_response):
        status = '500 Internal Server Error'
        error_msg = f"App failed to load: {str(e)}"
        output = f"""
        <html>
        <head><title>Error</title></head>
        <body>
        <h1>Application Error</h1>
        <p>{error_msg}</p>
        <p>Python: {sys.version}</p>
        <p>Path: {sys.path}</p>
        </body>
        </html>
        """.encode('utf-8')
        response_headers = [('Content-type', 'text/html'), ('Content-Length', str(len(output)))]
        start_response(status, response_headers)
        return [output]
