# 🛠️ Development Guide - Doc KB

## 🐛 Fixed Issues

### ✅ Import Issues Resolved
- **Added missing `Optional` import** to `backend/app/ingest.py` and `backend/app/query.py`
- **Fixed path permissions** in `backend/app/indices.py` with fallback directory support
- **Added robust directory creation** with error handling for development environments

### ✅ Path Issues Resolved
- **Fixed `/data/indices` permission errors** by using configurable paths
- **Added development-friendly defaults** that work in local environments
- **Created automatic directory setup** for development

## 🚀 Quick Start for Development

### 1. Backend Setup
```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Set up development environment (creates directories)
python3 setup_dev.py

# Test that imports work
python3 test_imports.py

# Start the development server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Frontend Setup (in another terminal)
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 3. Using Docker (Production-like)
```bash
# From project root
docker-compose up --build
```

## 📁 Directory Structure Created

The setup now creates these directories automatically:

```
backend/
├── data/
│   ├── indices/     # Index metadata storage
│   ├── uploads/     # Temporary file uploads
│   └── chroma/      # ChromaDB data (dev)
└── app/
    ├── main.py      # ✅ Fixed imports
    ├── ingest.py    # ✅ Added Optional import
    ├── query.py     # ✅ Added Optional import
    ├── indices.py   # ✅ Fixed path handling
    └── ...
```

## 🔧 Environment Variables

### Development (.env file created)
```env
# API Key Configuration
API_KEY_SECRET=your-secret-key-here-change-this-in-production-12345678901234567890

# Backend Configuration
CHROMA_DATA_DIR=/data/chroma
MODEL_NAME=jinaai/jina-embeddings-v3-small
COLLECTION_PREFIX=kb_
LOG_LEVEL=info
INDICES_DIR=./data/indices

# Frontend Configuration
VITE_BACKEND_URL=http://localhost:8000

# ChromaDB Configuration
IS_PERSISTENT=TRUE
ANONYMIZED_TELEMETRY=FALSE
```

### Development Override
For local development, the system automatically uses:
- `INDICES_DIR=./data/indices` (relative to backend directory)
- Falls back to temp directory if permissions fail

## 🧪 Testing

### Test Import Structure
```bash
cd backend
python3 test_imports.py
```

### Test API Endpoints
```bash
# Start server first
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Test health endpoint
curl http://localhost:8000/health

# Generate API key
curl -X POST http://localhost:8000/auth/generate-key
```

## 🔍 Troubleshooting

### Common Issues & Solutions

#### 1. Import Errors ✅ FIXED
**Problem**: `ModuleNotFoundError: Optional`
**Solution**: Added `Optional` import to all necessary files

#### 2. Permission Errors ✅ FIXED
**Problem**: `OSError: [Errno 30] Read-only file system: '/data'`
**Solution**: 
- Uses configurable `INDICES_DIR` environment variable
- Defaults to `./data/indices` for development
- Falls back to temp directory if needed

#### 3. Directory Not Found ✅ FIXED
**Problem**: `/data/indices` doesn't exist
**Solution**: 
- `setup_dev.py` creates all necessary directories
- Robust error handling with fallbacks

### Development Commands

```bash
# Backend development
cd backend
python3 setup_dev.py                    # Setup directories
python3 test_imports.py                 # Test imports
uvicorn app.main:app --reload           # Start with auto-reload

# Frontend development  
cd frontend
npm run dev                             # Start dev server

# Full stack with Docker
docker-compose up --build               # Production-like environment
```

## 🎯 New Features Working

All requested features are now working:

1. ✅ **Parser Tab**: Upload documents with parser selection
2. ✅ **Indexing Tab**: Create indices with custom names and parsers
3. ✅ **Query Tab**: Test queries and get integration code
4. ✅ **Dark/Light Mode**: Theme toggle with persistence
5. ✅ **Progress Bars**: Real-time progress for all operations
6. ✅ **Authentication**: API key generation and management

## 📚 API Endpoints

### Authentication
- `POST /auth/generate-key` - Generate new API key
- `POST /auth/register-key` - Register API key

### Parsers & Indices
- `GET /parsers` - List available parsers
- `GET /indices` - List user's indices
- `POST /indices` - Create new index
- `GET /indices/{id}` - Get index details

### Documents
- `POST /upload` - Upload document with parser selection
- `POST /ingest` - Ingest document to index
- `POST /query` - Query knowledge base

### Jobs
- `GET /jobs/{id}` - Get job status

## 🎉 Ready to Use!

Your Doc KB system is now fully functional with all import issues resolved and robust error handling. The development environment is set up to work seamlessly on any system.