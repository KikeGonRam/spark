#!/bin/bash
set -e

echo "================================"
echo "BarberPro Python - Entrypoint"
echo "================================"

# Wait for MongoDB to be ready (if in docker)
echo "Checking MongoDB connection..."
for i in {1..30}; do
    if python -c "from pymongo import MongoClient; MongoClient('${MONGO_HOST}', serverSelectionTimeoutMS=2000)" 2>/dev/null; then
        echo "✓ MongoDB is ready"
        break
    fi
    echo "Waiting for MongoDB... ($i/30)"
    sleep 1
done

# Run migrations/seeders (if needed)
if [ "$1" = "seed" ]; then
    echo "Running database seeders..."
    python -m app.database.seeders.run_seeders
    echo "✓ Seeders complete"
fi

# Run tests (if needed)
if [ "$1" = "test" ]; then
    echo "Running tests..."
    pytest
    exit 0
fi

# Start the application
echo "Starting BarberPro application..."
exec "$@"
