#!/bin/bash
set -e

# Export PYTHONPATH to ensure modules can be found by all workers
export PYTHONPATH="/app/src:$PYTHONPATH"

# Change to app directory
cd /app

# Setup Python path for uvicorn workers
echo "Starting Line Chatbot with gunicorn..."
echo "PYTHONPATH: $PYTHONPATH"
echo "Workers: ${WORKERS:-4}"

# Use gunicorn for better production performance with multiple workers
exec uv run gunicorn -c gunicorn.conf.py src.main:app
