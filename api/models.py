"""
Shared API Models and Utilities
================================
Common models, parsers, and helper functions for API endpoints.
"""

from flask_restx import fields, reqparse
from flask import request
from werkzeug.datastructures import FileStorage
import time
import uuid


def create_models(api):
    """Create all API models for documentation"""
    
    # Base response model
    base_response = api.model('BaseResponse', {
        'success': fields.Boolean(required=True, description='Whether the operation succeeded'),
        'error': fields.String(description='Error message if success is false')
    })
    
    # Video info model
    video_info = api.model('VideoInfo', {
        'file_id': fields.String(required=True, description='Unique file identifier'),
        'filename': fields.String(required=True, description='Original filename'),
        'size': fields.String(description='Human-readable file size'),
        'size_bytes': fields.Integer(description='File size in bytes'),
        'duration': fields.Float(description='Video duration in seconds'),
        'resolution': fields.String(description='Video resolution (e.g., 1920x1080)'),
        'fps': fields.Float(description='Frames per second'),
        'needs_split': fields.Boolean(description='Whether video exceeds 30s and may need splitting')
    })
    
    # Photo info model
    photo_info = api.model('PhotoInfo', {
        'file_id': fields.String(required=True, description='Unique file identifier'),
        'filename': fields.String(required=True, description='Original filename'),
        'size': fields.String(description='Human-readable file size'),
        'size_bytes': fields.Integer(description='File size in bytes'),
        'width': fields.Integer(description='Image width in pixels'),
        'height': fields.Integer(description='Image height in pixels'),
        'resolution': fields.String(description='Image resolution (e.g., 1920x1080)'),
        'format': fields.String(description='Image format (JPEG, PNG, etc.)'),
        'is_animated': fields.Boolean(description='Whether image is animated (GIF)')
    })
    
    # Upload response models
    video_upload_response = api.inherit('VideoUploadResponse', base_response, {
        'file_id': fields.String(description='Unique file identifier'),
        'filename': fields.String(description='Original filename'),
        'size': fields.String(description='Human-readable file size'),
        'size_bytes': fields.Integer(description='File size in bytes'),
        'duration': fields.Float(description='Video duration in seconds'),
        'resolution': fields.String(description='Video resolution'),
        'fps': fields.Float(description='Frames per second'),
        'needs_split': fields.Boolean(description='Whether video needs splitting for WhatsApp')
    })
    
    photo_upload_response = api.inherit('PhotoUploadResponse', base_response, {
        'file_id': fields.String(description='Unique file identifier'),
        'filename': fields.String(description='Original filename'),
        'size': fields.String(description='Human-readable file size'),
        'size_bytes': fields.Integer(description='File size in bytes'),
        'width': fields.Integer(description='Image width'),
        'height': fields.Integer(description='Image height'),
        'resolution': fields.String(description='Image resolution'),
        'format': fields.String(description='Image format'),
        'is_animated': fields.Boolean(description='Whether image is animated'),
        'type': fields.String(description='File type (always "photo")')
    })
    
    # Compression request models
    video_compress_request = api.model('VideoCompressRequest', {
        'file_id': fields.String(required=True, description='File ID from upload response'),
        'algorithm': fields.String(
            description='Compression algorithm',
            enum=['neural_preserve', 'bitrate_sculptor', 'quantum_compress'],
            default='neural_preserve'
        ),
        'split_duration': fields.Integer(
            description='Split video into segments of this duration (seconds). 0 = no split',
            enum=[0, 30, 60, 90],
            default=0
        )
    })
    
    photo_compress_request = api.model('PhotoCompressRequest', {
        'file_id': fields.String(required=True, description='File ID from upload response'),
        'algorithm': fields.String(
            description='Compression algorithm',
            enum=['clarity_max', 'balanced_pro', 'quick_share'],
            default='balanced_pro'
        ),
        'format': fields.String(
            description='Output format',
            enum=['jpg', 'png', 'webp'],
            default='jpg'
        )
    })
    
    gif_convert_request = api.model('GifConvertRequest', {
        'file_id': fields.String(required=True, description='File ID of video to convert'),
        'duration': fields.Float(
            description='Max GIF duration in seconds (max 6)',
            default=6.0
        ),
        'fps': fields.Integer(
            description='Frames per second (max 15)',
            default=12
        )
    })
    
    # Compression output model
    output_file = api.model('OutputFile', {
        'part': fields.Integer(description='Part number (1 if not split)'),
        'name': fields.String(description='Output filename'),
        'size': fields.String(description='Human-readable file size'),
        'size_bytes': fields.Integer(description='File size in bytes'),
        'format': fields.String(description='Output format'),
        'dimensions': fields.String(description='Output dimensions (photos only)'),
        'download_url': fields.String(description='URL to download the file')
    })
    
    # Compression result model
    compression_result = api.model('CompressionResult', {
        'part': fields.Integer(description='Part number'),
        'success': fields.Boolean(description='Whether compression succeeded'),
        'original_size': fields.String(description='Original file size'),
        'compressed_size': fields.String(description='Compressed file size'),
        'compression_ratio': fields.Float(description='Compression ratio percentage')
    })
    
    video_compress_response = api.inherit('VideoCompressResponse', base_response, {
        'file_id': fields.String(description='Original file ID'),
        'algorithm': fields.String(description='Algorithm used'),
        'total_parts': fields.Integer(description='Total number of output parts'),
        'results': fields.List(fields.Nested(compression_result), description='Compression results per part'),
        'outputs': fields.List(fields.Nested(output_file), description='Output files')
    })
    
    photo_compress_response = api.inherit('PhotoCompressResponse', base_response, {
        'file_id': fields.String(description='Original file ID'),
        'algorithm': fields.String(description='Algorithm used'),
        'original_size': fields.String(description='Original file size'),
        'compressed_size': fields.String(description='Compressed file size'),
        'compression_ratio': fields.Float(description='Compression ratio percentage'),
        'output_format': fields.String(description='Output format'),
        'new_dimensions': fields.List(fields.Integer, description='New width and height'),
        'message': fields.String(description='Status message'),
        'outputs': fields.List(fields.Nested(output_file), description='Output files')
    })
    
    gif_convert_response = api.inherit('GifConvertResponse', base_response, {
        'file_id': fields.String(description='Original file ID'),
        'compressed_size': fields.String(description='GIF file size'),
        'message': fields.String(description='Status message'),
        'outputs': fields.List(fields.Nested(output_file), description='Output files')
    })
    
    # Session models
    session_file = api.model('SessionFile', {
        'id': fields.String(description='File ID'),
        'original_name': fields.String(description='Original filename'),
        'size': fields.Integer(description='File size in bytes'),
        'width': fields.Integer(description='Width'),
        'height': fields.Integer(description='Height'),
        'timestamp': fields.String(description='Upload timestamp'),
        'type': fields.String(description='File type (video or photo)'),
        'duration': fields.Float(description='Video duration (videos only)'),
        'format': fields.String(description='Image format (photos only)'),
        'is_animated': fields.Boolean(description='Is animated (photos only)')
    })
    
    session_files_response = api.inherit('SessionFilesResponse', base_response, {
        'session_id': fields.String(description='Current session ID'),
        'uploads': fields.List(fields.Nested(session_file), description='Uploaded files'),
        'outputs': fields.Raw(description='Output files keyed by file_id')
    })
    
    clear_session_response = api.inherit('ClearSessionResponse', base_response, {
        'new_session_id': fields.String(description='New session ID after clearing')
    })
    
    # Health check model
    health_response = api.model('HealthResponse', {
        'status': fields.String(description='Service status'),
        'version': fields.String(description='API version'),
        'timestamp': fields.String(description='Current server time'),
        'features': fields.Raw(description='Available features and configuration')
    })
    
    # Algorithm info models
    algorithm_info = api.model('AlgorithmInfo', {
        'id': fields.String(description='Algorithm identifier'),
        'name': fields.String(description='Display name'),
        'description': fields.String(description='Algorithm description'),
        'quality': fields.Integer(description='Quality rating (1-5)'),
        'speed': fields.Integer(description='Speed rating (1-5)'),
        'compression': fields.Integer(description='Compression rating (1-5)'),
        'best_for': fields.String(description='Recommended use case')
    })
    
    algorithms_response = api.model('AlgorithmsResponse', {
        'video': fields.List(fields.Nested(algorithm_info), description='Video compression algorithms'),
        'photo': fields.List(fields.Nested(algorithm_info), description='Photo compression algorithms')
    })
    
    return {
        'base_response': base_response,
        'video_info': video_info,
        'photo_info': photo_info,
        'video_upload_response': video_upload_response,
        'photo_upload_response': photo_upload_response,
        'video_compress_request': video_compress_request,
        'photo_compress_request': photo_compress_request,
        'gif_convert_request': gif_convert_request,
        'output_file': output_file,
        'compression_result': compression_result,
        'video_compress_response': video_compress_response,
        'photo_compress_response': photo_compress_response,
        'gif_convert_response': gif_convert_response,
        'session_file': session_file,
        'session_files_response': session_files_response,
        'clear_session_response': clear_session_response,
        'health_response': health_response,
        'algorithm_info': algorithm_info,
        'algorithms_response': algorithms_response
    }


# File upload parsers
video_upload_parser = reqparse.RequestParser()
video_upload_parser.add_argument(
    'video',
    type=FileStorage,
    location='files',
    required=True,
    help='Video file to upload (MP4, MOV, AVI, MKV, WebM, M4V, 3GP)'
)

photo_upload_parser = reqparse.RequestParser()
photo_upload_parser.add_argument(
    'photo',
    type=FileStorage,
    location='files',
    required=True,
    help='Photo file to upload (JPG, PNG, GIF, WebP, BMP, TIFF)'
)


def get_session_id():
    """Get session ID from header or cookie"""
    # First check header (for API clients)
    session_id = request.headers.get('X-Session-ID')
    if session_id:
        return session_id
    
    # Fall back to cookie
    session_id = request.cookies.get('vp_session')
    if session_id:
        return session_id
    
    # Create new session
    return f"{int(time.time())}_{uuid.uuid4().hex[:12]}"


def get_base_url():
    """Get the base URL for download links"""
    return request.url_root.rstrip('/')
