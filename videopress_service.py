"""
VideoPress Windows Service
==========================
Installs VideoPress as a Windows Service for automatic startup.

Usage (run as Administrator):
  Install:   python videopress_service.py install
  Start:     python videopress_service.py start
  Stop:      python videopress_service.py stop
  Remove:    python videopress_service.py remove
  Debug:     python videopress_service.py debug
"""

import os
import sys
import time

# Add FFmpeg to PATH
FFMPEG_PATH = r'C:\ffmpeg\bin'
if os.path.exists(FFMPEG_PATH):
    os.environ['PATH'] = FFMPEG_PATH + os.pathsep + os.environ.get('PATH', '')

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket

# Add the project directory to path
PROJECT_DIR = r'C:\git\video-compressor'
sys.path.insert(0, PROJECT_DIR)
os.chdir(PROJECT_DIR)


class VideoPressService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'VideoPress'
    _svc_display_name_ = 'VideoPress Media Compressor'
    _svc_description_ = 'WhatsApp Video & Photo Compression Web Service'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.server = None
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        if self.server:
            self.server.close()

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        os.environ['FLASK_ENV'] = 'production'
        
        from waitress import serve
        from app import app
        
        HOST = '0.0.0.0'
        PORT = 5001
        THREADS = 8
        
        servicemanager.LogInfoMsg(f'VideoPress starting on {HOST}:{PORT}')
        
        serve(app, host=HOST, port=PORT, threads=THREADS)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(VideoPressService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(VideoPressService)
