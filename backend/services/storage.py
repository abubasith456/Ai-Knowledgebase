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

    def list_remove_all(self, list_key: str) -> None:
        """Remove all items from a list key"""
        if not self.list_path:
            return
        try:
            data = json.loads(self.list_path.read_text())
            if list_key in data:
                del data[list_key]
                self.list_path.write_text(json.dumps(data, indent=2))
        except (json.JSONDecodeError, FileNotFoundError):
            pass
