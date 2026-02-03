# 📹 MediaPress - WhatsApp Video & Photo Compressor

A powerful Python web application that compresses videos and photos optimized for WhatsApp Status, ensuring your media stays **crystal clear and blur-free** after upload.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![FFmpeg](https://img.shields.io/badge/FFmpeg-required-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### Video Compression
- **3 Unique Video Algorithms** - Neural Preserve, Bitrate Sculptor, Quantum Compress
- **AI-Enhanced Compression** - Machine learning analyzes content for optimal settings
- **Video Splitting** - Automatically split videos into 30s or 60s segments
- **Video to GIF** - Convert short videos to optimized GIFs

### Photo Compression (NEW!)
- **3 Photo Algorithms** - Clarity Max, Balanced Pro, Quick Share
- **Smart Content Detection** - Detects photos, graphics, screenshots, text
- **Animated GIF Support** - Optimizes animated GIFs with color reduction
- **Multiple Output Formats** - JPG, PNG, WebP support

### General
- **Session-Based Storage** - Files persist using cookies (7-day retention)
- **Split Parts Access** - Download individual parts from history
- **Modern Web Interface** - Clean, responsive design with video/photo mode toggle
- **WhatsApp Optimized** - Pre-compressed to prevent quality loss on upload

## 🧠 AI-Powered Features (NEW!)

The Neural Preserve algorithm now includes **machine learning** for smarter compression:

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

This app **pre-compresses your video** to match WhatsApp's expected specifications, so WhatsApp has minimal re-compression to do, preserving your video quality!

---

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** installed and in PATH

#### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/video-compressor.git
cd video-compressor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

Open your browser to **http://localhost:5000**

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

**AI/ML Features:**
- **Face Detection** using OpenCV DNN or Haar cascades
- **Content Classification** (talking head, action, nature, screen, etc.)
- **Scene Complexity Analysis** via edge detection and histogram variance
- **Motion Estimation** using optical flow analysis
- **Adaptive CRF** selected based on content type and complexity

**Technical Features:**
- Content-adaptive psycho-visual optimization (psy-rd)
- Lanczos scaling for sharpest downscaling
- Content-aware denoising (hqdn3d)
- Adaptive sharpening based on content type
- Film-grade color handling (BT.709)

### 2. Bitrate Sculptor 🎨
**Best for:** Vlogs, mixed content, general videos

| Aspect | Details |
|--------|---------|
| Strategy | 2-pass encoding with dynamic bitrate allocation |
| Resolution | 720p |
| Encoding | Target bitrate calculated from file size budget |
| Preset | `medium` (balanced speed/quality) |
| Special | Analyzes scene complexity for optimal bit distribution |

**Technical Features:**
- 2-pass encoding for precise bitrate control
- Scene change detection (scenecut=40)
- Adaptive B-frame decisions (b-adapt=2)
- Temporal denoising (hqdn3d) for cleaner compression

### 3. Quantum Compress 🚀
**Best for:** Quick sharing, low bandwidth, bulk processing

| Aspect | Details |
|--------|---------|
| Strategy | Maximum compression with aggressive settings |
| Resolution | 640p |
| CRF | 28 (higher compression) |
| Preset | `faster` (quick encoding) |
| Special | Mono audio, reduced framerate |

**Technical Features:**
- Aggressive noise reduction before encoding
- No B-frames for simplicity (bframes=0)
- Baseline profile for maximum compatibility
- Reduced audio bitrate (96kbps mono)

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
**Best for:** Portraits, detailed images, important photos

| Aspect | Details |
|--------|---------|
| Strategy | Maximum quality preservation with intelligent enhancement |
| Max Resolution | 1280px |
| Quality | 92% JPEG |
| Chroma | 4:4:4 (best color) |

**Features:**
- Smart sharpening to counteract WhatsApp compression
- Color/contrast enhancement optimized for mobile viewing
- Progressive JPEG for better perceived loading
- Content-type detection (photo, graphic, screenshot)

### 2. Balanced Pro ⚖️
**Best for:** General photos, social media sharing

| Aspect | Details |
|--------|---------|
| Strategy | Adaptive quality based on image content |
| Max Resolution | 1080px |
| Quality | 82-88% (content-adaptive) |
| Chroma | 4:2:2 (balanced) |

**Features:**
- Automatic quality adjustment based on content type
- Screenshots get higher quality for text clarity
- Moderate sharpening and enhancement
- Good balance between size and quality

### 3. Quick Share ⚡
**Best for:** Bulk sharing, low bandwidth, quick uploads

| Aspect | Details |
|--------|---------|
| Strategy | Maximum compression for smallest files |
| Max Resolution | 720px |
| Quality | 70% JPEG |
| Chroma | 4:2:0 (maximum compression) |

**Features:**
- Aggressive compression for fastest uploads
- Minimal processing for speed
- Still maintains acceptable WhatsApp quality
- Best for sharing many photos quickly

### Photo Algorithm Comparison

```
┌─────────────────────┬──────────────────┬──────────────────┬──────────────────┐
│ Feature             │ Clarity Max      │ Balanced Pro     │ Quick Share      │
├─────────────────────┼──────────────────┼──────────────────┼──────────────────┤
│ Quality             │ ★★★★★           │ ★★★★☆           │ ★★★☆☆           │
│ File Size           │ ★★★☆☆           │ ★★★★☆           │ ★★★★★           │
│ Best For            │ Portraits        │ General          │ Bulk Share       │
└─────────────────────┴──────────────────┴──────────────────┴──────────────────┘
```

---

## ✂️ Video Splitting

WhatsApp Status has a **30-second limit**. This app can automatically split longer videos:

| Option | Description |
|--------|-------------|
| **No Split** | Keep video as single file |
| **30 Seconds** | Split into WhatsApp Status-ready segments |
| **60 Seconds** | For platforms with longer limits |

---

## 🔒 Session Management

- **Cookie-based sessions** - Your files persist for 7 days
- **Session isolation** - Each user has their own storage
- **Split parts access** - Download individual parts from Recent Files history
- **Manual cleanup** - Clear your session anytime
- **Automatic cleanup** - Old sessions purged after 24 hours

---

## 📁 Project Structure

```
video-compressor/
├── app.py                    # Flask web application
├── requirements.txt          # Python dependencies
├── templates/
│   └── index.html           # Web interface (video & photo modes)
├── src/
│   ├── __init__.py
│   ├── algorithms.py        # 3 video compression algorithms
│   ├── photo_algorithms.py  # 3 photo compression algorithms (NEW)
│   ├── ml_analyzer.py       # ML-based video analysis (NEW)
│   └── splitter.py          # Video splitting module
├── uploads/                 # Uploaded files (per session)
├── outputs/                 # Compressed files (per session)
└── README.md
```

---

## 🛠️ API Endpoints

### Video Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload video file |
| `/compress` | POST | Process video compression |
| `/download/<file_id>/<part>` | GET | Download specific segment |

### Photo Endpoints (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload/photo` | POST | Upload photo file |
| `/compress/photo` | POST | Process photo compression |
| `/convert/video-to-gif` | POST | Convert video to GIF |

### Session Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main web interface |
| `/session/files` | GET | List session files (videos & photos) |
| `/session/clear` | POST | Clear all session data |
| `/delete/<file_id>` | DELETE | Delete specific file |
| `/health` | GET | Health check |

---

## ⚙️ Configuration

Environment variables (optional):

```bash
# Secret key for sessions (use strong random string in production)
export SECRET_KEY="your-secret-key-here"

# Run in production mode
export FLASK_ENV=production
```

---

## 📱 WhatsApp Status Specifications

For reference, WhatsApp Status uses these limits:

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
- Inspired by [PureStatus](https://play.google.com/store/apps/details?id=com.damtechdesigns.purepixel)

---

**Made with ❤️ for blur-free WhatsApp statuses!**
