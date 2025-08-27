import json
import os
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pathlib import Path

T = TypeVar("T")

class JSONStore(Generic[T]):
    def __init__(self, kv_path: str, list_path: Optional[str] = None):
        self.kv_path = Path(kv_path)
        self.list_path = Path(list_path) if list_path else None
        
        # Ensure directories exist
        self.kv_path.parent.mkdir(parents=True, exist_ok=True)
        if self.list_path:
            self.list_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize files if they don't exist
        if not self.kv_path.exists():
            self.kv_path.write_text("{}")
        if self.list_path and not self.list_path.exists():
            self.list_path.write_text("{}")

    def get(self, key: str) -> Optional[T]:
        try:
            data = json.loads(self.kv_path.read_text())
            return data.get(key)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def set(self, key: str, value: T) -> None:
        try:
            data = json.loads(self.kv_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
        data[key] = value
        self.kv_path.write_text(json.dumps(data, indent=2))

    def delete(self, key: str) -> None:
        try:
            data = json.loads(self.kv_path.read_text())
            if key in data:
                del data[key]
                self.kv_path.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, FileNotFoundError):
            pass

    def all_values(self) -> List[T]:
        try:
            data = json.loads(self.kv_path.read_text())
            return list(data.values())
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def list_get(self, list_key: str) -> List[str]:
        if not self.list_path:
            return []
        try:
            data = json.loads(self.list_path.read_text())
            return data.get(list_key, [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def list_set(self, list_key: str, items: List[str]) -> None:
        if not self.list_path:
            return
        try:
            data = json.loads(self.list_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
        data[list_key] = items
        self.list_path.write_text(json.dumps(data, indent=2))

    def list_append_unique_front(self, list_key: str, item: str) -> None:
        if not self.list_path:
            return
        try:
            data = json.loads(self.list_path.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            data = {}
        
        if list_key not in data:
            data[list_key] = []
        
        # Remove if exists, then add to front
        if item in data[list_key]:
            data[list_key].remove(item)
        data[list_key].insert(0, item)
        
        self.list_path.write_text(json.dumps(data, indent=2))

    def list_remove(self, list_key: str, item: str) -> None:
        if not self.list_path:
            return
        try:
            data = json.loads(self.list_path.read_text())
            if list_key in data and item in data[list_key]:
                data[list_key].remove(item)
                self.list_path.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, FileNotFoundError):
            pass

class MarkdownStorage:
    def __init__(self, base_path: str = "backend/markdown"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_markdown(self, project_id: str, doc_id: str, content: str) -> str:
        """Save markdown content and return file path"""
        project_dir = self.base_path / project_id
        project_dir.mkdir(exist_ok=True)
        
        file_path = project_dir / f"{doc_id}.md"
        file_path.write_text(content, encoding='utf-8')
        return str(file_path)

    def get_markdown(self, project_id: str, doc_id: str) -> Optional[str]:
        """Retrieve markdown content"""
        file_path = self.base_path / project_id / f"{doc_id}.md"
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return None

    def delete_markdown(self, project_id: str, doc_id: str) -> bool:
        """Delete markdown file"""
        file_path = self.base_path / project_id / f"{doc_id}.md"
        if file_path.exists():
            file_path.unlink()
            return True
        return False
