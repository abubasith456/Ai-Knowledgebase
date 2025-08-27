# ⚡️ Knowledge Base Console

A modern knowledge base management system with document parsing, indexing, and semantic search capabilities.

## 🚀 Features

- **Document Management**: Upload and parse PDF, DOCX, MD, TXT files using Docling
- **Project Organization**: Create and manage multiple knowledge base projects
- **Smart Indexing**: Build searchable indexes from parsed documents
- **Semantic Search**: Query your knowledge base using ChromaDB vector search
- **Modern UI**: Clean, responsive interface built with React 19 and Tailwind CSS

## 📦 Getting Started

### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Start the server:
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
│   ├── main.py            # API endpoints
│   └── start.sh           # Startup script
├── src/                    # React frontend
│   ├── pages/             # Page components
│   ├── components/        # Reusable UI components
│   └── routes/            # Application routing
└── package.json           # Frontend dependencies
```

## 🎯 Usage

1. **Create a Project**: Start by creating a new knowledge base project
2. **Upload Documents**: Add PDF, DOCX, MD, or TXT files to your project
3. **Parse Documents**: Process documents to extract text and create chunks
4. **Build Indexes**: Create searchable indexes from completed documents
5. **Query Knowledge**: Use the Query tab to search your indexed documents

## 🔍 Search

The system uses ChromaDB for vector similarity search, allowing you to find relevant information even with natural language queries.
