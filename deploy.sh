#!/bin/bash

# Exit on error
set -e

echo "Starting deployment..."

# Build and start containers
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

echo "Deployment completed successfully!"