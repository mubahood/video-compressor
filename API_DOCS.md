# MediaPress API Documentation

## Overview

The MediaPress API is a complete REST API for video and photo compression optimized for WhatsApp Status. It provides full programmatic access to all compression features with OpenAPI/Swagger documentation.

**Base URL:** `http://your-server:5001/api/v1`  
**Swagger Docs:** `http://your-server:5001/api/v1/docs`

---

## Quick Start

### 1. Upload a Video
```bash
curl -X POST "http://localhost:5001/api/v1/video/upload" \
  -F "video=@/path/to/your-video.mp4"
```

### 2. Compress the Video
```bash
curl -X POST "http://localhost:5001/api/v1/video/compress" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "YOUR_FILE_ID", "algorithm": "neural_preserve"}'
```

### 3. Download the Result
```bash
curl -O "http://localhost:5001/api/v1/video/download/YOUR_FILE_ID/1"
```

---

## Authentication

The API uses session-based authentication. Sessions are managed via cookies or headers.

| Method | Description |
|--------|-------------|
| **Cookie** | `vp_session` cookie (automatic in browsers) |
| **Header** | `X-Session-ID: your-session-id` (for API clients) |

Sessions are created automatically on first request and expire after 7 days.

---

## Rate Limits & Constraints

| Constraint | Value |
|------------|-------|
| Max file size | 500 MB |
| File expiry | 24 hours |
| Session duration | 7 days |
| Max video duration | Unlimited (split for WhatsApp) |
| WhatsApp status limit | 30 seconds, ~16 MB |

---

## Endpoints Overview

### Video Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/video/upload` | Upload a video file |
| `POST` | `/video/compress` | Compress a video |
| `GET` | `/video/download/{file_id}/{part}` | Download compressed video |
| `GET` | `/video/{file_id}` | Get video file info |

### Photo Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/photo/upload` | Upload a photo |
| `POST` | `/photo/compress` | Compress a photo |
| `POST` | `/photo/gif` | Convert video to GIF |
| `GET` | `/photo/download/{file_id}/{part}` | Download compressed photo |
| `GET` | `/photo/{file_id}` | Get photo file info |

### Session Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/session/` | Get session info |
| `GET` | `/session/files` | List all session files |
| `DELETE` | `/session/files/{file_id}` | Delete a specific file |
| `POST` | `/session/clear` | Clear all session data |

### Utility Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/utility/health` | API health check |
| `GET` | `/utility/algorithms` | List compression algorithms |
| `GET` | `/utility/limits` | Get API limits |
| `GET` | `/utility/formats` | Supported file formats |

---

## Video Compression Algorithms

### 1. Neural Preserve (`neural_preserve`)

**Best for:** Faces, detailed content, artistic videos

| Setting | Value |
|---------|-------|
| Quality | ★★★★★ |
| Speed | ★★☆☆☆ |
| Max Resolution | 1080p |
| CRF Range | 17-21 |
| FFmpeg Preset | veryslow |

**Features:**
- AI-powered content analysis
- Face detection for quality prioritization
- Scene complexity analysis
- Motion-adaptive encoding

### 2. Bitrate Sculptor (`bitrate_sculptor`)

**Best for:** Vlogs, general content, mixed videos

| Setting | Value |
|---------|-------|
| Quality | ★★★★☆ |
| Speed | ★★★☆☆ |
| Max Resolution | 720p |
| Encoding | 2-pass VBR |
| FFmpeg Preset | medium |

**Features:**
- Two-pass encoding
- Dynamic bitrate calculation
- File size optimization
- Balanced quality/size ratio

### 3. Quantum Compress (`quantum_compress`)

**Best for:** Quick sharing, bulk processing, low bandwidth

| Setting | Value |
|---------|-------|
| Quality | ★★★☆☆ |
| Speed | ★★★★★ |
| Max Resolution | 640p |
| CRF | 28 |
| FFmpeg Preset | faster |

**Features:**
- Maximum compression
- Fastest encoding
- Smallest file sizes
- Bulk processing friendly

---

## Photo Compression Algorithms

### 1. Clarity Max (`clarity_max`)

**Best for:** High-quality photos, portraits, print

| Setting | Value |
|---------|-------|
| Quality | ★★★★★ |
| Size Reduction | ★★★☆☆ |
| Max Resolution | 1280px |
| JPEG Quality | 92% |

