#!/bin/bash

# Create staticfiles directory if it doesn't exist and set permissions
mkdir -p /app/staticfiles
chmod 755 /app/staticfiles

# Create media directory if it doesn't exist and set permissions  
mkdir -p /app/media
chmod 755 /app/media

# Run database migrations
python manage.py migrate

# Collect static files (skip if it fails due to permissions)
python manage.py collectstatic --noinput || echo "Warning: Could not collect static files"

# Start the Django development server
python manage.py runserver 0.0.0.0:8000
