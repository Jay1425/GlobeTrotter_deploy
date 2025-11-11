#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create instance directory if it doesn't exist
mkdir -p instance

# Initialize the database
python init_db.py

echo "Build completed successfully!"