### 2. Balanced Pro (`balanced_pro`)

**Best for:** General photos, social media

| Setting | Value |
|---------|-------|
| Quality | ★★★★☆ |
| Size Reduction | ★★★★☆ |
| Max Resolution | 1080px |
| JPEG Quality | 85% |

### 3. Quick Share (`quick_share`)

**Best for:** Quick sharing, thumbnails, previews

| Setting | Value |
|---------|-------|
| Quality | ★★★☆☆ |
| Size Reduction | ★★★★★ |
| Max Resolution | 800px |
| JPEG Quality | 78% |

---

## Detailed Endpoint Documentation

### Video Upload

**POST** `/api/v1/video/upload`

Upload a video file for compression.

**Request:**
```http
POST /api/v1/video/upload HTTP/1.1
Content-Type: multipart/form-data

video: [binary file data]
```

**Response:**
```json
{
  "success": true,
  "file_id": "1706184532_a1b2c3d4",
  "filename": "my-video.mp4",
  "size": "45.2 MB",
  "size_bytes": 47395328,
  "duration": 65.4,
  "resolution": "1920x1080",
  "fps": 30.0,
  "needs_split": true
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: mp4, mov, avi, mkv, webm, m4v, 3gp"
}
```

---

### Video Compress

**POST** `/api/v1/video/compress`

Compress a previously uploaded video.

**Request:**
```json
{
  "file_id": "1706184532_a1b2c3d4",
  "algorithm": "neural_preserve",
  "split_duration": 30
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | ✅ | File ID from upload response |
| `algorithm` | string | ❌ | `neural_preserve`, `bitrate_sculptor`, `quantum_compress` |
| `split_duration` | integer | ❌ | 0, 30, 60, or 90 seconds |

**Response:**
```json
{
  "success": true,
  "file_id": "1706184532_a1b2c3d4",
  "algorithm": "neural_preserve",
  "total_parts": 3,
  "results": [
    {
      "part": 1,
      "success": true,
      "original_size": "15.2 MB",
      "compressed_size": "4.8 MB",
      "compression_ratio": 68.4
    },
    {
      "part": 2,
      "success": true,
      "compressed_size": "4.5 MB",
      "compression_ratio": 70.2
    },
    {
      "part": 3,
      "success": true,
      "compressed_size": "3.9 MB",
      "compression_ratio": 74.3
    }
  ],
  "outputs": [
    {
      "part": 1,
      "name": "1706184532_a1b2c3d4_part01.mp4",
      "size": "4.8 MB",
      "size_bytes": 5033164,
      "download_url": "/api/v1/video/download/1706184532_a1b2c3d4/1"
    }
  ]
}
```

---

### Video Download

**GET** `/api/v1/video/download/{file_id}/{part}`

Download a compressed video file.

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_id` | string | File ID from compression response |
| `part` | integer | Part number (1 for single file, 1-N for split) |

**Response:** Binary video file with `Content-Disposition: attachment`

---

### Photo Upload

**POST** `/api/v1/photo/upload`

Upload a photo for compression.

**Request:**
```http
POST /api/v1/photo/upload HTTP/1.1
Content-Type: multipart/form-data

photo: [binary file data]
```

**Response:**
```json
{
  "success": true,
  "file_id": "photo_1706184532_a1b2c3d4",
  "filename": "my-photo.jpg",
  "size": "5.2 MB",
  "size_bytes": 5452595,
  "width": 4032,
  "height": 3024,
  "resolution": "4032x3024",
  "format": "JPEG",
  "is_animated": false,
  "type": "photo"
}
```

---

### Photo Compress

**POST** `/api/v1/photo/compress`

Compress a previously uploaded photo.

