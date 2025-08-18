#!/bin/bash

# Start the Doc KB application
echo "Starting Doc KB application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating default .env file..."
    cat > .env << EOF
# API Key Configuration
API_KEY_SECRET=your-secret-key-here-change-this-in-production-$(openssl rand -hex 32)

# Backend Configuration
CHROMA_DATA_DIR=/data/chroma
MODEL_NAME=jinaai/jina-embeddings-v3-small
COLLECTION_PREFIX=kb_
LOG_LEVEL=info

# Frontend Configuration
VITE_BACKEND_URL=http://localhost:8000

# ChromaDB Configuration
IS_PERSISTENT=TRUE
ANONYMIZED_TELEMETRY=FALSE
EOF
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Start with Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up --build -d

echo ""
echo "🚀 Doc KB is starting up!"
echo ""
echo "📊 Backend API: http://localhost:8000"
echo "🖥️  Frontend UI: http://localhost:5173"
echo "🔍 ChromaDB: http://localhost:8001"
echo ""
echo "📝 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
echo ""
echo "⏳ Please wait a moment for all services to fully start..."