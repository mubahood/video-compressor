"""
Photo API Endpoints
====================
Handles photo upload, compression, and video-to-GIF conversion.
"""

import os
import time
import uuid
from datetime import datetime
from flask import request, send_file, make_response
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

# Create namespace
photo_ns = Namespace(
    'photo',
    description='Photo compression and conversion operations',
    decorators=[]
)

# Import after namespace creation
from .models import create_models, photo_upload_parser, get_session_id, get_base_url

# Lazy model initialization
_models = None

def get_models():
    global _models
    if _models is None:
        _models = create_models(photo_ns)
    return _models


def get_config():
    """Get configuration from main app"""
    from app import (
        UPLOAD_FOLDER, OUTPUT_FOLDER, ALLOWED_IMAGE_EXTENSIONS,
        get_user_data, update_user_data, get_user_folder, format_size, is_image_file
    )
    from src.photo_algorithms import (
        PhotoAlgorithm, compress_photo, analyze_photo, video_to_gif
    )
    
    return {
        'UPLOAD_FOLDER': UPLOAD_FOLDER,
        'OUTPUT_FOLDER': OUTPUT_FOLDER,
        'ALLOWED_IMAGE_EXTENSIONS': ALLOWED_IMAGE_EXTENSIONS,
        'get_user_data': get_user_data,
        'update_user_data': update_user_data,
        'get_user_folder': get_user_folder,
        'format_size': format_size,
        'is_image_file': is_image_file,
        'PhotoAlgorithm': PhotoAlgorithm,
        'compress_photo': compress_photo,
        'analyze_photo': analyze_photo,
        'video_to_gif': video_to_gif
    }


def make_api_response(data, session_id, status_code=200):
    """Create API response with session cookie"""
    response = make_response(data, status_code)
    response.set_cookie(
        'vp_session',
        session_id,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        samesite='Lax'
    )
    return response


# =============================================================================
# PHOTO UPLOAD ENDPOINT
# =============================================================================

