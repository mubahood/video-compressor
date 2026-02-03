"""
Passenger WSGI Entry Point for cPanel Deployment
=================================================
This file is required for deploying Flask apps on cPanel with Passenger.
"""

import sys
import os

# Add application directory to Python path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Set up virtual environment (if using one on cPanel)
# Uncomment and adjust the path if you create a venv on cPanel
# VENV_DIR = os.path.join(CURRENT_DIR, 'venv')
# if os.path.exists(VENV_DIR):
#     activate_this = os.path.join(VENV_DIR, 'bin', 'activate_this.py')
#     with open(activate_this) as f:
#         exec(f.read(), {'__file__': activate_this})

# Import the Flask application
from app import app as application

# Passenger expects the WSGI app to be named 'application'
# This is already done above, but making it explicit:
if __name__ == '__main__':
    application.run()
