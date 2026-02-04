# 📹 MediaPress - WhatsApp Video & Photo Compressor

A powerful Python web application that compresses videos and photos optimized for WhatsApp Status, ensuring your media stays **crystal clear and blur-free** after upload.

**🌐 Live Demo:** [http://compress.ugnews24.info:5001](http://compress.ugnews24.info:5001)

![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### Video Compression
- **3 Unique Video Algorithms** - Neural Preserve, Bitrate Sculptor, Quantum Compress
- **AI-Enhanced Compression** - Machine learning analyzes content for optimal settings
- **Video Splitting** - Automatically split videos into 30s or 60s segments
- **Video to GIF** - Convert short videos to optimized GIFs

### Photo Compression
- **3 Photo Algorithms** - Clarity Max, Balanced Pro, Quick Share
- **Smart Content Detection** - Detects photos, graphics, screenshots, text
- **Animated GIF Support** - Optimizes animated GIFs with color reduction
- **Multiple Output Formats** - JPG, PNG, WebP support

### General
- **Session-Based Storage** - Files persist using cookies (7-day retention)
- **Split Parts Access** - Download individual parts from history
- **Modern Web Interface** - Clean, responsive design with video/photo mode toggle
- **WhatsApp Optimized** - Pre-compressed to prevent quality loss on upload

## 🧠 AI-Powered Features

The Neural Preserve algorithm includes **machine learning** for smarter compression:

- **Face Detection** - Detects faces and prioritizes quality in face regions
- **Content Classification** - Identifies talking heads, action, nature, screen content
- **Scene Complexity Analysis** - Measures visual complexity for optimal bitrate
- **Motion Estimation** - Uses optical flow to detect movement levels
- **Adaptive Parameters** - CRF, bitrate, and filters auto-tuned per content type

```
Content Type       │ CRF  │ Bitrate Mult │ Optimization
───────────────────┼──────┼──────────────┼─────────────────────
Talking Head       │ 18   │ 1.2x         │ Face detail priority
Group People       │ 19   │ 1.15x        │ Multi-face handling
Action/Sports      │ 20   │ 1.1x         │ Motion preservation
Nature/Landscape   │ 19   │ 1.1x         │ Color & detail
Screen Content     │ 18   │ 1.0x         │ Text sharpness
General            │ 20   │ 1.0x         │ Balanced
```

## 🎯 The Problem

When you upload a video to WhatsApp Status, WhatsApp aggressively re-compresses it:
- Reduces resolution to ~720p or lower
- Drops bitrate to ~1-2 Mbps
- Results in **blurry, pixelated videos**

## 💡 The Solution

MediaPress **pre-compresses your video** to match WhatsApp's expected specifications, so WhatsApp has minimal re-compression to do, preserving your video quality!

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** installed and in PATH

#### Install FFmpeg

**Windows:**
```powershell
# Download FFmpeg and extract to C:\ffmpeg
# Add C:\ffmpeg\bin to system PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mediapress.git
cd mediapress

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open your browser to **http://localhost:5001**

---

## 🖥️ Windows Server Deployment

MediaPress can run as a Windows Service that persists across reboots.

### Using NSSM (Recommended)

```powershell
# Install NSSM
# Download from https://nssm.cc and place nssm.exe in C:\ffmpeg\bin

# Install the service
nssm.exe install MediaPress "C:\path\to\venv\Scripts\python.exe" "C:\path\to\service_runner.py"

# Configure auto-start
nssm.exe set MediaPress Start SERVICE_AUTO_START
nssm.exe set MediaPress AppDirectory "C:\path\to\project"

# Start the service
nssm.exe start MediaPress
```

### Service Management

```powershell
# Check status
Get-Service MediaPress

# Stop service
nssm.exe stop MediaPress

# Start service
nssm.exe start MediaPress

# Restart service
nssm.exe restart MediaPress

# Remove service
nssm.exe remove MediaPress confirm
```

### Service Logs

- `service.log` - Application logs
- `service_stdout.log` - Standard output
- `service_stderr.log` - Error logs

---

## 🧠 Compression Algorithms

### 1. Neural Preserve 🧠 (AI-Enhanced)
**Best for:** Detailed videos, faces, artistic content

| Aspect | Details |
|--------|---------|
| Strategy | AI-powered content analysis with adaptive encoding |
| Resolution | Up to 1080p |
| CRF | 17-21 (AI-selected based on content) |
| Preset | `veryslow` (maximum quality) |
| Special | Face detection, content classification, motion analysis |

### 2. Bitrate Sculptor 🎨
**Best for:** Vlogs, mixed content, general videos

| Aspect | Details |
|--------|---------|
| Strategy | 2-pass encoding with dynamic bitrate allocation |
| Resolution | 720p |
| Encoding | Target bitrate calculated from file size budget |
| Preset | `medium` (balanced speed/quality) |

### 3. Quantum Compress 🚀
**Best for:** Quick sharing, low bandwidth, bulk processing

| Aspect | Details |
|--------|---------|
| Strategy | Maximum compression with aggressive settings |
| Resolution | 640p |
| CRF | 28 (higher compression) |
| Preset | `faster` (quick encoding) |

### Algorithm Comparison

```
┌─────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Feature             │ Neural Preserve  │ Bitrate Sculptor │ Quantum Compress │
├─────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Quality             │ ★★★★★           │ ★★★★☆           │ ★★★☆☆           │
│ File Size           │ ★★★☆☆           │ ★★★★☆           │ ★★★★★           │
│ Speed               │ ★★☆☆☆           │ ★★★☆☆           │ ★★★★★           │
│ Best For            │ Detail/Faces     │ General Use      │ Quick Share      │
└─────────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## 🖼️ Photo Compression Algorithms

### 1. Clarity Max 👁️
Maximum quality preservation with intelligent enhancement.
- Max Resolution: 1280px
- Quality: 92% JPEG
- Features: Smart sharpening, color enhancement

### 2. Balanced Pro ⚖️
Balanced quality and file size.
- Max Resolution: 1080px
- Quality: 85% JPEG
- Features: Adaptive quality, format optimization

### 3. Quick Share 📤
Fast, lightweight compression.
- Max Resolution: 800px
- Quality: 78% JPEG
- Features: Fast processing, small file sizes

---

## 📡 REST API

MediaPress includes a complete REST API with OpenAPI/Swagger documentation.

### API Documentation

**Swagger UI:** `http://your-server:5001/api/v1/docs`  
**API Base URL:** `http://your-server:5001/api/v1`

See [API_DOCS.md](API_DOCS.md) for complete API documentation.

### Quick API Example

```bash
# Upload a video
curl -X POST "http://localhost:5001/api/v1/video/upload" \
  -F "video=@my-video.mp4"

# Compress the video
curl -X POST "http://localhost:5001/api/v1/video/compress" \
  -H "Content-Type: application/json" \
  -d '{"file_id": "YOUR_FILE_ID", "algorithm": "neural_preserve"}'

# Download the result
curl -O "http://localhost:5001/api/v1/video/download/YOUR_FILE_ID/1"
```

### API Endpoints Overview

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Video | `/api/v1/video/upload` | POST | Upload video |
| Video | `/api/v1/video/compress` | POST | Compress video |
| Video | `/api/v1/video/download/{id}/{part}` | GET | Download video |
| Photo | `/api/v1/photo/upload` | POST | Upload photo |
| Photo | `/api/v1/photo/compress` | POST | Compress photo |
| Photo | `/api/v1/photo/gif` | POST | Convert to GIF |
| Session | `/api/v1/session/files` | GET | List files |
| Session | `/api/v1/session/clear` | POST | Clear session |
| Utility | `/api/v1/utility/health` | GET | Health check |
| Utility | `/api/v1/utility/algorithms` | GET | List algorithms |

---

## ⚙️ Configuration

Environment variables (optional):

```bash
# Secret key for sessions
export SECRET_KEY="your-secret-key-here"

# Run in production mode
export FLASK_ENV=production

# Custom FFmpeg path (Windows)
export FFMPEG_PATH="C:\ffmpeg\bin"
```

---

## 📱 WhatsApp Status Specifications

| Parameter | Limit |
|-----------|-------|
| Max Duration | 30 seconds |
| Max File Size | ~16 MB |
| Resolution | Usually downscaled to 720p |
| Codec | H.264 |
| Container | MP4 |

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- [FFmpeg](https://ffmpeg.org/) - The backbone of video processing
- [ffmpeg-python](https://github.com/kkroening/ffmpeg-python) - Python bindings for FFmpeg
- [Waitress](https://docs.pylonsproject.org/projects/waitress/) - Production WSGI server
- [NSSM](https://nssm.cc/) - Windows Service Manager

---

**🌐 Live at:** [http://compress.ugnews24.info:5001](http://compress.ugnews24.info:5001)

**Made with ❤️ for blur-free WhatsApp statuses!**
