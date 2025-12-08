#!/usr/bin/env bash
# exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create uploads directory if it doesn't exist
mkdir -p uploads/products
mkdir -p uploads/avatar
mkdir -p uploads/reviews

echo "Build completed successfully!"