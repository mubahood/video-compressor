# VideoPress Server Deployment Guide

## Quick Start

### 1. Server Requirements
- Ubuntu 20.04+ or similar Linux
- Python 3.9+
- FFmpeg installed (`sudo apt install ffmpeg`)
- 2GB+ RAM recommended

### 2. Clone & Setup

```bash
# Clone your repo
git clone https://github.com/yourusername/video-compressor.git /var/www/videopress
cd /var/www/videopress

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create directories
mkdir -p uploads outputs

# Configure environment
cp .env.example .env
nano .env  # Edit with your settings
```

### 3. Generate Secret Key

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output to SECRET_KEY in .env
```

### 4. Test Run

```bash
# Quick test
./start.sh

# Or manually
gunicorn -c gunicorn.conf.py app:app
```

Visit `http://YOUR_SERVER_IP:5001` to verify it works.

---

## Production Setup

### Option A: Systemd Service (Recommended)

```bash
# Copy service file
sudo cp videopress.service /etc/systemd/system/

# Edit paths if needed
sudo nano /etc/systemd/system/videopress.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable videopress
sudo systemctl start videopress

# Check status
sudo systemctl status videopress
```

### Option B: Direct with Gunicorn

```bash
# Run in background with nohup
nohup ./start.sh > /var/log/videopress.log 2>&1 &
```

---

## Nginx Reverse Proxy (Recommended)

```bash
# Install Nginx
sudo apt install nginx

# Copy config
sudo cp nginx.conf.example /etc/nginx/sites-available/videopress

# Edit domain/IP
sudo nano /etc/nginx/sites-available/videopress

# Enable site
sudo ln -s /etc/nginx/sites-available/videopress /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## Firewall Setup

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 5001/tcp  # Only if not using Nginx
sudo ufw enable
```

---

## Common Commands

```bash
# View logs
sudo journalctl -u videopress -f

# Restart service
sudo systemctl restart videopress

# Check if running
sudo systemctl status videopress

# Update application
cd /var/www/videopress
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart videopress
```

---

## Directory Structure on Server

```
/var/www/videopress/
├── app.py
├── gunicorn.conf.py
├── start.sh
├── .env
├── requirements.txt
├── venv/
├── uploads/
├── outputs/
├── templates/
└── src/
```

---

## Troubleshooting

**Port already in use:**
```bash
sudo lsof -i :5001
sudo kill -9 <PID>
```

**Permission denied:**
```bash
sudo chown -R www-data:www-data /var/www/videopress
sudo chmod +x start.sh
```

**FFmpeg not found:**
```bash
sudo apt update
sudo apt install ffmpeg
ffmpeg -version
```
