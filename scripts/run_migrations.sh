#!/bin/bash
# Script to run database migrations

set -e

echo "Running database migrations..."

# Wait for database to be ready
echo "Waiting for database..."
sleep 5

# Run migrations
cd /app/..
alembic upgrade head

echo "Migrations completed successfully!"
