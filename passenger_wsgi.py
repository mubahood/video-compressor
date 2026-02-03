"""
Passenger WSGI Entry Point for cPanel Deployment
=================================================
This file is required for deploying Flask apps on cPanel with Passenger.
"""

import sys
import os

# IMPORTANT: Set the correct paths for your cPanel environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# Virtual environment path - UPDATE THIS to match your cPanel setup
# Check your Python App settings in cPanel for the correct path
VENV_DIR = os.path.join(CURRENT_DIR, 'venv')

# Alternative common paths on cPanel:
# VENV_DIR = '/home/whatsinu/virtualenv/africa.ugnews24.info/3.8'
# VENV_DIR = '/home/whatsinu/africa.ugnews24.info/venv'

# Activate virtual environment
if os.path.exists(VENV_DIR):
    venv_site_packages = os.path.join(VENV_DIR, 'lib', 'python3.8', 'site-packages')
    if os.path.exists(venv_site_packages):
        sys.path.insert(0, venv_site_packages)
    # Also try python3.9, 3.10, 3.11
    for pyver in ['3.9', '3.10', '3.11', '3.12']:
        alt_path = os.path.join(VENV_DIR, 'lib', f'python{pyver}', 'site-packages')
        if os.path.exists(alt_path):
            sys.path.insert(0, alt_path)
            break

# Add application directory to Python path
sys.path.insert(0, CURRENT_DIR)

# Import the Flask application
from app import app as application

# Passenger expects the WSGI app to be named 'application'
if __name__ == '__main__':
    application.run()
