# ⚡️ Knowledge Base Console

A modern knowledge base management system with document parsing, indexing, and semantic search capabilities.

## 🚀 Features

- **Document Management**: Upload and parse PDF, DOCX, MD, TXT files using Docling DocumentConverter
- **Project Organization**: Create and manage multiple knowledge base projects
- **Smart Indexing**: Build searchable indexes from parsed documents
- **Semantic Search**: Query your knowledge base using ChromaDB vector search
- **Cloud Storage**: Automatically store parsed markdown files on Dropbox
- **Modern UI**: Clean, responsive interface built with React 19 and Tailwind CSS

## 📦 Getting Started

### Prerequisites

- **uv**: Fast Python package installer and resolver
- **Node.js**: For frontend development
- **Dropbox Account**: For document storage (optional but recommended)

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Install uv if you haven't already:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env and add your Dropbox access token
```

4. Start the server:
```bash
./start.sh
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## 🔧 API Endpoints

- `POST /projects` - Create a new project
- `GET /projects` - List all projects
- `POST /projects/{project_id}/documents` - Upload a document
- `GET /projects/{project_id}/documents` - List project documents
- `POST /projects/{project_id}/parse-next` - Parse next pending document
- `POST /projects/{project_id}/indexes` - Create an index
- `GET /projects/{project_id}/indexes` - List project indexes
- `POST /query` - Query an index (requires project_id as param, index_id in body)

## 📁 Project Structure

```
├── backend/                 # FastAPI backend
│   ├── services/           # Business logic services
│   │   ├── parsing.py     # Docling document converter
│   │   ├── dropbox_storage.py # Dropbox integration
│   │   └── chroma_store.py # Vector database
│   ├── main.py            # API endpoints
│   └── start.sh           # Startup script (uses uv)
├── src/                    # React frontend
│   ├── pages/             # Page components
│   ├── components/        # Reusable UI components
│   └── routes/            # Application routing
└── package.json           # Frontend dependencies
```

## 🎯 Usage

1. **Create a Project**: Start by creating a new knowledge base project
2. **Upload Documents**: Add PDF, DOCX, MD, or TXT files to your project
3. **Parse Documents**: Process documents using Docling with OCR support
4. **Cloud Storage**: Parsed markdown is automatically uploaded to Dropbox
5. **Build Indexes**: Create searchable indexes from completed documents
6. **Query Knowledge**: Use the Query tab to search your indexed documents

## 🔍 Search

The system uses ChromaDB for vector similarity search, allowing you to find relevant information even with natural language queries.

## ☁️ Dropbox Integration

- Parsed markdown files are automatically uploaded to Dropbox
- Files are organized by project: `/parsed/{project_id}/{doc_id}.md`
- Shared links are generated for easy access
- Local markdown files are cleaned up after upload

## 🛠️ Technology Stack

- **Backend**: FastAPI, Docling, ChromaDB, Dropbox API
- **Frontend**: React 19, TypeScript, Tailwind CSS v4
- **Package Management**: uv (Python), npm (Node.js)
- **Vector Database**: ChromaDB for embeddings and similarity search

## 🚨 Troubleshooting

### Import Errors
If you encounter import errors like "cannot import name 'DocumentConverter'", the issue has been resolved by:
- Moving the Docling import inside the function to avoid circular imports
- Cleaning up duplicate files and consolidating logic
- Using proper import paths

### Startup Issues
The startup script now includes import checks to catch any dependency issues early. If the import check fails:
1. Ensure all dependencies are installed: `uv pip install -r requirements.txt`
2. Check that you're using Python 3.8+ and uv
3. Verify your environment variables are set correctly
