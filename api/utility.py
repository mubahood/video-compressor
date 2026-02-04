"""
Utility API Endpoints
======================
Health checks, algorithm info, and system utilities.
"""

import os
from datetime import datetime
from flask import request, make_response
from flask_restx import Namespace, Resource

# Create namespace
utility_ns = Namespace(
    'utility',
    description='Utility and information endpoints',
    decorators=[]
)

from .models import create_models, get_session_id

# Lazy model initialization
_models = None

def get_models():
    global _models
    if _models is None:
        _models = create_models(utility_ns)
    return _models


# =============================================================================
# HEALTH CHECK
# =============================================================================

@utility_ns.route('/health')
class HealthCheck(Resource):
    @utility_ns.doc(
        description='Check if the API is healthy and running',
        responses={
            200: 'Service is healthy'
        }
    )
    def get(self):
        """Health check endpoint"""
        from app import ALLOWED_VIDEO_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS, MAX_FILE_SIZE
        
        # Check FFmpeg availability
        ffmpeg_available = False
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            ffmpeg_available = result.returncode == 0
        except:
            pass
        
        return {
            'status': 'healthy',
            'version': '1.0.0',
            'api_version': 'v1',
            'timestamp': datetime.now().isoformat(),
            'features': {
                'video_compression': True,
                'photo_compression': True,
                'video_splitting': True,
                'video_to_gif': True,
                'ffmpeg_available': ffmpeg_available
            },
            'limits': {
                'max_file_size_mb': MAX_FILE_SIZE // (1024 * 1024),
                'file_expiry_hours': 24,
                'session_duration_days': 7
            },
            'supported_formats': {
                'video': list(ALLOWED_VIDEO_EXTENSIONS),
                'image': list(ALLOWED_IMAGE_EXTENSIONS)
            }
        }


# =============================================================================
# ALGORITHMS INFO
# =============================================================================

@utility_ns.route('/algorithms')
class AlgorithmsInfo(Resource):
    @utility_ns.doc(
        description='Get detailed information about available compression algorithms',
        responses={
            200: 'Algorithm information'
        }
    )
    def get(self):
        """Get available algorithms and their details"""
        return {
            'video': [
                {
                    'id': 'neural_preserve',
                    'name': 'Neural Preserve',
                    'description': 'AI-powered compression with content analysis. Detects faces, motion, and scene complexity for optimal quality.',
                    'quality': 5,
                    'speed': 2,
                    'compression': 3,
                    'best_for': 'Detailed videos, faces, artistic content',
                    'features': [
                        'Face detection for quality prioritization',
                        'Content-aware bitrate allocation',
                        'Scene complexity analysis',
                        'Motion-adaptive encoding'
                    ],
                    'settings': {
                        'max_resolution': '1080p',
                        'crf_range': '17-21',
                        'preset': 'veryslow'
                    }
                },
                {
                    'id': 'bitrate_sculptor',
                    'name': 'Bitrate Sculptor',
                    'description': '2-pass encoding with dynamic bitrate allocation for optimal file size.',
                    'quality': 4,
                    'speed': 3,
                    'compression': 4,
                    'best_for': 'Vlogs, mixed content, general videos',
                    'features': [
                        'Two-pass encoding',
                        'Dynamic bitrate calculation',
                        'File size optimization',
                        'Balanced quality/size ratio'
                    ],
                    'settings': {
                        'max_resolution': '720p',
                        'encoding': 'Target bitrate',
                        'preset': 'medium'
                    }
                },
                {
                    'id': 'quantum_compress',
                    'name': 'Quantum Compress',
                    'description': 'Maximum compression with aggressive settings for smallest file size.',
                    'quality': 3,
                    'speed': 5,
                    'compression': 5,
                    'best_for': 'Quick sharing, bulk processing, low bandwidth',
                    'features': [
                        'Aggressive compression',
                        'Fast encoding',
                        'Smallest file sizes',
                        'Bulk processing friendly'
                    ],
                    'settings': {
                        'max_resolution': '640p',
                        'crf': '28',
                        'preset': 'faster'
                    }
                }
            ],
            'photo': [
                {
                    'id': 'clarity_max',
                    'name': 'Clarity Max',
                    'description': 'Maximum quality preservation with intelligent enhancement.',
                    'quality': 5,
                    'speed': 2,
                    'compression': 3,
                    'best_for': 'High-quality photos, portraits, detailed images',
                    'features': [
                        'Smart sharpening',
                        'Color enhancement',
                        'Detail preservation',
                        'Noise reduction'
                    ],
                    'settings': {
                        'max_resolution': '1280px',
                        'jpeg_quality': 92
                    }
                },
                {
                    'id': 'balanced_pro',
                    'name': 'Balanced Pro',
                    'description': 'Balanced quality and file size for general use.',
                    'quality': 4,
                    'speed': 4,
                    'compression': 4,
                    'best_for': 'General purpose, social media, everyday photos',
                    'features': [
                        'Adaptive quality',
                        'Format optimization',
                        'Smart resizing',
                        'WhatsApp optimized'
                    ],
                    'settings': {
                        'max_resolution': '1080px',
                        'jpeg_quality': 85
                    }
                },
                {
                    'id': 'quick_share',
                    'name': 'Quick Share',
                    'description': 'Fast, lightweight compression for quick sharing.',
                    'quality': 3,
                    'speed': 5,
                    'compression': 5,
                    'best_for': 'Quick sharing, thumbnails, messaging',
                    'features': [
                        'Fast processing',
                        'Small file sizes',
                        'Instant sharing',
                        'Bandwidth friendly'
                    ],
                    'settings': {
                        'max_resolution': '800px',
                        'jpeg_quality': 78
                    }
                }
            ]
        }


