#!/bin/bash

# Exit on error
set -e

echo "Starting deployment..."

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo "Deployment complete!"