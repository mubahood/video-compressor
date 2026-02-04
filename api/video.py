"""
Video API Endpoints
====================
Handles video upload, compression, splitting, and downloads.
"""

import os
import time
import uuid
import json
from datetime import datetime
from flask import request, send_file, make_response
from flask_restx import Namespace, Resource
from werkzeug.utils import secure_filename

# Create namespace
video_ns = Namespace(
    'video',
    description='Video compression and processing operations',
    decorators=[]
)

# Import after namespace creation to avoid circular imports
from .models import create_models, video_upload_parser, get_session_id, get_base_url

# Lazy model initialization
_models = None

def get_models():
    global _models
    if _models is None:
        _models = create_models(video_ns)
    return _models


# =============================================================================
# CONFIGURATION (imported from main app)
# =============================================================================

def get_config():
    """Get configuration from main app"""
    from app import (
        UPLOAD_FOLDER, OUTPUT_FOLDER, ALLOWED_VIDEO_EXTENSIONS,
        load_session_data, save_session_data, get_user_data, update_user_data,
        get_user_folder, format_size, allowed_file
    )
    from src.algorithms import Algorithm, compress_video, probe_video
    from src.splitter import split_video
    
    return {
        'UPLOAD_FOLDER': UPLOAD_FOLDER,
        'OUTPUT_FOLDER': OUTPUT_FOLDER,
        'ALLOWED_VIDEO_EXTENSIONS': ALLOWED_VIDEO_EXTENSIONS,
        'load_session_data': load_session_data,
        'save_session_data': save_session_data,
        'get_user_data': get_user_data,
        'update_user_data': update_user_data,
        'get_user_folder': get_user_folder,
        'format_size': format_size,
        'allowed_file': allowed_file,
        'Algorithm': Algorithm,
        'compress_video': compress_video,
        'probe_video': probe_video,
        'split_video': split_video
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
# VIDEO UPLOAD ENDPOINT
# =============================================================================

@video_ns.route('/upload')
class VideoUpload(Resource):
    @video_ns.doc(
        description='Upload a video file for compression',
        responses={
            200: 'Video uploaded successfully',
            400: 'Invalid request or file type',
            413: 'File too large',
            500: 'Server error'
        },
        security='session'
    )
    @video_ns.expect(video_upload_parser)
    def post(self):
        """Upload a video file"""
        models = get_models()
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        # Validate file
        if 'video' not in request.files:
            return make_api_response({
                'success': False,
                'error': 'No video file provided. Use form field "video"'
            }, session_id, 400)
        
        file = request.files['video']
        
        if file.filename == '':
            return make_api_response({
                'success': False,
                'error': 'No file selected'
            }, session_id, 400)
        
        # Check extension
        ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if ext not in config['ALLOWED_VIDEO_EXTENSIONS']:
            return make_api_response({
                'success': False,
                'error': f'Invalid file type. Allowed: {", ".join(config["ALLOWED_VIDEO_EXTENSIONS"])}'
            }, session_id, 400)
        
        try:
            # Generate unique file ID
            file_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Save file
            original_name = file.filename
            safe_name = secure_filename(f"{file_id}_{original_name}")
            upload_folder = config['get_user_folder'](session_id, 'upload')
            file_path = os.path.join(upload_folder, safe_name)
            
            file.save(file_path)
            
            # Analyze video
            video_info = config['probe_video'](file_path)
            
            if not video_info:
                os.remove(file_path)
                return make_api_response({
                    'success': False,
                    'error': 'Could not analyze video. File may be corrupted or unsupported.'
                }, session_id, 400)
            
            # Store file info
            file_data = {
                'id': file_id,
                'original_name': original_name,
                'path': file_path,
                'size': video_info.file_size,
                'duration': video_info.duration,
                'width': video_info.width,
                'height': video_info.height,
                'fps': video_info.fps,
                'timestamp': datetime.now().isoformat(),
                'type': 'video'
            }
            
            user_data['uploads'][file_id] = file_data
            config['update_user_data'](session_id, user_data)
            
            return make_api_response({
                'success': True,
                'file_id': file_id,
                'filename': original_name,
                'size': config['format_size'](video_info.file_size),
                'size_bytes': video_info.file_size,
                'duration': round(video_info.duration, 2),
                'resolution': f"{video_info.width}x{video_info.height}",
                'fps': round(video_info.fps, 2),
                'needs_split': video_info.duration > 30
            }, session_id)
            
        except Exception as e:
            return make_api_response({
                'success': False,
                'error': str(e)
            }, session_id, 500)


# =============================================================================
# VIDEO COMPRESSION ENDPOINT
# =============================================================================

@video_ns.route('/compress')
class VideoCompress(Resource):
    @video_ns.doc(
        description='''
Compress a previously uploaded video.

### Algorithms

| Algorithm | Quality | Speed | Best For |
|-----------|---------|-------|----------|
| `neural_preserve` | ★★★★★ | ★★☆☆☆ | Faces, detail-heavy content |
| `bitrate_sculptor` | ★★★★☆ | ★★★☆☆ | General purpose, vlogs |
| `quantum_compress` | ★★★☆☆ | ★★★★★ | Quick sharing, bulk processing |

### Split Duration
- `0` - No splitting (single output file)
- `30` - Split into 30-second segments (WhatsApp Status)
- `60` - Split into 60-second segments
- `90` - Split into 90-second segments
        ''',
        responses={
            200: 'Video compressed successfully',
            400: 'Invalid request',
            404: 'File not found',
            500: 'Compression failed'
        }
    )
    @video_ns.expect(get_models()['video_compress_request'] if _models else None)
    def post(self):
        """Compress a video with selected algorithm"""
        models = get_models()
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        data = request.get_json() or {}
        file_id = data.get('file_id')
        algorithm = data.get('algorithm', 'neural_preserve')
        split_duration = data.get('split_duration', 0)
        
        # Validate input
        if not file_id:
            return make_api_response({
                'success': False,
                'error': 'file_id is required'
            }, session_id, 400)
        
        # Validate algorithm
        valid_algorithms = ['neural_preserve', 'bitrate_sculptor', 'quantum_compress']
        if algorithm not in valid_algorithms:
            return make_api_response({
                'success': False,
                'error': f'Invalid algorithm. Must be one of: {", ".join(valid_algorithms)}'
            }, session_id, 400)
        
        # Validate split duration
        valid_splits = [0, 30, 60, 90]
        if split_duration not in valid_splits:
            return make_api_response({
                'success': False,
                'error': f'Invalid split_duration. Must be one of: {valid_splits}'
            }, session_id, 400)
        
        # Check file exists
        if file_id not in user_data.get('uploads', {}):
            return make_api_response({
                'success': False,
                'error': 'File not found in session. Upload a video first.'
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
                'neural_preserve': config['Algorithm'].NEURAL_PRESERVE,
                'bitrate_sculptor': config['Algorithm'].BITRATE_SCULPTOR,
                'quantum_compress': config['Algorithm'].QUANTUM_COMPRESS
            }
            selected_algo = algo_map[algorithm]
            
            output_folder = config['get_user_folder'](session_id, 'output')
            results = []
            output_files = []
            base_url = get_base_url()
            
            video_duration = file_info['duration']
            
            if split_duration > 0 and video_duration > split_duration:
                # Split then compress
                split_folder = os.path.join(output_folder, f"{file_id}_splits")
                os.makedirs(split_folder, exist_ok=True)
                
                split_result = config['split_video'](
                    input_path,
                    split_folder,
                    split_duration,
                    f"{file_id}_segment"
                )
                
                if not split_result.success:
                    return make_api_response({
                        'success': False,
                        'error': f'Split failed: {split_result.message}'
                    }, session_id, 500)
                
                # Compress each segment
                for i, segment_path in enumerate(split_result.segments):
                    output_name = f"{file_id}_part{i+1:02d}.mp4"
                    output_path = os.path.join(output_folder, output_name)
                    
                    result = config['compress_video'](segment_path, output_path, selected_algo)
                    
                    if result.success:
                        output_files.append({
                            'part': i + 1,
                            'path': output_path,
                            'name': output_name,
                            'size': config['format_size'](result.compressed_size),
                            'size_bytes': result.compressed_size,
                            'format': 'mp4',
                            'download_url': f"{base_url}/api/v1/video/download/{file_id}/{i+1}",
                            'timestamp': datetime.now().isoformat()
                        })
                        results.append({
                            'part': i + 1,
                            'success': True,
                            'compression_ratio': round(result.compression_ratio, 1)
                        })
                    else:
                        results.append({
                            'part': i + 1,
                            'success': False,
                            'error': result.message
                        })
                    
                    # Clean up segment
                    if os.path.exists(segment_path):
                        try:
                            os.remove(segment_path)
                        except:
                            pass
                
                # Clean up split folder
                try:
                    os.rmdir(split_folder)
                except:
                    pass
            else:
                # Single file compression
                output_name = f"{file_id}_compressed.mp4"
                output_path = os.path.join(output_folder, output_name)
                
                result = config['compress_video'](input_path, output_path, selected_algo)
                
                if result.success:
                    output_files.append({
                        'part': 1,
                        'path': output_path,
                        'name': output_name,
                        'size': config['format_size'](result.compressed_size),
                        'size_bytes': result.compressed_size,
                        'format': 'mp4',
                        'download_url': f"{base_url}/api/v1/video/download/{file_id}/1",
                        'timestamp': datetime.now().isoformat()
                    })
                    results.append({
                        'part': 1,
                        'success': True,
                        'original_size': config['format_size'](result.original_size),
                        'compressed_size': config['format_size'](result.compressed_size),
                        'compression_ratio': round(result.compression_ratio, 1)
                    })
                else:
                    return make_api_response({
                        'success': False,
                        'error': f'Compression failed: {result.message}'
                    }, session_id, 500)
            
            # Store outputs (without path for API response)
            user_data['outputs'][file_id] = output_files
            config['update_user_data'](session_id, user_data)
            
            # Remove internal path from response
            api_outputs = []
            for out in output_files:
                api_out = {k: v for k, v in out.items() if k != 'path'}
                api_outputs.append(api_out)
            
            return make_api_response({
                'success': True,
                'file_id': file_id,
                'algorithm': algorithm,
                'total_parts': len(output_files),
                'results': results,
                'outputs': api_outputs
            }, session_id)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return make_api_response({
                'success': False,
                'error': str(e)
            }, session_id, 500)


# =============================================================================
# VIDEO DOWNLOAD ENDPOINT
# =============================================================================

@video_ns.route('/download/<string:file_id>/<int:part>')
@video_ns.param('file_id', 'The file ID from upload/compress response')
@video_ns.param('part', 'Part number (1 for single files, 1-N for split files)')
class VideoDownload(Resource):
    @video_ns.doc(
        description='Download a compressed video file',
        responses={
            200: 'File download',
            404: 'File not found'
        }
    )
    def get(self, file_id, part):
        """Download a compressed video"""
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
        
        return {'success': False, 'error': 'Part not found'}, 404


# =============================================================================
# VIDEO INFO ENDPOINT
# =============================================================================

@video_ns.route('/info/<string:file_id>')
@video_ns.param('file_id', 'The file ID from upload response')
class VideoInfo(Resource):
    @video_ns.doc(
        description='Get information about an uploaded video',
        responses={
            200: 'Video information',
            404: 'File not found'
        }
    )
    def get(self, file_id):
        """Get video file information"""
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
            'duration': file_info.get('duration', 0),
            'width': file_info.get('width', 0),
            'height': file_info.get('height', 0),
            'resolution': f"{file_info.get('width', 0)}x{file_info.get('height', 0)}",
            'fps': file_info.get('fps', 0),
            'needs_split': file_info.get('duration', 0) > 30,
            'has_output': file_id in user_data.get('outputs', {}),
            'uploaded_at': file_info.get('timestamp', '')
        }, session_id)
