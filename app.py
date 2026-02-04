"""
VideoPress - WhatsApp Video & Photo Compressor
===============================================
Professional Flask application with persistent session management,
auto-cleanup, and improved cookie handling.
Supports both video and photo compression optimized for WhatsApp.

Deployment: Compatible with cPanel Passenger WSGI
"""

import os
import uuid
import time
import json
import shutil
import threading
from datetime import datetime, timedelta
from flask import (
    Flask, render_template, request, jsonify,
    send_file, session, make_response
)
from werkzeug.utils import secure_filename

# Import compression modules
from src.algorithms import Algorithm, compress_video, probe_video
from src.splitter import split_video
from src.photo_algorithms import (
    PhotoAlgorithm, compress_photo, analyze_photo, video_to_gif
)

# =============================================================================
# APP CONFIGURATION
# =============================================================================

# Determine base directory (works for both local and cPanel deployment)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Environment detection
IS_PRODUCTION = os.environ.get('FLASK_ENV', 'development') == 'production'

app = Flask(__name__, template_folder='templates', static_folder='static')

# Security: Use environment variable in production, fallback for development
app.secret_key = os.environ.get('SECRET_KEY', 'videopress-dev-key-change-in-production')

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = IS_PRODUCTION  # HTTPS only in production

# File configuration - use absolute paths for cPanel compatibility
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
SESSION_DATA_FILE = os.path.join(BASE_DIR, 'session_data.json')
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'webm', 'm4v', '3gp'}
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'tiff'}
ALLOWED_EXTENSIONS = ALLOWED_VIDEO_EXTENSIONS | ALLOWED_IMAGE_EXTENSIONS
MAX_FILE_SIZE = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB default
FILE_EXPIRY_HOURS = int(os.environ.get('FILE_EXPIRY_HOURS', 24))  # Auto-delete after 24 hours

# Set max content length for Flask
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


# =============================================================================
# SESSION DATA PERSISTENCE
# =============================================================================

