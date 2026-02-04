"""
Session API Endpoints
======================
Handles session management, file listing, and deletion.
"""

import os
import shutil
import time
import uuid
from flask import request, make_response
from flask_restx import Namespace, Resource

# Create namespace
session_ns = Namespace(
    'session',
    description='Session and file management operations',
    decorators=[]
)

from .models import create_models, get_session_id

# Lazy model initialization
_models = None

def get_models():
    global _models
    if _models is None:
        _models = create_models(session_ns)
    return _models


def get_config():
    """Get configuration from main app"""
    from app import (
        UPLOAD_FOLDER, OUTPUT_FOLDER,
        load_session_data, save_session_data, get_user_data, update_user_data,
        format_size
    )
    
    return {
        'UPLOAD_FOLDER': UPLOAD_FOLDER,
        'OUTPUT_FOLDER': OUTPUT_FOLDER,
        'load_session_data': load_session_data,
        'save_session_data': save_session_data,
        'get_user_data': get_user_data,
        'update_user_data': update_user_data,
        'format_size': format_size
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
# LIST SESSION FILES
# =============================================================================

@session_ns.route('/files')
class SessionFiles(Resource):
    @session_ns.doc(
        description='''
Get all files in the current session.

Returns a list of uploaded files (videos and photos) along with any
compressed outputs associated with each file.
        ''',
        responses={
            200: 'List of session files'
        }
    )
    def get(self):
        """Get all files in current session"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        uploads = []
        for file_id, info in user_data.get('uploads', {}).items():
            file_data = {
                'id': file_id,
                'original_name': info.get('original_name', ''),
                'size': config['format_size'](info.get('size', 0)),
                'size_bytes': info.get('size', 0),
                'width': info.get('width', 0),
                'height': info.get('height', 0),
                'timestamp': info.get('timestamp', ''),
                'type': info.get('type', 'video'),
                'has_output': file_id in user_data.get('outputs', {})
            }
            
            # Add video-specific fields
            if info.get('type') != 'photo':
                file_data['duration'] = info.get('duration', 0)
                file_data['fps'] = info.get('fps', 0)
            # Add photo-specific fields
            else:
                file_data['format'] = info.get('format', '')
                file_data['is_animated'] = info.get('is_animated', False)
            
            uploads.append(file_data)
        
        # Format outputs for API response (remove paths)
        outputs = {}
        for file_id, file_outputs in user_data.get('outputs', {}).items():
            outputs[file_id] = []
            for out in file_outputs:
                api_out = {k: v for k, v in out.items() if k != 'path'}
                outputs[file_id].append(api_out)
        
        return make_api_response({
            'success': True,
            'session_id': session_id,
            'file_count': len(uploads),
            'uploads': uploads,
            'outputs': outputs
        }, session_id)


# =============================================================================
# GET SESSION INFO
# =============================================================================

@session_ns.route('/info')
class SessionInfo(Resource):
    @session_ns.doc(
        description='Get information about the current session',
        responses={
            200: 'Session information'
        }
    )
    def get(self):
        """Get current session information"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        # Calculate totals
        total_upload_size = sum(
            info.get('size', 0) for info in user_data.get('uploads', {}).values()
        )
        total_output_size = 0
        for file_outputs in user_data.get('outputs', {}).values():
            for out in file_outputs:
                total_output_size += out.get('size_bytes', 0)
        
        video_count = sum(
            1 for info in user_data.get('uploads', {}).values() 
            if info.get('type') != 'photo'
        )
        photo_count = sum(
            1 for info in user_data.get('uploads', {}).values() 
            if info.get('type') == 'photo'
        )
        
        return make_api_response({
            'success': True,
            'session_id': session_id,
            'created': user_data.get('created', ''),
            'stats': {
                'total_uploads': len(user_data.get('uploads', {})),
                'video_count': video_count,
                'photo_count': photo_count,
                'total_outputs': sum(len(outs) for outs in user_data.get('outputs', {}).values()),
                'upload_size': config['format_size'](total_upload_size),
                'upload_size_bytes': total_upload_size,
                'output_size': config['format_size'](total_output_size),
                'output_size_bytes': total_output_size
            }
        }, session_id)


# =============================================================================
# DELETE FILE
# =============================================================================

@session_ns.route('/files/<string:file_id>')
@session_ns.param('file_id', 'The file ID to delete')
class SessionFile(Resource):
    @session_ns.doc(
        description='Get information about a specific file',
        responses={
            200: 'File information',
            404: 'File not found'
        }
    )
    def get(self, file_id):
        """Get specific file information"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        if file_id not in user_data.get('uploads', {}):
            return make_api_response({
                'success': False,
                'error': 'File not found'
            }, session_id, 404)
        
        info = user_data['uploads'][file_id]
        
        file_data = {
            'id': file_id,
            'original_name': info.get('original_name', ''),
            'size': config['format_size'](info.get('size', 0)),
            'size_bytes': info.get('size', 0),
            'width': info.get('width', 0),
            'height': info.get('height', 0),
            'timestamp': info.get('timestamp', ''),
            'type': info.get('type', 'video'),
            'has_output': file_id in user_data.get('outputs', {})
        }
        
        if info.get('type') != 'photo':
            file_data['duration'] = info.get('duration', 0)
            file_data['fps'] = info.get('fps', 0)
        else:
            file_data['format'] = info.get('format', '')
            file_data['is_animated'] = info.get('is_animated', False)
        
        # Include outputs if available
        if file_id in user_data.get('outputs', {}):
            file_data['outputs'] = [
                {k: v for k, v in out.items() if k != 'path'}
                for out in user_data['outputs'][file_id]
            ]
        
        return make_api_response({
            'success': True,
            'file': file_data
        }, session_id)
    
    @session_ns.doc(
        description='Delete a specific file and its outputs',
        responses={
            200: 'File deleted',
            404: 'File not found'
        }
    )
    def delete(self, file_id):
        """Delete a specific file"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        deleted_upload = False
        deleted_outputs = False
        
        # Delete upload
        if file_id in user_data.get('uploads', {}):
            file_path = user_data['uploads'][file_id].get('path', '')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
            del user_data['uploads'][file_id]
            deleted_upload = True
        
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
            deleted_outputs = True
        
        if not deleted_upload and not deleted_outputs:
            return make_api_response({
                'success': False,
                'error': 'File not found'
            }, session_id, 404)
        
        config['update_user_data'](session_id, user_data)
        
        return make_api_response({
            'success': True,
            'deleted_upload': deleted_upload,
            'deleted_outputs': deleted_outputs,
            'message': f'File {file_id} deleted successfully'
        }, session_id)


# =============================================================================
# CLEAR SESSION
# =============================================================================

@session_ns.route('/clear')
class ClearSession(Resource):
    @session_ns.doc(
        description='''
Clear all files from the current session.

This will:
- Delete all uploaded files
- Delete all compressed outputs
- Remove session folders
- Generate a new session ID
        ''',
        responses={
            200: 'Session cleared successfully'
        }
    )
    def post(self):
        """Clear all files from session"""
        config = get_config()
        session_id = get_session_id()
        user_data = config['get_user_data'](session_id)
        
        files_deleted = 0
        outputs_deleted = 0
        
        # Delete all uploads
        for file_id, info in user_data.get('uploads', {}).items():
            file_path = info.get('path', '')
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    files_deleted += 1
                except:
                    pass
        
        # Delete all outputs
        for file_id, outputs in user_data.get('outputs', {}).items():
            for output in outputs:
                output_path = output.get('path', '')
                if output_path and os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                        outputs_deleted += 1
                    except:
                        pass
        
        # Remove session folders
        try:
            upload_folder = os.path.join(config['UPLOAD_FOLDER'], session_id)
            if os.path.exists(upload_folder):
                shutil.rmtree(upload_folder)
        except:
            pass
        
        try:
            output_folder = os.path.join(config['OUTPUT_FOLDER'], session_id)
            if os.path.exists(output_folder):
                shutil.rmtree(output_folder)
        except:
            pass
        
        # Clear session from data file
        all_data = config['load_session_data']()
        if session_id in all_data:
            del all_data[session_id]
        config['save_session_data'](all_data)
        
        # Create new session
        new_session_id = f"{int(time.time())}_{uuid.uuid4().hex[:12]}"
        
        response = make_response({
            'success': True,
            'message': 'Session cleared successfully',
            'files_deleted': files_deleted,
            'outputs_deleted': outputs_deleted,
            'old_session_id': session_id,
            'new_session_id': new_session_id
        })
        response.set_cookie(
            'vp_session',
            new_session_id,
            max_age=7 * 24 * 60 * 60,
            httponly=True,
            samesite='Lax'
        )
        return response


# =============================================================================
# CREATE NEW SESSION
# =============================================================================

@session_ns.route('/new')
class NewSession(Resource):
    @session_ns.doc(
        description='Create a new session (without clearing existing files)',
        responses={
            200: 'New session created'
        }
    )
    def post(self):
        """Create a new session"""
        new_session_id = f"{int(time.time())}_{uuid.uuid4().hex[:12]}"
        
        response = make_response({
            'success': True,
            'session_id': new_session_id,
            'message': 'New session created'
        })
        response.set_cookie(
            'vp_session',
            new_session_id,
            max_age=7 * 24 * 60 * 60,
            httponly=True,
            samesite='Lax'
        )
        return response
