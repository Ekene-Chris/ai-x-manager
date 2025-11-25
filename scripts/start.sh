#!/bin/bash
# Production startup script for AI X Account Manager

set -e

echo "Starting AI X Account Manager..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure your credentials."
    exit 1
fi

# Initialize database
echo "Initializing database..."
python -c "from app.database import init_db; init_db(); print('Database initialized successfully')"

# Start the application
echo "Starting FastAPI server..."
if [ "$ENVIRONMENT" = "production" ]; then
    # Production mode
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --workers ${WORKERS:-4} \
        --log-level ${LOG_LEVEL:-info}
else
    # Development mode
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --reload \
        --log-level ${LOG_LEVEL:-info}
fi