**Request:**
```json
{
  "file_id": "photo_1706184532_a1b2c3d4",
  "algorithm": "balanced_pro",
  "format": "jpg"
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | ✅ | File ID from upload response |
| `algorithm` | string | ❌ | `clarity_max`, `balanced_pro`, `quick_share` |
| `format` | string | ❌ | `jpg`, `png`, `webp` |

**Response:**
```json
{
  "success": true,
  "file_id": "photo_1706184532_a1b2c3d4",
  "algorithm": "balanced_pro",
  "original_size": "5.2 MB",
  "compressed_size": "892 KB",
  "compression_ratio": 83.2,
  "output_format": "JPEG",
  "new_dimensions": [1080, 810],
  "message": "Photo compressed successfully",
  "outputs": [
    {
      "part": 1,
      "name": "photo_1706184532_a1b2c3d4_compressed.jpg",
      "size": "892 KB",
      "size_bytes": 913408,
      "download_url": "/api/v1/photo/download/photo_1706184532_a1b2c3d4/1"
    }
  ]
}
```

---

### Video to GIF

**POST** `/api/v1/photo/gif`

Convert a video to an optimized GIF.

**Request:**
```json
{
  "file_id": "1706184532_a1b2c3d4",
  "duration": 5.0,
  "fps": 12
}
```

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_id` | string | ✅ | Video file ID |
| `duration` | float | ❌ | Max GIF duration (max 6 seconds) |
| `fps` | integer | ❌ | Frames per second (max 15) |

**Response:**
```json
{
  "success": true,
  "file_id": "1706184532_a1b2c3d4",
  "compressed_size": "2.1 MB",
  "message": "GIF created successfully",
  "outputs": [
    {
      "part": 1,
      "name": "1706184532_a1b2c3d4_converted.gif",
      "size": "2.1 MB",
      "format": "GIF",
      "download_url": "/api/v1/photo/download/1706184532_a1b2c3d4/1"
    }
  ]
}
```

---

### Session Info

**GET** `/api/v1/session/`

Get current session information.

**Response:**
```json
{
  "success": true,
  "session_id": "1706184532_a1b2c3d4e5f6",
  "created": "2026-02-04T10:15:32.123456",
  "stats": {
    "total_uploads": 5,
    "video_count": 3,
    "photo_count": 2,
    "upload_size": "125.4 MB",
    "upload_size_bytes": 131502694
  }
}
```

---

### List Session Files

**GET** `/api/v1/session/files`

Get all files in the current session.

**Response:**
```json
{
  "success": true,
  "session_id": "1706184532_a1b2c3d4e5f6",
  "uploads": [
    {
      "id": "1706184532_a1b2c3d4",
      "original_name": "video.mp4",
      "size": "45.2 MB",
      "size_bytes": 47395328,
      "width": 1920,
      "height": 1080,
      "duration": 65.4,
      "timestamp": "2026-02-04T10:15:32",
      "type": "video",
      "has_output": true
    }
  ],
  "outputs": {
    "1706184532_a1b2c3d4": [
      {
        "part": 1,
        "name": "1706184532_a1b2c3d4_compressed.mp4",
        "size": "12.3 MB"
      }
    ]
  }
}
```

---

### Delete File

**DELETE** `/api/v1/session/files/{file_id}`

Delete a specific file and its outputs.

**Response:**
```json
{
  "success": true,
  "deleted": {
    "uploads": 1,
    "outputs": 3
  }
}
```

---

### Clear Session

**POST** `/api/v1/session/clear`

Delete all files and create a new session.

**Response:**
```json
{
  "success": true,
  "new_session_id": "1706185678_b2c3d4e5f6g7"
}
```

---

### Health Check

**GET** `/api/v1/utility/health`

