# VideoPress - cPanel Deployment Guide

## 📋 Prerequisites

1. cPanel hosting with **Python Selector** or **Passenger** support
2. SSH access (recommended) or File Manager
3. FFmpeg installed on the server (contact your host if not available)

---

## 🚀 Step-by-Step Deployment

### Step 1: Upload Files

Upload all project files to your cPanel account:

```
/home/YOUR_USERNAME/videopress/
├── app.py
├── passenger_wsgi.py
├── wsgi.py
├── requirements.txt
├── .htaccess
├── .env.example
├── templates/
│   └── index.html
└── src/
    ├── __init__.py
    ├── algorithms.py
    ├── splitter.py
    ├── photo_algorithms.py
    └── ml_analyzer.py
```

**Note:** Replace `YOUR_USERNAME` with your actual cPanel username.

---

### Step 2: Set Up Python Application in cPanel

#### Option A: Using Python Selector (Recommended)

1. Log in to cPanel
2. Go to **Software** → **Setup Python App**
3. Click **Create Application**
4. Configure:
   - **Python version**: 3.9+ (3.10 or 3.11 recommended)
   - **Application root**: `videopress` (or your folder name)
   - **Application URL**: Your domain or subdomain
   - **Application startup file**: `passenger_wsgi.py`
   - **Application Entry point**: `application`
5. Click **Create**
6. Note the **virtual environment path** shown

#### Option B: Manual Setup

1. SSH into your server:
   ```bash
   ssh username@yourdomain.com
   ```

2. Navigate to your app directory:
   ```bash
   cd ~/videopress
   ```

3. Create virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

---

### Step 3: Install Dependencies

**⚠️ IMPORTANT: Use the cPanel-specific requirements file to avoid installation errors!**

#### Via cPanel Python Selector:
1. In the Python App settings, scroll to **Configuration files**
2. Change the configuration file from `requirements.txt` to `requirements-cpanel.txt`
3. Click **Run Pip Install**

#### Via SSH:
```bash
cd ~/videopress
source venv/bin/activate
pip install -r requirements-cpanel.txt
```

**Note:** The `requirements-cpanel.txt` excludes opencv and numpy which often fail on shared hosting. The app will work perfectly without them - only the AI-enhanced compression feature is disabled.

#### Via SSH:
```bash
cd ~/videopress
source venv/bin/activate
pip install -r requirements.txt
```

---

### Step 4: Configure Environment Variables

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with secure values:
   ```bash
   nano .env
   ```
   
   Update these values:
   ```
   FLASK_ENV=production
   FLASK_DEBUG=0
   SECRET_KEY=your-very-long-random-secure-key-here
   ```

   **Generate a secure key:**
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```

---

### Step 5: Update .htaccess

Edit `.htaccess` with your actual paths:

```apache
PassengerEnabled On
PassengerAppRoot /home/YOUR_USERNAME/videopress
PassengerPython /home/YOUR_USERNAME/videopress/venv/bin/python

SetEnv FLASK_ENV production
SetEnv SECRET_KEY your-secure-secret-key-here
```

---

### Step 6: Create Required Directories

```bash
cd ~/videopress
mkdir -p uploads outputs
chmod 755 uploads outputs
```

---

### Step 7: Verify FFmpeg

Check if FFmpeg is available:
```bash
which ffmpeg
ffmpeg -version
```

If not installed, contact your hosting provider or use a VPS.

---

### Step 8: Restart Application

#### Via cPanel:
1. Go to **Setup Python App**
2. Find your application
3. Click **Restart**

#### Via SSH:
```bash
touch ~/videopress/tmp/restart.txt
```

---

## 🔧 Troubleshooting

### Check Error Logs
```bash
tail -f ~/logs/error.log
```

### Common Issues

**1. 500 Internal Server Error**
- Check file permissions: `chmod 755 *.py`
- Verify virtual environment path in `.htaccess`
- Check error logs

**2. Module Not Found**
- Ensure all dependencies are installed
- Verify `passenger_wsgi.py` path settings

**3. FFmpeg Not Found**
- Contact hosting provider
- Or use a VPS where you have root access

**4. Permission Denied on uploads**
```bash
chmod 755 uploads outputs
chown -R username:username uploads outputs
```

**5. Application Not Starting**
- Verify Python version compatibility
- Check `passenger_wsgi.py` syntax

---

## 📁 File Structure After Deployment

```
/home/YOUR_USERNAME/videopress/
├── app.py                 # Main Flask application
├── passenger_wsgi.py      # Passenger entry point
├── wsgi.py               # Alternative WSGI entry
├── requirements.txt       # Python dependencies
├── .htaccess             # Apache/Passenger config
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment file
├── templates/
│   └── index.html        # Web interface
├── src/
│   ├── __init__.py
│   ├── algorithms.py     # Video compression
│   ├── splitter.py       # Video splitting
│   ├── photo_algorithms.py # Photo compression
│   └── ml_analyzer.py    # ML analysis
├── uploads/              # Uploaded files (auto-created)
├── outputs/              # Compressed files (auto-created)
└── venv/                 # Virtual environment
```

---

## 🔒 Security Checklist

- [ ] Changed `SECRET_KEY` in `.env`
- [ ] Set `FLASK_ENV=production`
- [ ] Set `FLASK_DEBUG=0`
- [ ] Verified `.htaccess` has correct paths
- [ ] File permissions set correctly (755 for directories, 644 for files)
- [ ] uploads/outputs directories are not publicly accessible

---

## 🌐 Testing

After deployment, visit your domain to test:

1. **Video Upload**: Try uploading a small video file
2. **Video Compression**: Test each algorithm
3. **Photo Upload**: Try uploading an image
4. **Photo Compression**: Test compression and format conversion
5. **Download**: Verify downloads work correctly

---

## 📞 Support

If you encounter issues:
1. Check cPanel error logs
2. Verify all paths in configuration files
3. Ensure FFmpeg is available on the server
4. Contact your hosting provider for server-specific issues

---

## 🔄 Updates

To update the application:
1. Upload new files
2. Restart the Python application in cPanel
3. Clear browser cache if needed
