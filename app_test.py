"""
Test file - minimal Flask app
"""
import sys
from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return f"""
    <html>
    <head><title>Test</title></head>
    <body>
        <h1>PY WORKS!</h1>
        <p>Python version: {sys.version}</p>
        <p>Executable: {sys.executable}</p>
    </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
