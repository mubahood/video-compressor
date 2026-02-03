"""
WSGI Entry Point
================
Alternative WSGI file for various deployment scenarios.
"""

import os
import sys

# Add application directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# For Gunicorn, uWSGI, or other WSGI servers
if __name__ == '__main__':
    app.run()
