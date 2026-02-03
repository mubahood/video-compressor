"""
Passenger WSGI Entry Point for cPanel
"""
import sys
import os

# Setup paths
INTERP = '/home/whatsinu/virtualenv/africa.ugnews24.info/3.8/bin/python'
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Import Flask app
from app import app as application