def load_session_data():
    """Load all session data from file"""
    if os.path.exists(SESSION_DATA_FILE):
        try:
            with open(SESSION_DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_session_data(data):
    """Save all session data to file"""
    try:
        with open(SESSION_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving session data: {e}")


def get_session_id():
    """Get session ID from cookie or create new one"""
    session_id = request.cookies.get('vp_session')
    if not session_id:
        session_id = f"{int(time.time())}_{uuid.uuid4().hex[:12]}"
    return session_id


def get_user_data(session_id):
    """Get user's session data, creating if needed"""
    all_data = load_session_data()
    if session_id not in all_data:
        all_data[session_id] = {
            'created': datetime.now().isoformat(),
            'uploads': {},
            'outputs': {}
        }
        save_session_data(all_data)
    return all_data[session_id]


def update_user_data(session_id, user_data):
    """Update user's session data"""
    all_data = load_session_data()
    all_data[session_id] = user_data
    save_session_data(all_data)


def make_session_response(data, session_id, is_json=True):
    """Create response with session cookie"""
    if is_json:
        response = make_response(jsonify(data))
    else:
        response = make_response(data)
    
    response.set_cookie(
        'vp_session',
        session_id,
        max_age=7 * 24 * 60 * 60,  # 7 days
        httponly=True,
        samesite='Lax'
    )
    return response


# =============================================================================
# FILE CLEANUP
# =============================================================================

def cleanup_expired_files():
    """Remove files older than 24 hours"""
    all_data = load_session_data()
    current_time = datetime.now()
    sessions_to_remove = []
    modified = False
    
    for session_id, user_data in list(all_data.items()):
        files_to_remove = []
        
        # Check uploads for expiry
        for file_id, file_info in list(user_data.get('uploads', {}).items()):
            timestamp = file_info.get('timestamp')
            if timestamp:
                try:
                    file_time = datetime.fromisoformat(timestamp)
                    if current_time - file_time > timedelta(hours=FILE_EXPIRY_HOURS):
                        # Delete the file
                        file_path = file_info.get('path', '')
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except:
                                pass
                        files_to_remove.append(file_id)
                        modified = True
                except:
                    pass
        
        # Remove expired files from session data
        for file_id in files_to_remove:
            if file_id in user_data.get('uploads', {}):
                del user_data['uploads'][file_id]
            
            # Also delete associated outputs
            if file_id in user_data.get('outputs', {}):
                for output in user_data['outputs'][file_id]:
                    output_path = output.get('path', '')
                    if output_path and os.path.exists(output_path):
                        try:
                            os.remove(output_path)
                        except:
                            pass
                del user_data['outputs'][file_id]
        
        # Check if session is empty and old
        if not user_data.get('uploads') and not user_data.get('outputs'):
            created = user_data.get('created')
            if created:
                try:
                    created_time = datetime.fromisoformat(created)
                    if current_time - created_time > timedelta(hours=FILE_EXPIRY_HOURS):
                        sessions_to_remove.append(session_id)
                        modified = True
                except:
                    pass
    
    # Remove empty sessions
    for session_id in sessions_to_remove:
        if session_id in all_data:
            del all_data[session_id]
    
    if modified:
        save_session_data(all_data)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def is_video_file(filename):
    """Check if file is a video"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS


def is_image_file(filename):
    """Check if file is an image"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def format_size(size_bytes):
    """Format bytes to human-readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_user_folder(session_id, folder_type='upload'):
    """Get user's session-specific folder"""
    base = UPLOAD_FOLDER if folder_type == 'upload' else OUTPUT_FOLDER
    folder = os.path.join(base, session_id)
    os.makedirs(folder, exist_ok=True)
    return folder


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    """Serve main page"""
    # Run cleanup in background
    threading.Thread(target=cleanup_expired_files, daemon=True).start()
    
    session_id = get_session_id()
    response = make_response(render_template('index.html'))
    response.set_cookie(
        'vp_session',
        session_id,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        samesite='Lax'
    )
    return response


@app.route('/upload', methods=['POST'])
def upload_video():
    """Handle video upload with session tracking"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    if 'video' not in request.files:
        return make_session_response({'success': False, 'error': 'No video file provided'}, session_id)
    
    file = request.files['video']
    
    if file.filename == '':
        return make_session_response({'success': False, 'error': 'No file selected'}, session_id)
    
    if not allowed_file(file.filename):
        return make_session_response({
            'success': False, 
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
        }, session_id)
    
    try:
        # Generate unique file ID with timestamp
        file_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Save file
        original_name = file.filename
        safe_name = secure_filename(f"{file_id}_{original_name}")
        upload_folder = get_user_folder(session_id, 'upload')
        file_path = os.path.join(upload_folder, safe_name)
        
        file.save(file_path)
        
        # Get video info
        video_info = probe_video(file_path)
        
        if not video_info:
            os.remove(file_path)
            return make_session_response({'success': False, 'error': 'Could not analyze video'}, session_id)
        
        # Store file info with timestamp
        file_data = {
            'id': file_id,
            'original_name': original_name,
            'path': file_path,
            'size': video_info.file_size,
            'duration': video_info.duration,
            'width': video_info.width,
            'height': video_info.height,
            'fps': video_info.fps,
            'timestamp': datetime.now().isoformat()
        }
        
        user_data['uploads'][file_id] = file_data
        update_user_data(session_id, user_data)
        
        return make_session_response({
            'success': True,
            'file_id': file_id,
            'filename': original_name,
            'size': format_size(video_info.file_size),
            'size_bytes': video_info.file_size,
            'duration': round(video_info.duration, 2),
            'resolution': f"{video_info.width}x{video_info.height}",
            'fps': round(video_info.fps, 2),
            'needs_split': video_info.duration > 30
        }, session_id)
        
    except Exception as e:
        return make_session_response({'success': False, 'error': str(e)}, session_id)


@app.route('/compress', methods=['POST'])
def compress():
    """Compress video with selected algorithm"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    data = request.get_json()
    file_id = data.get('file_id')
    algorithm = data.get('algorithm', 'neural_preserve')
    split_duration = data.get('split_duration', 0)
    
    # Validate file exists
    if file_id not in user_data.get('uploads', {}):
        return make_session_response({'success': False, 'error': 'File not found in session'}, session_id)
    
    file_info = user_data['uploads'][file_id]
    input_path = file_info['path']
    
    if not os.path.exists(input_path):
        return make_session_response({'success': False, 'error': 'File no longer exists'}, session_id)
    
    try:
        # Map algorithm
        algo_map = {
            'neural_preserve': Algorithm.NEURAL_PRESERVE,
            'bitrate_sculptor': Algorithm.BITRATE_SCULPTOR,
            'quantum_compress': Algorithm.QUANTUM_COMPRESS
        }
        selected_algo = algo_map.get(algorithm, Algorithm.NEURAL_PRESERVE)
        
        output_folder = get_user_folder(session_id, 'output')
        results = []
        output_files = []
        
        video_duration = file_info['duration']
        
        if split_duration > 0 and video_duration > split_duration:
            # Split then compress
            split_folder = os.path.join(output_folder, f"{file_id}_splits")
            os.makedirs(split_folder, exist_ok=True)
            
            split_result = split_video(
                input_path,
                split_folder,
                split_duration,
                f"{file_id}_segment"
            )
            
            if not split_result.success:
                return make_session_response({'success': False, 'error': split_result.message}, session_id)
            
            # Compress each segment
            for i, segment_path in enumerate(split_result.segments):
                output_name = f"{file_id}_part{i+1:02d}.mp4"
                output_path = os.path.join(output_folder, output_name)
                
                result = compress_video(segment_path, output_path, selected_algo)
                
                if result.success:
                    output_files.append({
                        'part': i + 1,
                        'path': output_path,
                        'name': output_name,
                        'size': format_size(result.compressed_size),
                        'size_bytes': result.compressed_size,
                        'timestamp': datetime.now().isoformat()
                    })
                    results.append({
                        'part': i + 1,
                        'success': True,
                        'compression_ratio': round(result.compression_ratio, 1)
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
            
            result = compress_video(input_path, output_path, selected_algo)
            
            if result.success:
                output_files.append({
                    'part': 1,
                    'path': output_path,
                    'name': output_name,
                    'size': format_size(result.compressed_size),
                    'size_bytes': result.compressed_size,
                    'timestamp': datetime.now().isoformat()
                })
                results.append({
                    'part': 1,
                    'success': True,
                    'original_size': format_size(result.original_size),
                    'compressed_size': format_size(result.compressed_size),
                    'compression_ratio': round(result.compression_ratio, 1)
                })
            else:
                return make_session_response({'success': False, 'error': result.message}, session_id)
        
        # Store outputs
        user_data['outputs'][file_id] = output_files
        update_user_data(session_id, user_data)
        
        return make_session_response({
            'success': True,
            'file_id': file_id,
            'algorithm': algorithm,
            'results': results,
            'outputs': output_files,
            'total_parts': len(output_files)
        }, session_id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return make_session_response({'success': False, 'error': str(e)}, session_id)


# =============================================================================
# PHOTO ROUTES
# =============================================================================

@app.route('/upload/photo', methods=['POST'])
def upload_photo():
    """Handle photo upload with session tracking"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    if 'photo' not in request.files:
        return make_session_response({'success': False, 'error': 'No photo file provided'}, session_id)
    
    file = request.files['photo']
    
    if file.filename == '':
        return make_session_response({'success': False, 'error': 'No file selected'}, session_id)
    
    if not is_image_file(file.filename):
        return make_session_response({
            'success': False,
            'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'
        }, session_id)
    
    try:
        # Generate unique file ID
        file_id = f"photo_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Save file
        original_name = file.filename
        safe_name = secure_filename(f"{file_id}_{original_name}")
        upload_folder = get_user_folder(session_id, 'upload')
        file_path = os.path.join(upload_folder, safe_name)
        
        file.save(file_path)
        
        # Get photo info
        photo_info = analyze_photo(file_path)
        
        if not photo_info:
            os.remove(file_path)
            return make_session_response({'success': False, 'error': 'Could not analyze photo'}, session_id)
        
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
        update_user_data(session_id, user_data)
        
        return make_session_response({
            'success': True,
            'file_id': file_id,
            'filename': original_name,
            'size': format_size(photo_info.file_size),
            'size_bytes': photo_info.file_size,
            'width': photo_info.width,
            'height': photo_info.height,
            'resolution': f"{photo_info.width}x{photo_info.height}",
            'format': photo_info.format,
            'is_animated': photo_info.is_animated,
            'type': 'photo'
        }, session_id)
        
    except Exception as e:
        return make_session_response({'success': False, 'error': str(e)}, session_id)


@app.route('/compress/photo', methods=['POST'])
def compress_photo_route():
    """Compress photo with selected algorithm"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    data = request.get_json()
    file_id = data.get('file_id')
    algorithm = data.get('algorithm', 'balanced_pro')
    output_format = data.get('format', 'jpg')
    
    # Validate file exists
    if file_id not in user_data.get('uploads', {}):
        return make_session_response({'success': False, 'error': 'File not found in session'}, session_id)
    
    file_info = user_data['uploads'][file_id]
    input_path = file_info['path']
    
    if not os.path.exists(input_path):
        return make_session_response({'success': False, 'error': 'File no longer exists'}, session_id)
    
    try:
        # Map algorithm
        algo_map = {
            'clarity_max': PhotoAlgorithm.CLARITY_MAX,
            'balanced_pro': PhotoAlgorithm.BALANCED_PRO,
            'quick_share': PhotoAlgorithm.QUICK_SHARE
        }
        selected_algo = algo_map.get(algorithm, PhotoAlgorithm.BALANCED_PRO)
        
        output_folder = get_user_folder(session_id, 'output')
        
        # Determine output extension
        ext = output_format.lower()
        if ext not in ('jpg', 'jpeg', 'png', 'webp', 'gif'):
            ext = 'jpg'
        
        output_name = f"{file_id}_compressed.{ext}"
        output_path = os.path.join(output_folder, output_name)
        
        result = compress_photo(input_path, output_path, selected_algo, ext)
        
        if result.success:
            # Update output path with actual extension (may have changed)
            actual_name = os.path.basename(result.output_path)
            
            output_files = [{
                'part': 1,
                'path': result.output_path,
                'name': actual_name,
                'size': format_size(result.compressed_size),
                'size_bytes': result.compressed_size,
                'format': result.output_format,
                'dimensions': f"{result.new_dimensions[0]}x{result.new_dimensions[1]}",
                'timestamp': datetime.now().isoformat()
            }]
            
            # Store outputs
            user_data['outputs'][file_id] = output_files
            update_user_data(session_id, user_data)
            
            return make_session_response({
                'success': True,
                'file_id': file_id,
                'algorithm': algorithm,
                'original_size': format_size(result.original_size),
                'compressed_size': format_size(result.compressed_size),
                'compression_ratio': round(result.compression_ratio, 1),
                'output_format': result.output_format,
                'new_dimensions': result.new_dimensions,
                'message': result.message,
                'outputs': output_files
            }, session_id)
        else:
            return make_session_response({'success': False, 'error': result.message}, session_id)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return make_session_response({'success': False, 'error': str(e)}, session_id)


@app.route('/convert/video-to-gif', methods=['POST'])
def convert_video_to_gif():
    """Convert video to GIF"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    data = request.get_json()
    file_id = data.get('file_id')
    max_duration = data.get('duration', 6.0)
    fps = data.get('fps', 12)
    
    # Validate file exists
    if file_id not in user_data.get('uploads', {}):
        return make_session_response({'success': False, 'error': 'File not found'}, session_id)
    
    file_info = user_data['uploads'][file_id]
    input_path = file_info['path']
    
    if not os.path.exists(input_path):
        return make_session_response({'success': False, 'error': 'File no longer exists'}, session_id)
    
    try:
        output_folder = get_user_folder(session_id, 'output')
        output_name = f"{file_id}_converted.gif"
        output_path = os.path.join(output_folder, output_name)
        
        result = video_to_gif(
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
                'size': format_size(result.compressed_size),
                'size_bytes': result.compressed_size,
                'format': 'GIF',
                'timestamp': datetime.now().isoformat()
            }]
            
            user_data['outputs'][file_id] = output_files
            update_user_data(session_id, user_data)
            
            return make_session_response({
                'success': True,
                'file_id': file_id,
                'compressed_size': format_size(result.compressed_size),
                'message': result.message,
                'outputs': output_files
            }, session_id)
        else:
            return make_session_response({'success': False, 'error': result.message}, session_id)
        
    except Exception as e:
        return make_session_response({'success': False, 'error': str(e)}, session_id)


@app.route('/download/<file_id>/<int:part>')
def download(file_id, part):
    """Download compressed file"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    if file_id not in user_data.get('outputs', {}):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    outputs = user_data['outputs'][file_id]
    
    for output in outputs:
        if output['part'] == part:
            if os.path.exists(output['path']):
                return send_file(
                    output['path'],
                    as_attachment=True,
                    download_name=output['name']
                )
    
    return jsonify({'success': False, 'error': 'File not found'}), 404


@app.route('/session/files')
def get_session_files():
    """Get all files in current session"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    uploads = []
    for file_id, info in user_data.get('uploads', {}).items():
        file_data = {
            'id': file_id,
            'original_name': info.get('original_name', ''),
            'size': info.get('size', 0),
            'width': info.get('width', 0),
            'height': info.get('height', 0),
            'timestamp': info.get('timestamp', ''),
            'type': info.get('type', 'video')  # Default to video for backwards compat
        }
        # Add video-specific fields
        if info.get('type') != 'photo':
            file_data['duration'] = info.get('duration', 0)
        # Add photo-specific fields
        else:
            file_data['format'] = info.get('format', '')
            file_data['is_animated'] = info.get('is_animated', False)
        
        uploads.append(file_data)
    
    return make_session_response({
        'session_id': session_id,
        'uploads': uploads,
        'outputs': user_data.get('outputs', {})
    }, session_id)


@app.route('/delete/<file_id>', methods=['DELETE'])
def delete_file(file_id):
    """Delete a specific file"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    # Delete upload
    if file_id in user_data.get('uploads', {}):
        file_path = user_data['uploads'][file_id].get('path', '')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        del user_data['uploads'][file_id]
    
    # Delete outputs
    if file_id in user_data.get('outputs', {}):
        for output in user_data['outputs'][file_id]:
            output_path = output.get('path', '')
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
        del user_data['outputs'][file_id]
    
    update_user_data(session_id, user_data)
    
    return make_session_response({'success': True}, session_id)


@app.route('/session/clear', methods=['POST'])
def clear_session():
    """Clear all files for current session"""
    session_id = get_session_id()
    user_data = get_user_data(session_id)
    
    # Delete all uploads
    for file_id, info in user_data.get('uploads', {}).items():
        file_path = info.get('path', '')
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
    
    # Delete all outputs
    for file_id, outputs in user_data.get('outputs', {}).items():
        for output in outputs:
            output_path = output.get('path', '')
            if output_path and os.path.exists(output_path):
                try:
                    os.remove(output_path)
                except:
                    pass
    
    # Remove session folders
    try:
        upload_folder = os.path.join(UPLOAD_FOLDER, session_id)
        if os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
    except:
        pass
    
    try:
        output_folder = os.path.join(OUTPUT_FOLDER, session_id)
        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
    except:
        pass
    
    # Clear session from data file
    all_data = load_session_data()
    if session_id in all_data:
        del all_data[session_id]
    save_session_data(all_data)
    
    # Create new session
    new_session_id = f"{int(time.time())}_{uuid.uuid4().hex[:12]}"
    
    response = make_response(jsonify({'success': True, 'new_session_id': new_session_id}))
    response.set_cookie(
        'vp_session',
        new_session_id,
        max_age=7 * 24 * 60 * 60,
        httponly=True,
        samesite='Lax'
    )
    return response


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
    }), 413


@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# =============================================================================
# MAIN - Only runs when executed directly (not via WSGI)
# =============================================================================

# Run cleanup on import (for both local and WSGI)
cleanup_expired_files()

if __name__ == '__main__':
    # Local development server
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5001)),
        debug=not IS_PRODUCTION
    )
