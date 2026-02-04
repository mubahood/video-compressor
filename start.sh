#!/bin/bash
# VideoPress Production Startup Script

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
fi

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Create required directories
mkdir -p uploads outputs

# Start with Gunicorn
echo "Starting VideoPress on port ${PORT:-5001}..."
exec gunicorn -c gunicorn.conf.py app:app
