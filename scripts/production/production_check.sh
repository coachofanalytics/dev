#!/bin/bash
# Simple production database check

echo ""
echo "🔍 Checking Production Database..."
echo ""

/usr/local/bin/heroku run "python discover_production.py" --app codatrainingapp

echo ""
echo "✅ Discovery Complete!"
echo ""

