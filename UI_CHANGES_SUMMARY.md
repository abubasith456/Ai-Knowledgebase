# UI Changes Summary

## Overview
Completely redesigned the Doc KB UI with a new two-tab structure and enhanced functionality as requested.

## Major Changes

### 1. New Tab Structure
- **Tab 1: "Upload & Process"** - Handles file upload, chunking configuration, and document processing
- **Tab 2: "Query"** - Handles knowledge base queries with configurable parameters

### 2. Backend API Enhancements

#### New Schemas (`backend/app/schemas.py`)
- Added `ChunkMode` enum with `AUTO` and `MANUAL` options
- Updated `IngestRequest` to include:
  - `chunk_mode: ChunkMode = ChunkMode.AUTO`
  - `chunk_size: Optional[int] = None`
  - `chunk_overlap: Optional[int] = None`
- Added `DocumentInfo` schema for document management

#### Enhanced Chunking (`backend/app/chunking.py`)
- Updated `hybrid_chunk_document()` function to accept optional `max_tokens` and `overlap_tokens` parameters
- Added default values for auto mode (1000 tokens chunk size, 200 tokens overlap)
- Enhanced logging to show chunking parameters used

#### Updated Embeddings Model (`backend/app/embeddings.py`)
- Changed default model from `jinaai/jina-embeddings-v3-small` to `jinaai/jina-embeddings-v3` (exact model as requested)

#### Enhanced Ingest Process (`backend/app/ingest.py`)
- Updated `ingest_document()` function to accept chunking parameters
- Added support for both auto and manual chunking modes
- Passes chunking parameters to the chunking function

#### New API Endpoints (`backend/app/main.py`)
- Updated `/ingest` endpoint to handle new chunking parameters
- Added `/index/{index_id}/documents` endpoint to get documents in an index
- Added `/check-document-name/{index_id}/{document_name}` endpoint to check for duplicate document names

### 3. Frontend UI Redesign (`frontend/src/App.tsx`)

#### Tab 1: Upload & Process
**Step 1: Index Creation (Optional)**
- Index creation section at the top
- Simple form to create new indices
- Real-time feedback and job status

**Step 2: File Upload**
- File upload area with progress tracking
- Automatic document name extraction from filename
- Upload status and job monitoring

**Step 3: Processing Configuration**
- Document name input with duplicate validation
- Index selection dropdown
- **Chunking Mode Selection:**
  - Auto mode: "Optimized hybrid chunking"
  - Manual mode: "Custom chunk size and overlap"
- **Manual Chunking Parameters:**
  - Chunk Size (tokens): 100-8000 range
  - Chunk Overlap (tokens): 0-2000 range
- Process Document button with validation
- Real-time processing status and progress

**Additional Features:**
- Indexed documents list showing existing documents in selected index
- Processing logs with timestamps
- Automatic tab switching to Query tab after successful processing

#### Tab 2: Query
**Query Interface:**
- Index selection dropdown
- Question input field
- **Configurable K Value:** Number input (1-20) for top-k results
- Ask button with validation

**Results Display:**
- Answer section with formatted text
- Retrieved contexts section showing top-k results
- Context cards with scores and metadata
- Integration code generation with API examples

### 4. Key Features Implemented

#### ✅ Chunk Mode Selection
- Auto mode: Uses optimized hybrid chunking with default parameters
- Manual mode: Allows custom chunk size and overlap configuration

#### ✅ Document Name Validation
- Real-time checking for duplicate document names in selected index
- Visual feedback with red border and error message
- Prevents processing if duplicate name exists

#### ✅ Processing Status
- Upload progress tracking
- Processing status with job monitoring
- Real-time logs with timestamps
- Automatic completion detection

#### ✅ Enhanced Query Interface
- Configurable top-k parameter (1-20)
- Separate index selection for queries
- Improved results display with context information

#### ✅ Index Management
- Create new indices
- View existing indices with document counts
- Browse documents within indices

#### ✅ Automatic Workflow
- Automatic tab switching after successful processing
- Pre-filled query index selection
- Seamless user experience

### 5. Technical Improvements

#### TypeScript Configuration
- Fixed Vite environment variable types
- Added proper type definitions for `import.meta.env`

#### Error Handling
- Comprehensive error handling for all API calls
- User-friendly error messages
- Graceful fallbacks for failed operations

#### State Management
- Proper state management for all UI components
- Real-time updates for job status
- Efficient re-rendering and updates

#### Responsive Design
- Mobile-friendly interface
- Proper spacing and layout
- Dark mode support maintained

## Usage Flow

1. **Create Index (Optional):** User can create a new index or use existing one
2. **Upload File:** Drag and drop or select file to upload
3. **Configure Processing:**
   - Set document name (validated for duplicates)
   - Select target index
   - Choose chunking mode (auto/manual)
   - Set manual parameters if needed
4. **Process Document:** Click "Process Document" to start parsing and indexing
5. **Monitor Progress:** Watch real-time logs and progress
6. **Query Results:** Automatically switch to Query tab to test the indexed document
7. **Configure Query:** Set index, question, and top-k value
8. **Get Results:** View answer and retrieved contexts

## Backward Compatibility
- All existing functionality preserved
- Default auto chunking mode maintains previous behavior
- Existing indices and documents remain accessible

## Testing
- Backend changes verified with syntax tests
- Frontend builds successfully with TypeScript
- All new features properly integrated

The new UI provides a much more intuitive and feature-rich experience while maintaining all existing functionality and adding the requested chunking controls and document management features.