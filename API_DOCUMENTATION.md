# Doc KB API Documentation

## Overview
Each document gets its own separate collection in the vector database, identified by a unique job ID. This allows for isolated querying of individual documents.

## API Endpoints

### 1. Upload Document
**POST** `/upload`

Upload a document and get a file ID for processing.

**Response:**
```json
{
  "file_id": "uuid-string",
  "document_name": "example.pdf",
  "job_id": "job-uuid-string"
}
```

### 2. Process Document
**POST** `/ingest`

Process a document and create a dedicated collection.

**Request Body:**
```json
{
  "file_id": "uuid-string",
  "document_name": "example.pdf",
  "chunk_mode": "auto",  // "auto" or "manual"
  "chunk_size": 1000,    // only for manual mode
  "chunk_overlap": 200   // only for manual mode
}
```

**Response:**
```json
{
  "document_name": "example.pdf",
  "num_chunks": 25,
  "chunk_ids": ["chunk1", "chunk2", ...],
  "job_id": "job-uuid-string"
}
```

### 3. Query Specific Document
**POST** `/query`

Query a specific document using its job ID.

**Request Body:**
```json
{
  "question": "What are the main findings?",
  "top_k": 5,
  "job_id": "job-uuid-string"
}
```

**Response:**
```json
{
  "answer": "Based on the document content, here are the most relevant findings...",
  "contexts": [
    {
      "chunk_id": "chunk1",
      "score": 0.95,
      "text": "Relevant text from the document...",
      "metadata": {
        "document_name": "example.pdf",
        "job_id": "job-uuid-string"
      }
    }
  ]
}
```

### 4. Query All Documents (Legacy)
**POST** `/query`

Query across all documents (legacy behavior).

**Request Body:**
```json
{
  "question": "What are the main findings?",
  "top_k": 5
}
```

### 5. Check Job Status
**GET** `/jobs/{job_id}`

Get the status of a processing job.

**Response:**
```json
{
  "id": "job-uuid-string",
  "type": "ingest",
  "status": "completed",
  "document_name": "example.pdf",
  "num_chunks": 25,
  "started_at": "2025-08-19T01:00:00Z",
  "finished_at": "2025-08-19T01:02:00Z"
}
```

### 6. List All Collections
**GET** `/collections`

Get a list of all available document collections.

**Response:**
```json
{
  "collections": [
    {
      "collection_name": "kb_example_pdf_12345678",
      "job_id": "job-uuid-string",
      "document_name": "example.pdf",
      "status": "completed",
      "num_chunks": 25,
      "created_at": "2025-08-19T01:00:00Z",
      "completed_at": "2025-08-19T01:02:00Z"
    }
  ],
  "total": 1
}
```

### 7. Get Collection Info
**GET** `/collections/{job_id}`

Get information about a specific collection.

**Response:**
```json
{
  "collection_name": "kb_example_pdf_12345678",
  "job_id": "job-uuid-string",
  "document_name": "example.pdf",
  "status": "completed",
  "num_chunks": 25,
  "created_at": "2025-08-19T01:00:00Z",
  "completed_at": "2025-08-19T01:02:00Z"
}
```

## Workflow for External Applications

### Step 1: Upload Document
```bash
curl -X POST "http://localhost:8000/upload" \
  -F "file=@document.pdf"
```

### Step 2: Process Document
```bash
curl -X POST "http://localhost:8000/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "file_id": "file-uuid",
    "document_name": "document.pdf",
    "chunk_mode": "auto"
  }'
```

### Step 3: Monitor Job Status
```bash
curl "http://localhost:8000/jobs/job-uuid"
```

### Step 4: Query Document
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is this document about?",
    "top_k": 5,
    "job_id": "job-uuid"
  }'
```

## Collection Naming Convention

Collections are named using the pattern:
```
kb_{sanitized_document_name}_{job_id_prefix}
```

Example:
- Document: `Research Paper.pdf`
- Job ID: `12345678-1234-1234-1234-123456789abc`
- Collection: `kb_Research_Paper_pdf_12345678`

## Features

### ✅ **Per-Document Collections**
- Each document gets its own isolated collection
- No cross-contamination between documents
- Individual querying and management

### ✅ **Job ID Tracking**
- Unique job ID for each document processing
- Job status tracking and monitoring
- Collection discovery via job ID

### ✅ **Flexible Chunking**
- Auto mode: Optimized hybrid chunking
- Manual mode: Custom chunk size and overlap
- Configurable parameters

### ✅ **Production Ready**
- Telemetry completely disabled
- Local storage support
- Error handling and logging

## Error Handling

### Common Error Responses

**404 - Job Not Found:**
```json
{
  "detail": "No collection found for job_id: job-uuid"
}
```

**500 - Processing Error:**
```json
{
  "detail": "Processing failed: Error message"
}
```

## Integration Examples

### Python Client
```python
import requests

# Upload document
with open('document.pdf', 'rb') as f:
    upload_response = requests.post('http://localhost:8000/upload', files={'file': f})
    file_data = upload_response.json()

# Process document
ingest_response = requests.post('http://localhost:8000/ingest', json={
    'file_id': file_data['file_id'],
    'document_name': file_data['document_name'],
    'chunk_mode': 'auto'
})
job_id = ingest_response.json()['job_id']

# Query document
query_response = requests.post('http://localhost:8000/query', json={
    'question': 'What is this document about?',
    'job_id': job_id,
    'top_k': 5
})
answer = query_response.json()['answer']
```

### JavaScript Client
```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const uploadResponse = await fetch('http://localhost:8000/upload', {
  method: 'POST',
  body: formData
});
const fileData = await uploadResponse.json();

// Process document
const ingestResponse = await fetch('http://localhost:8000/ingest', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    file_id: fileData.file_id,
    document_name: fileData.document_name,
    chunk_mode: 'auto'
  })
});
const { job_id } = await ingestResponse.json();

// Query document
const queryResponse = await fetch('http://localhost:8000/query', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: 'What is this document about?',
    job_id: job_id,
    top_k: 5
  })
});
const { answer } = await queryResponse.json();
```

This API provides a complete solution for document processing and querying with isolated collections per document.