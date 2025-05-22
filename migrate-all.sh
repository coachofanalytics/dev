#!/bin/bash

# Activate virtual environment (if needed)
# source venv/bin/activate  # For Unix/Mac
# venv\Scripts\activate     # For Windows

# Reset migrations
python manage.py migrate accounts zero
python manage.py migrate main zero
python manage.py migrate accounts zero

# Create new migrations
python manage.py makemigrations accounts
python manage.py makemigrations main

# Apply migrations
python manage.py migrate

# Optional: Run server
python manage.py runserver
