"""
MediaPress REST API
====================
Complete RESTful API with OpenAPI/Swagger documentation.
"""

from flask import Blueprint
from flask_restx import Api

# Create API Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize Flask-RESTX API with Swagger documentation
api = Api(
    api_bp,
    version='1.0.0',
    title='MediaPress API',
    description='''
## WhatsApp Video & Photo Compression API

A powerful REST API for compressing videos and photos optimized for WhatsApp Status.

### Features
- **Video Compression** - 3 AI-powered algorithms
- **Photo Compression** - Smart image optimization
- **Video Splitting** - Split into 30s, 60s, or 90s segments
- **Video to GIF** - Convert short videos to optimized GIFs
- **Session Management** - Persistent file storage with auto-cleanup

### Authentication
This API uses session-based authentication via cookies (`vp_session`).
You can also pass `X-Session-ID` header for programmatic access.

### Rate Limits
- Max file size: 500MB
- Files auto-expire after 24 hours

### Supported Formats
**Video:** MP4, MOV, AVI, MKV, WebM, M4V, 3GP  
**Image:** JPG, JPEG, PNG, GIF, WebP, BMP, TIFF
    ''',
    doc='/docs',
    license='MIT',
    license_url='https://opensource.org/licenses/MIT',
    contact='MediaPress API',
    contact_email='support@example.com',
    authorizations={
        'session': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-Session-ID',
            'description': 'Session ID for API access (optional - cookie is preferred)'
        }
    },
    default_mediatype='application/json'
)

# Import and register namespaces
from .video import video_ns
from .photo import photo_ns
from .session import session_ns
from .utility import utility_ns

api.add_namespace(video_ns, path='/video')
api.add_namespace(photo_ns, path='/photo')
api.add_namespace(session_ns, path='/session')
api.add_namespace(utility_ns, path='/utility')