# =============================================================================
# SPLIT OPTIONS
# =============================================================================

@utility_ns.route('/split-options')
class SplitOptions(Resource):
    @utility_ns.doc(
        description='Get available video split duration options',
        responses={
            200: 'Split options'
        }
    )
    def get(self):
        """Get available split duration options"""
        return {
            'options': [
                {
                    'duration': 0,
                    'label': 'No Split',
                    'description': 'Keep as single file'
                },
                {
                    'duration': 30,
                    'label': '30 Seconds',
                    'description': 'WhatsApp Status limit'
                },
                {
                    'duration': 60,
                    'label': '60 Seconds',
                    'description': 'Extended clips'
                },
                {
                    'duration': 90,
                    'label': '90 Seconds',
                    'description': '1.5 minute segments'
                }
            ],
            'whatsapp_status_limit': 30,
            'recommended': 30
        }


# =============================================================================
# SUPPORTED FORMATS
# =============================================================================

@utility_ns.route('/formats')
class SupportedFormats(Resource):
    @utility_ns.doc(
        description='Get all supported file formats',
        responses={
            200: 'Supported formats'
        }
    )
    def get(self):
        """Get supported file formats"""
        from app import ALLOWED_VIDEO_EXTENSIONS, ALLOWED_IMAGE_EXTENSIONS
        
        return {
            'video': {
                'input': list(ALLOWED_VIDEO_EXTENSIONS),
                'output': ['mp4'],
                'codecs': ['H.264 (libx264)', 'AAC (audio)']
            },
            'image': {
                'input': list(ALLOWED_IMAGE_EXTENSIONS),
                'output': ['jpg', 'jpeg', 'png', 'webp'],
                'gif_output': True
            },
            'gif': {
                'max_duration': 6,
                'max_fps': 15,
                'max_width': 360
            }
        }


# =============================================================================
# API DOCUMENTATION INFO
# =============================================================================

