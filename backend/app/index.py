import os
import uuid
import json
from datetime import datetime
from typing import List, Optional
from pathlib import Path

try:
    from .schemas import Index, Parser
except ImportError:
    from schemas import Index, Parser

# Simple file-based storage for index (in production, use a proper database)
# Use local directory in development, /data/index in production
try:
    index_path = os.environ.get("INDEX_DIR", "./data/index")
    INDEX_DIR = Path(index_path)
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
except (OSError, PermissionError) as e:
    # Fallback to a local directory if we can't create the default path
    import tempfile
    INDEX_DIR = Path(tempfile.gettempdir()) / "doc_kb_index"
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Warning: Using fallback directory for index: {INDEX_DIR}")

# Available parsers
AVAILABLE_PARSERS = [
    Parser(
        id="default",
        name="Default Parser",
        description="Basic text extraction",
        supported_formats=["pdf", "txt", "docx"]
    ),
    Parser(
        id="advanced",
        name="Advanced Parser", 
        description="OCR and advanced formatting",
        supported_formats=["pdf", "png", "jpg", "docx"]
    ),
    Parser(
        id="structured",
        name="Structured Parser",
        description="For tables and structured data",
        supported_formats=["csv", "xlsx", "json"]
    )
]


def get_parsers() -> List[Parser]:
    """Get all available parsers."""
    return AVAILABLE_PARSERS


def get_parser(parser_id: str) -> Optional[Parser]:
    """Get a specific parser by ID."""
    for parser in AVAILABLE_PARSERS:
        if parser.id == parser_id:
            return parser
    return None


def create_index(name: str, parser_id: str) -> str:
    """Create a new index and return its ID."""
    index_id = str(uuid.uuid4())
    
    index_data = {
        "id": index_id,
        "name": name,
        "created_at": datetime.now().isoformat(),
        "document_count": 0,
        "parser_id": parser_id
    }
    
    index_file = INDEX_DIR / f"{index_id}.json"
    with open(index_file, 'w') as f:
        json.dump(index_data, f, indent=2)
    
    return index_id


def get_index(index_id: str) -> Optional[Index]:
    """Get an index by ID."""
    index_file = INDEX_DIR / f"{index_id}.json"
    if not index_file.exists():
        return None
    
    try:
        with open(index_file, 'r') as f:
            data = json.load(f)
        return Index(**data)
    except (json.JSONDecodeError, ValueError):
        return None


def get_all_indices() -> List[Index]:
    """Get all index."""
    index_list = []
    for index_file in INDEX_DIR.glob("*.json"):
        try:
            with open(index_file, 'r') as f:
                data = json.load(f)
            index_list.append(Index(**data))
        except (json.JSONDecodeError, ValueError):
            continue
    
    # Sort by creation date (newest first)
    index_list.sort(key=lambda x: x.created_at, reverse=True)
    return index_list


def update_index_document_count(index_id: str, count: int):
    """Update the document count for an index."""
    index_file = INDEX_DIR / f"{index_id}.json"
    if not index_file.exists():
        return
    
    try:
        with open(index_file, 'r') as f:
            data = json.load(f)
        
        data["document_count"] = count
        
        with open(index_file, 'w') as f:
            json.dump(data, f, indent=2)
    except (json.JSONDecodeError, ValueError):
        pass


def delete_index(index_id: str) -> bool:
    """Delete an index."""
    index_file = INDEX_DIR / f"{index_id}.json"
    if index_file.exists():
        index_file.unlink()
        return True
    return False