@photo_ns.route('/upload')
class PhotoUpload(Resource):
    @photo_ns.doc(
        description='Upload a photo for compression',
        responses={
            200: 'Photo uploaded successfully',
            400: 'Invalid request or file type',
            413: 'File too large',
            500: 'Server error'
        }
    )
    @photo_ns.expect(photo_upload_parser)
    def post(self):
        """Upload a photo file"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        # Validate file
        if 'photo' not in request.files:
            return make_api_response({
                'success': False,
                'error': 'No photo file provided. Use form field "photo"'
            }, session_id, 400)
        
        file = request.files['photo']
        
        if file.filename == '':
            return make_api_response({
                'success': False,
                'error': 'No file selected'
            }, session_id, 400)
        
        # Check extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in config['ALLOWED_IMAGE_EXTENSIONS']:
            return make_api_response({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(config["ALLOWED_IMAGE_EXTENSIONS"])}'
            }, session_id, 400)
        
        try:
            # Generate unique file ID
            file_id = f"photo_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Save file
            original_name = file.filename
            safe_name = secure_filename(f"{file_id}_{original_name}")
            upload_folder = config['get_user_folder'](session_id, 'upload')
            file_path = os.path.join(upload_folder, safe_name)
            
            file.save(file_path)
            
            # Analyze photo
            photo_info = config['analyze_photo'](file_path)
            
            if not photo_info:
                os.remove(file_path)
                return make_api_response({
                    'success': False,
                    'error': 'Could not analyze photo. File may be corrupted.'
                }, session_id, 400)
            
            # Store file info
            file_data = {
                'id': file_id,
                'original_name': original_name,
                'path': file_path,
                'size': photo_info.file_size,
                'width': photo_info.width,
                'height': photo_info.height,
                'format': photo_info.format,
                'is_animated': photo_info.is_animated,
                'type': 'photo',
                'timestamp': datetime.now().isoformat()
            }
            
            user_data['uploads'][file_id] = file_data
            config['update_user_data'](session_id, user_data)
            
            return make_api_response({
                'success': True,
                'file_id': file_id,
                'filename': original_name,
                'size': config['format_size'](photo_info.file_size),
                'size_bytes': photo_info.file_size,
                'width': photo_info.width,
                'height': photo_info.height,
                'resolution': f"{photo_info.width}x{photo_info.height}",
                'format': photo_info.format,
                'is_animated': photo_info.is_animated,
                'type': 'photo'
            }, session_id)
            
        except Exception as e:
            return make_api_response({
                'success': False,
                'error': str(e)
            }, session_id, 500)


# =============================================================================
# PHOTO COMPRESSION ENDPOINT
# =============================================================================

@photo_ns.route('/compress')
class PhotoCompress(Resource):
    @photo_ns.doc(
        description='''
Compress a previously uploaded photo.

### Algorithms

| Algorithm | Quality | Size Reduction | Best For |
|-----------|---------|----------------|----------|
| `clarity_max` | ★★★★★ | ★★★☆☆ | High-quality photos, portraits |
| `balanced_pro` | ★★★★☆ | ★★★★☆ | General purpose (default) |
| `quick_share` | ★★★☆☆ | ★★★★★ | Quick sharing, thumbnails |

### Output Formats
- `jpg` - Best for photos (lossy, small size)
- `png` - Best for graphics with transparency (lossless)
- `webp` - Modern format with best compression
        ''',
        responses={
            200: 'Photo compressed successfully',
            400: 'Invalid request',
            404: 'File not found',
            500: 'Compression failed'
        }
    )
    def post(self):
        """Compress a photo with selected algorithm"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        data = request.get_json() or {}
        file_id = data.get('file_id')
        algorithm = data.get('algorithm', 'balanced_pro')
        output_format = data.get('format', 'jpg')
        
        # Validate input
        if not file_id:
            return make_api_response({
                'success': False,
                'error': 'file_id is required'
            }, session_id, 400)
        
        # Validate algorithm
        valid_algorithms = ['clarity_max', 'balanced_pro', 'quick_share']
        if algorithm not in valid_algorithms:
            return make_api_response({
                'success': False,
                'error': f'Invalid algorithm. Must be one of: {", ".join(valid_algorithms)}'
            }, session_id, 400)
        
        # Validate format
        valid_formats = ['jpg', 'jpeg', 'png', 'webp']
        if output_format.lower() not in valid_formats:
            return make_api_response({
                'success': False,
                'error': f'Invalid format. Must be one of: {", ".join(valid_formats)}'
            }, session_id, 400)
        
        # Check file exists
        if file_id not in user_data.get('uploads', {}):
            return make_api_response({
                'success': False,
                'error': 'File not found in session'
            }, session_id, 404)
        
        file_info = user_data['uploads'][file_id]
        input_path = file_info['path']
        
        if not os.path.exists(input_path):
            return make_api_response({
                'success': False,
                'error': 'File no longer exists on server'
            }, session_id, 404)
        
        try:
            # Map algorithm
            algo_map = {
                'clarity_max': config['PhotoAlgorithm'].CLARITY_MAX,
                'balanced_pro': config['PhotoAlgorithm'].BALANCED_PRO,
                'quick_share': config['PhotoAlgorithm'].QUICK_SHARE
            }
            selected_algo = algo_map[algorithm]
            
            output_folder = config['get_user_folder'](session_id, 'output')
            base_url = get_base_url()
            
            # Determine output extension
            ext = output_format.lower()
            if ext == 'jpeg':
                ext = 'jpg'
            
            output_name = f"{file_id}_compressed.{ext}"
            output_path = os.path.join(output_folder, output_name)
            
            result = config['compress_photo'](input_path, output_path, selected_algo, ext)
            
            if result.success:
                actual_name = os.path.basename(result.output_path)
                
                output_files = [{
                    'part': 1,
                    'path': result.output_path,
                    'name': actual_name,
                    'size': config['format_size'](result.compressed_size),
                    'size_bytes': result.compressed_size,
                    'format': result.output_format,
                    'dimensions': f"{result.new_dimensions[0]}x{result.new_dimensions[1]}",
                    'download_url': f"{base_url}/api/v1/photo/download/{file_id}/1",
                    'timestamp': datetime.now().isoformat()
                }]
                
                # Store outputs
                user_data['outputs'][file_id] = output_files
                config['update_user_data'](session_id, user_data)
                
                # Remove internal path from response
                api_outputs = [{k: v for k, v in out.items() if k != 'path'} for out in output_files]
                
                return make_api_response({
                    'success': True,
                    'file_id': file_id,
                    'algorithm': algorithm,
                    'original_size': config['format_size'](result.original_size),
                    'compressed_size': config['format_size'](result.compressed_size),
                    'compression_ratio': round(result.compression_ratio, 1),
                    'output_format': result.output_format,
                    'new_dimensions': list(result.new_dimensions),
                    'message': result.message,
                    'outputs': api_outputs
                }, session_id)
            else:
                return make_api_response({
                    'success': False,
                    'error': result.message
                }, session_id, 500)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return make_api_response({
                'success': False,
                'error': str(e)
            }, session_id, 500)


# =============================================================================
# VIDEO TO GIF CONVERSION
# =============================================================================

