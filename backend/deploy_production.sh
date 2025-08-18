#!/bin/bash

# Production Deployment Script for Doc KB Backend
# Ensures ChromaDB telemetry is completely disabled

set -e  # Exit on any error

echo "🚀 Deploying Doc KB Backend (Production Mode)..."

# Set environment variables
export ANONYMIZED_TELEMETRY=FALSE
export CHROMA_TELEMETRY=FALSE
export MODEL_NAME=jinaai/jina-embeddings-v3
export PYTHONUNBUFFERED=1

# Create data directory
mkdir -p ./data/chroma

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Clean up old collections (if any)
echo "🧹 Cleaning up old collections..."
python -c "
import os
os.environ['ANONYMIZED_TELEMETRY'] = 'FALSE'
os.environ['CHROMA_TELEMETRY'] = 'FALSE'
from app.chroma_client import cleanup_incompatible_collections
cleanup_incompatible_collections()
"

# Start the server
echo "🚀 Starting production server..."
echo "🔇 ChromaDB telemetry completely disabled"
echo "📁 Using local storage at ./data/chroma"
echo "🤖 Using embedding model: jinaai/jina-embeddings-v3"
echo "=" * 60

python production_start.py