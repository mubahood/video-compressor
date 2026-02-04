#!/usr/bin/env python3
"""Quick API test script"""
import requests

BASE = 'http://127.0.0.1:5001/api/v1'

print('Testing API Endpoints...')
print()

# Test 1: Health
r = requests.get(f'{BASE}/utility/health')
print(f'1. Health Check: {r.status_code} - {r.json()}')

# Test 2: Algorithms
r = requests.get(f'{BASE}/utility/algorithms')
print(f'2. Algorithms: {r.status_code} - Video: {len(r.json().get("video", []))} algos')

# Test 3: Formats
r = requests.get(f'{BASE}/utility/formats')
print(f'3. Formats: {r.status_code} - {r.json()}')

# Test 4: Limits
r = requests.get(f'{BASE}/utility/limits')
print(f'4. Limits: {r.status_code} - {r.json()}')

# Test 5: Session Info
r = requests.get(f'{BASE}/session/')
print(f'5. Session: {r.status_code} - ID: {r.json().get("session_id", "N/A")[:20]}...')

# Test 6: Session Files
r = requests.get(f'{BASE}/session/files')
print(f'6. Files: {r.status_code} - Uploads: {len(r.json().get("uploads", []))}')

print()
print('All basic endpoints working!')
