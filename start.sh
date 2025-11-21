#!/bin/bash
set -e

echo "Starting TruFan API..."

# Run database migrations
echo "Running database migrations..."
cd backend && alembic upgrade head

# Start the application
echo "Starting uvicorn server..."
uvicorn app.main:app --host 0.0.0.0 --port $PORT