Check API health and capabilities.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "api_version": "v1",
  "timestamp": "2026-02-04T10:15:32.123456",
  "features": {
    "video_compression": true,
    "photo_compression": true,
    "video_splitting": true,
    "video_to_gif": true,
    "ffmpeg_available": true
  },
  "limits": {
    "max_file_size_mb": 500,
    "file_expiry_hours": 24,
    "session_duration_days": 7
  },
  "supported_formats": {
    "video": ["mp4", "mov", "avi", "mkv", "webm", "m4v", "3gp"],
    "image": ["jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"]
  }
}
```

---

### Algorithms Info

**GET** `/api/v1/utility/algorithms`

Get detailed information about all compression algorithms.

**Response:**
```json
{
  "video": [
    {
      "id": "neural_preserve",
      "name": "Neural Preserve",
      "description": "AI-powered compression with content analysis...",
      "quality": 5,
      "speed": 2,
      "compression": 3,
      "best_for": "Detailed videos, faces, artistic content",
      "features": ["Face detection", "Content-aware encoding", "..."],
      "settings": {
        "max_resolution": "1080p",
        "crf_range": "17-21",
        "preset": "veryslow"
      }
    }
  ],
  "photo": [
    {
      "id": "clarity_max",
      "name": "Clarity Max",
      "description": "Maximum quality preservation...",
      "quality": 5,
      "speed": 3,
      "compression": 3,
      "best_for": "High-quality photos, portraits"
    }
  ]
}
```

---

### API Limits

**GET** `/api/v1/utility/limits`

Get API limits and constraints.

**Response:**
```json
{
  "max_file_size_mb": 500,
  "max_file_size_bytes": 524288000,
  "file_expiry_hours": 24,
  "session_duration_days": 7,
  "whatsapp_status": {
    "max_duration_seconds": 30,
    "max_file_size_mb": 16,
    "recommended_resolution": "720p"
  },
  "video": {
    "max_duration": "unlimited",
    "max_resolution": "1080p",
    "split_options": [0, 30, 60, 90]
  },
  "photo": {
    "max_resolution": "1280px",
    "output_formats": ["jpg", "png", "webp"]
  },
  "gif": {
    "max_duration_seconds": 6,
    "max_fps": 15,
    "max_width": 360
  }
}
```

---

## Error Handling

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Descriptive error message"
}
```

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad request (invalid input) |
| 404 | File or resource not found |
| 413 | File too large |
| 500 | Server error |

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `No video file provided` | Missing form field | Use field name `video` |
| `Invalid file type` | Unsupported format | Check supported formats |
| `File not found in session` | Invalid file_id | Re-upload the file |
| `File no longer exists` | File expired (24h) | Re-upload the file |
| `Could not analyze video` | Corrupted file | Try different file |

---

## Code Examples

### Python

```python
import requests

BASE_URL = "http://localhost:5001/api/v1"
session = requests.Session()

# Upload video
with open("video.mp4", "rb") as f:
    response = session.post(f"{BASE_URL}/video/upload", files={"video": f})
    data = response.json()
    file_id = data["file_id"]

# Compress video
response = session.post(f"{BASE_URL}/video/compress", json={
    "file_id": file_id,
    "algorithm": "neural_preserve",
    "split_duration": 30
})
result = response.json()

# Download each part
for output in result["outputs"]:
    part = output["part"]
    response = session.get(f"{BASE_URL}/video/download/{file_id}/{part}")
    with open(f"compressed_part{part}.mp4", "wb") as f:
        f.write(response.content)
```

### JavaScript (Node.js)

```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const BASE_URL = 'http://localhost:5001/api/v1';

async function compressVideo() {
  // Upload
  const form = new FormData();
  form.append('video', fs.createReadStream('video.mp4'));
  
  const uploadRes = await axios.post(`${BASE_URL}/video/upload`, form, {
    headers: form.getHeaders()
  });
  
  const fileId = uploadRes.data.file_id;
  
  // Compress
  const compressRes = await axios.post(`${BASE_URL}/video/compress`, {
    file_id: fileId,
    algorithm: 'neural_preserve'
  });
  
  // Download
  for (const output of compressRes.data.outputs) {
    const downloadRes = await axios.get(
      `${BASE_URL}/video/download/${fileId}/${output.part}`,
      { responseType: 'stream' }
    );
    downloadRes.data.pipe(fs.createWriteStream(`part${output.part}.mp4`));
  }
}
```

### cURL

```bash
# Upload
FILE_ID=$(curl -s -X POST "http://localhost:5001/api/v1/video/upload" \
  -F "video=@video.mp4" | jq -r '.file_id')

# Compress
curl -X POST "http://localhost:5001/api/v1/video/compress" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\": \"$FILE_ID\", \"algorithm\": \"neural_preserve\"}"

# Download
curl -o compressed.mp4 "http://localhost:5001/api/v1/video/download/$FILE_ID/1"
```

---

## Swagger UI

Interactive API documentation is available at:

**`http://your-server:5001/api/v1/docs`**

The Swagger UI provides:
- Interactive endpoint testing
- Request/response examples
- Schema documentation
- Authentication setup

---

## Changelog

### v1.0.0 (February 2026)
- Initial API release
- Video compression with 3 algorithms
- Photo compression with 3 algorithms
- Video splitting (30s, 60s, 90s)
- Video to GIF conversion
- Session-based file management
- OpenAPI/Swagger documentation