@utility_ns.route('/docs-info')
class DocsInfo(Resource):
    @utility_ns.doc(
        description='Get API documentation links and information',
        responses={
            200: 'Documentation info'
        }
    )
    def get(self):
        """Get API documentation information"""
        base_url = request.url_root.rstrip('/')
        
        return {
            'api_name': 'MediaPress API',
            'version': '1.0.0',
            'documentation': {
                'swagger_ui': f'{base_url}/api/v1/docs',
                'openapi_json': f'{base_url}/api/v1/swagger.json'
            },
            'endpoints': {
                'video': {
                    'upload': 'POST /api/v1/video/upload',
                    'compress': 'POST /api/v1/video/compress',
                    'download': 'GET /api/v1/video/download/{file_id}/{part}',
                    'info': 'GET /api/v1/video/info/{file_id}'
                },
                'photo': {
                    'upload': 'POST /api/v1/photo/upload',
                    'compress': 'POST /api/v1/photo/compress',
                    'video_to_gif': 'POST /api/v1/photo/video-to-gif',
                    'download': 'GET /api/v1/photo/download/{file_id}/{part}',
                    'info': 'GET /api/v1/photo/info/{file_id}'
                },
                'session': {
                    'files': 'GET /api/v1/session/files',
                    'info': 'GET /api/v1/session/info',
                    'file': 'GET/DELETE /api/v1/session/files/{file_id}',
                    'clear': 'POST /api/v1/session/clear',
                    'new': 'POST /api/v1/session/new'
                },
                'utility': {
                    'health': 'GET /api/v1/utility/health',
                    'algorithms': 'GET /api/v1/utility/algorithms',
                    'formats': 'GET /api/v1/utility/formats',
                    'split_options': 'GET /api/v1/utility/split-options'
                }
            },
            'authentication': {
                'type': 'Session-based',
                'cookie_name': 'vp_session',
                'header_alternative': 'X-Session-ID',
                'session_duration': '7 days'
            }
        }


# =============================================================================
# STATISTICS (Optional - Admin)
# =============================================================================

@utility_ns.route('/stats')
class SystemStats(Resource):
    @utility_ns.doc(
        description='Get system statistics (file counts, storage usage)',
        responses={
            200: 'System statistics'
        }
    )
    def get(self):
        """Get system statistics"""
        from app import UPLOAD_FOLDER, OUTPUT_FOLDER, load_session_data
        
        all_data = load_session_data()
        
        # Count totals
        total_sessions = len(all_data)
        total_uploads = 0
        total_outputs = 0
        video_count = 0
        photo_count = 0
        
        for session_data in all_data.values():
            uploads = session_data.get('uploads', {})
            outputs = session_data.get('outputs', {})
            total_uploads += len(uploads)
            total_outputs += sum(len(outs) for outs in outputs.values())
            
            for info in uploads.values():
                if info.get('type') == 'photo':
                    photo_count += 1
                else:
                    video_count += 1
        
        # Calculate disk usage
        def get_folder_size(folder):
            total = 0
            if os.path.exists(folder):
                for dirpath, dirnames, filenames in os.walk(folder):
                    for f in filenames:
                        fp = os.path.join(dirpath, f)
                        total += os.path.getsize(fp)
            return total
        
        upload_size = get_folder_size(UPLOAD_FOLDER)
        output_size = get_folder_size(OUTPUT_FOLDER)
        
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            return f"{size_bytes:.1f} TB"
        
        return {
            'sessions': {
                'active': total_sessions
            },
            'files': {
                'total_uploads': total_uploads,
                'total_outputs': total_outputs,
                'videos': video_count,
                'photos': photo_count
            },
            'storage': {
                'uploads': format_size(upload_size),
                'uploads_bytes': upload_size,
                'outputs': format_size(output_size),
                'outputs_bytes': output_size,
                'total': format_size(upload_size + output_size),
                'total_bytes': upload_size + output_size
            },
            'timestamp': datetime.now().isoformat()
        }