@photo_ns.route('/video-to-gif')
class VideoToGif(Resource):
    @photo_ns.doc(
        description='''
Convert a video to an optimized GIF for WhatsApp.

### Parameters
- `duration` - Maximum GIF duration (max 6 seconds for WhatsApp)
- `fps` - Frames per second (max 15, default 12)

### Notes
- Output is automatically optimized for WhatsApp sticker requirements
- Color palette is reduced for smaller file size
- Maximum width is 360px
        ''',
        responses={
            200: 'GIF created successfully',
            400: 'Invalid request',
            404: 'Video not found',
            500: 'Conversion failed'
        }
    )
    def post(self):
        """Convert a video to GIF"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        data = request.get_json() or {}
        file_id = data.get('file_id')
        max_duration = data.get('duration', 6.0)
        fps = data.get('fps', 12)
        
        # Validate input
        if not file_id:
            return make_api_response({
                'success': False,
                'error': 'file_id is required'
            }, session_id, 400)
        
        # Validate duration
        if not isinstance(max_duration, (int, float)) or max_duration <= 0:
            return make_api_response({
                'success': False,
                'error': 'duration must be a positive number'
            }, session_id, 400)
        
        # Validate fps
        if not isinstance(fps, int) or fps <= 0:
            return make_api_response({
                'success': False,
                'error': 'fps must be a positive integer'
            }, session_id, 400)
        
        # Check file exists
        if file_id not in user_data.get('uploads', {}):
            return make_api_response({
                'success': False,
                'error': 'File not found in session'
            }, session_id, 404)
        
        file_info = user_data['uploads'][file_id]
        input_path = file_info['path']
        
        # Ensure it's a video, not a photo
        if file_info.get('type') == 'photo':
            return make_api_response({
                'success': False,
                'error': 'Cannot convert photo to GIF. Upload a video file.'
            }, session_id, 400)
        
        if not os.path.exists(input_path):
            return make_api_response({
                'success': False,
                'error': 'File no longer exists on server'
            }, session_id, 404)
        
        try:
            output_folder = config['get_user_folder'](session_id, 'output')
            output_name = f"{file_id}_converted.gif"
            output_path = os.path.join(output_folder, output_name)
            base_url = get_base_url()
            
            result = config['video_to_gif'](
                input_path,
                output_path,
                max_duration=min(max_duration, 6.0),  # WhatsApp limit
                fps=min(fps, 15),
                max_width=360
            )
            
            if result.success:
                output_files = [{
                    'part': 1,
                    'path': result.output_path,
                    'name': os.path.basename(result.output_path),
                    'size': config['format_size'](result.compressed_size),
                    'size_bytes': result.compressed_size,
                    'format': 'GIF',
                    'download_url': f"{base_url}/api/v1/photo/download/{file_id}/1",
                    'timestamp': datetime.now().isoformat()
                }]
                
                user_data['outputs'][file_id] = output_files
                config['update_user_data'](session_id, user_data)
                
                # Remove internal path from response
                api_outputs = [{k: v for k, v in out.items() if k != 'path'} for out in output_files]
                
                return make_api_response({
                    'success': True,
                    'file_id': file_id,
                    'compressed_size': config['format_size'](result.compressed_size),
                    'size_bytes': result.compressed_size,
                    'message': result.message,
                    'outputs': api_outputs
                }, session_id)
            else:
                return make_api_response({
                    'success': False,
                    'error': result.message
                }, session_id, 500)
            
        except Exception as e:
            return make_api_response({
                'success': False,
                'error': str(e)
            }, session_id, 500)


# =============================================================================
# PHOTO DOWNLOAD ENDPOINT
# =============================================================================

@photo_ns.route('/download/<string:file_id>/<int:part>')
@photo_ns.param('file_id', 'The file ID from upload/compress response')
@photo_ns.param('part', 'Part number (always 1 for photos)')
class PhotoDownload(Resource):
    @photo_ns.doc(
        description='Download a compressed photo or GIF',
        responses={
            200: 'File download',
            404: 'File not found'
        }
    )
    def get(self, file_id, part):
        """Download a compressed photo"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        if file_id not in user_data.get('outputs', {}):
            return {'success': False, 'error': 'File not found'}, 404
        
        outputs = user_data['outputs'][file_id]
        
        for output in outputs:
            if output['part'] == part:
                if os.path.exists(output['path']):
                    return send_file(
                        output['path'],
                        as_attachment=True,
                        download_name=output['name']
                    )
        
        return {'success': False, 'error': 'File not found'}, 404


# =============================================================================
# PHOTO INFO ENDPOINT
# =============================================================================

@photo_ns.route('/info/<string:file_id>')
@photo_ns.param('file_id', 'The file ID from upload response')
class PhotoInfo(Resource):
    @photo_ns.doc(
        description='Get information about an uploaded photo',
        responses={
            200: 'Photo information',
            404: 'File not found'
        }
    )
    def get(self, file_id):
        """Get photo file information"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        if file_id not in user_data.get('uploads', {}):
            return make_api_response({
                'success': False,
                'error': 'File not found'
            }, session_id, 404)
        
        file_info = user_data['uploads'][file_id]
        
        return make_api_response({
            'success': True,
            'file_id': file_id,
            'filename': file_info.get('original_name', ''),
            'size': config['format_size'](file_info.get('size', 0)),
            'size_bytes': file_info.get('size', 0),
            'width': file_info.get('width', 0),
            'height': file_info.get('height', 0),
            'resolution': f"{file_info.get('width', 0)}x{file_info.get('height', 0)}",
            'format': file_info.get('format', ''),
            'is_animated': file_info.get('is_animated', False),
            'has_output': file_id in user_data.get('outputs', {}),
            'uploaded_at': file_info.get('timestamp', '')
        }, session_id)
