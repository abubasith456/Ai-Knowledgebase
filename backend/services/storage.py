import json
import os
import threading
from typing import Any, Dict, List, Optional, TypeVar, Generic

T = TypeVar("T")


class JSONStore(Generic[T]):
    """
    Simple JSON-backed key-value store plus grouped lists.
    kv_path -> dict id -> object
    list_path -> dict group_key -> [ids]
    """

    def __init__(self, kv_path: str, list_path: Optional[str] = None):
        self.kv_path = kv_path
        self.list_path = list_path
        self._kv: Dict[str, Any] = {}
        self._lists: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        os.makedirs(os.path.dirname(kv_path), exist_ok=True)
        self._load()

    def _load(self):
        with self._lock:
            if os.path.exists(self.kv_path):
                try:
                    with open(self.kv_path, "r", encoding="utf-8") as f:
                        self._kv = json.load(f)
                except Exception:
                    self._kv = {}
            if self.list_path:
                if os.path.exists(self.list_path):
                    try:
                        with open(self.list_path, "r", encoding="utf-8") as f:
                            self._lists = json.load(f)
                    except Exception:
                        self._lists = {}

    def _flush(self):
        with self._lock:
            with open(self.kv_path, "w", encoding="utf-8") as f:
                json.dump(self._kv, f, ensure_ascii=False, indent=2)
            if self.list_path:
                with open(self.list_path, "w", encoding="utf-8") as f:
                    json.dump(self._lists, f, ensure_ascii=False, indent=2)

    def get(self, key: str) -> Optional[T]:
        with self._lock:
            return self._kv.get(key)

    def set(self, key: str, value: T) -> None:
        with self._lock:
            self._kv[key] = value
            self._flush()

    def delete(self, key: str) -> None:
        with self._lock:
            if key in self._kv:
                del self._kv[key]
                self._flush()

    def all_values(self) -> List[T]:
        with self._lock:
            return list(self._kv.values())

    def list_get(self, group_key: str) -> List[str]:
        with self._lock:
            return list(self._lists.get(group_key, []))

    def list_append_unique_front(self, group_key: str, item_id: str) -> None:
        with self._lock:
            arr = self._lists.setdefault(group_key, [])
            if item_id in arr:
                arr.remove(item_id)
            arr.insert(0, item_id)
            self._flush()

    def list_set(self, group_key: str, ids: List[str]) -> None:
        with self._lock:
            self._lists[group_key] = list(ids)
            self._flush()
