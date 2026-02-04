#!/usr/bin/env python3
"""
MediaPress API Test Suite
=========================
Tests all API endpoints for correctness.
"""

import requests
import os
import sys
import json
import time

BASE_URL = "http://127.0.0.1:5001/api/v1"

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def log_pass(msg):
    print(f"{GREEN}✓ PASS{RESET}: {msg}")

def log_fail(msg):
    print(f"{RED}✗ FAIL{RESET}: {msg}")

def log_info(msg):
    print(f"{BLUE}ℹ INFO{RESET}: {msg}")

def log_section(msg):
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{msg}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

class APITester:
    def __init__(self):
        self.session = requests.Session()
        self.passed = 0
        self.failed = 0
        self.uploaded_video_id = None
        self.uploaded_photo_id = None
        
    def test_endpoint(self, method, endpoint, expected_status=200, **kwargs):
        """Test an endpoint and return response"""
        url = f"{BASE_URL}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            if response.status_code == expected_status:
                self.passed += 1
                return True, response
            else:
                self.failed += 1
                return False, response
        except Exception as e:
            self.failed += 1
            return False, str(e)
    
    # =========================================================================
    # UTILITY TESTS
    # =========================================================================
    
    def test_health(self):
        log_section("Testing Utility Endpoints")
        
        success, resp = self.test_endpoint("GET", "/utility/health")
        if success:
            data = resp.json()
            if data.get('status') == 'healthy':
                log_pass(f"Health check - Status: {data.get('status')}, Version: {data.get('version')}")
            else:
                log_fail(f"Health check returned unexpected status: {data}")
        else:
            log_fail(f"Health check failed: {resp}")
    
    def test_algorithms(self):
        success, resp = self.test_endpoint("GET", "/utility/algorithms")
        if success:
            data = resp.json()
            if 'video' in data and 'photo' in data:
                log_pass(f"Algorithms - Video: {len(data['video'])} algorithms, Photo: {len(data['photo'])} algorithms")
            else:
                log_fail(f"Algorithms response missing expected keys: {data}")
        else:
            log_fail(f"Algorithms endpoint failed: {resp}")
    
    def test_formats(self):
        success, resp = self.test_endpoint("GET", "/utility/formats")
        if success:
            data = resp.json()
            if 'video' in data and 'image' in data:
                log_pass(f"Formats - Video: {data['video']}, Image: {data['image'][:5]}...")
            else:
                log_fail(f"Formats response missing expected keys: {data}")
        else:
            log_fail(f"Formats endpoint failed: {resp}")
    
    def test_limits(self):
        success, resp = self.test_endpoint("GET", "/utility/limits")
        if success:
            data = resp.json()
            if 'max_file_size_mb' in data:
                log_pass(f"Limits - Max file: {data['max_file_size_mb']}MB, Expiry: {data.get('file_expiry_hours')}h")
            else:
                log_fail(f"Limits response missing expected keys: {data}")
        else:
            log_fail(f"Limits endpoint failed: {resp}")
    
    # =========================================================================
    # SESSION TESTS
    # =========================================================================
    
    def test_session_info(self):
        log_section("Testing Session Endpoints")
        
        success, resp = self.test_endpoint("GET", "/session/")
        if success:
            data = resp.json()
            if 'session_id' in data:
                log_pass(f"Session info - ID: {data['session_id'][:20]}...")
            else:
                log_fail(f"Session info missing session_id: {data}")
        else:
            log_fail(f"Session info failed: {resp}")
    
    def test_session_files(self):
        success, resp = self.test_endpoint("GET", "/session/files")
        if success:
            data = resp.json()
            if 'uploads' in data:
                log_pass(f"Session files - Uploads: {len(data['uploads'])}, Outputs: {len(data.get('outputs', {}))}")
            else:
                log_fail(f"Session files missing expected keys: {data}")
        else:
            log_fail(f"Session files failed: {resp}")
    
    # =========================================================================
    # VIDEO TESTS
    # =========================================================================
    
    def test_video_upload(self):
        log_section("Testing Video Endpoints")
        
        # Create a minimal test video file (not a real video, just for upload test)
        test_file_path = "/tmp/test_video.mp4"
        
        # Check if a real test video exists
        real_videos = [
            "/Users/mac/Desktop/github/video-compressor/uploads",
            "/Users/mac/Movies"
        ]
        
        test_video = None
        for path in real_videos:
            if os.path.exists(path):
                for f in os.listdir(path):
                    if f.endswith(('.mp4', '.mov', '.avi')):
                        test_video = os.path.join(path, f)
                        break
            if test_video:
                break
        
        if not test_video:
            log_info("No test video found - skipping upload test")
            return
        
        with open(test_video, 'rb') as f:
            files = {'video': (os.path.basename(test_video), f, 'video/mp4')}
            success, resp = self.test_endpoint("POST", "/video/upload", files=files)
        
        if success:
            data = resp.json()
            if data.get('success') and 'file_id' in data:
                self.uploaded_video_id = data['file_id']
                log_pass(f"Video upload - ID: {data['file_id']}, Size: {data.get('size')}")
            else:
                log_fail(f"Video upload returned error: {data.get('error', data)}")
        else:
            log_fail(f"Video upload failed: {resp}")
    
    def test_video_compress(self):
        if not self.uploaded_video_id:
            log_info("No uploaded video - skipping compression test")
            return
        
        payload = {
            "file_id": self.uploaded_video_id,
            "algorithm": "quantum_compress",  # Fastest algorithm
            "split_duration": 0
        }
        
        success, resp = self.test_endpoint("POST", "/video/compress", json=payload)
        if success:
            data = resp.json()
            if data.get('success'):
                log_pass(f"Video compress - Algorithm: {data.get('algorithm')}, Parts: {data.get('total_parts')}")
            else:
                log_fail(f"Video compress returned error: {data.get('error', data)}")
        else:
            log_fail(f"Video compress failed: {resp}")
    
    # =========================================================================
    # PHOTO TESTS
    # =========================================================================
    
    def test_photo_upload(self):
        log_section("Testing Photo Endpoints")
        
        # Look for a test image
        test_dirs = [
            "/Users/mac/Desktop/github/video-compressor/uploads",
            "/Users/mac/Pictures",
            "/Users/mac/Desktop"
        ]
        
        test_photo = None
        for path in test_dirs:
            if os.path.exists(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                            test_photo = os.path.join(root, f)
                            break
                    if test_photo:
                        break
            if test_photo:
                break
        
        if not test_photo:
            log_info("No test photo found - skipping upload test")
            return
        
        with open(test_photo, 'rb') as f:
            files = {'photo': (os.path.basename(test_photo), f, 'image/jpeg')}
            success, resp = self.test_endpoint("POST", "/photo/upload", files=files)
        
        if success:
            data = resp.json()
            if data.get('success') and 'file_id' in data:
                self.uploaded_photo_id = data['file_id']
                log_pass(f"Photo upload - ID: {data['file_id']}, Size: {data.get('size')}")
            else:
                log_fail(f"Photo upload returned error: {data.get('error', data)}")
        else:
            log_fail(f"Photo upload failed: {resp}")
    
    def test_photo_compress(self):
        if not self.uploaded_photo_id:
            log_info("No uploaded photo - skipping compression test")
            return
        
        payload = {
            "file_id": self.uploaded_photo_id,
            "algorithm": "quick_share",
            "format": "jpg"
        }
        
        success, resp = self.test_endpoint("POST", "/photo/compress", json=payload)
        if success:
            data = resp.json()
            if data.get('success'):
                log_pass(f"Photo compress - Ratio: {data.get('compression_ratio')}%, Format: {data.get('output_format')}")
            else:
                log_fail(f"Photo compress returned error: {data.get('error', data)}")
        else:
            log_fail(f"Photo compress failed: {resp}")
    
    # =========================================================================
    # ERROR HANDLING TESTS
    # =========================================================================
    
    def test_error_handling(self):
        log_section("Testing Error Handling")
        
        # Test invalid file_id
        payload = {"file_id": "nonexistent-id", "algorithm": "neural_preserve"}
        success, resp = self.test_endpoint("POST", "/video/compress", expected_status=404, json=payload)
        if success:
            log_pass("Invalid file_id returns 404")
        else:
            log_fail(f"Invalid file_id should return 404, got: {resp.status_code if hasattr(resp, 'status_code') else resp}")
        
        # Test invalid algorithm
        if self.uploaded_video_id:
            payload = {"file_id": self.uploaded_video_id, "algorithm": "invalid_algo"}
            success, resp = self.test_endpoint("POST", "/video/compress", expected_status=400, json=payload)
            if success:
                log_pass("Invalid algorithm returns 400")
            else:
                if hasattr(resp, 'status_code'):
                    log_fail(f"Invalid algorithm should return 400, got: {resp.status_code}")
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    def test_cleanup(self):
        log_section("Cleanup")
        
        # Delete uploaded files
        if self.uploaded_video_id:
            success, resp = self.test_endpoint("DELETE", f"/session/files/{self.uploaded_video_id}")
            if success:
                log_pass(f"Deleted video file: {self.uploaded_video_id}")
            else:
                log_fail(f"Failed to delete video: {resp}")
        
        if self.uploaded_photo_id:
            success, resp = self.test_endpoint("DELETE", f"/session/files/{self.uploaded_photo_id}")
            if success:
                log_pass(f"Deleted photo file: {self.uploaded_photo_id}")
            else:
                log_fail(f"Failed to delete photo: {resp}")
    
    # =========================================================================
    # RUN ALL TESTS
    # =========================================================================
    
    def run_all(self):
        print(f"\n{BLUE}MediaPress API Test Suite{RESET}")
        print(f"{BLUE}Base URL: {BASE_URL}{RESET}\n")
        
        # Utility tests
        self.test_health()
        self.test_algorithms()
        self.test_formats()
        self.test_limits()
        
        # Session tests
        self.test_session_info()
        self.test_session_files()
        
        # Video tests
        self.test_video_upload()
        self.test_video_compress()
        
        # Photo tests  
        self.test_photo_upload()
        self.test_photo_compress()
        
        # Error handling
        self.test_error_handling()
        
        # Cleanup
        self.test_cleanup()
        
        # Summary
        log_section("Test Summary")
        total = self.passed + self.failed
        print(f"Total: {total} tests")
        print(f"{GREEN}Passed: {self.passed}{RESET}")
        print(f"{RED}Failed: {self.failed}{RESET}")
        
        if self.failed == 0:
            print(f"\n{GREEN}All tests passed! ✓{RESET}\n")
        else:
            print(f"\n{RED}Some tests failed!{RESET}\n")
        
        return self.failed == 0


if __name__ == '__main__':
    tester = APITester()
    success = tester.run_all()
    sys.exit(0 if success else 1)
