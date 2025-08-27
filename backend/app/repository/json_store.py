# app/storage/json_store.py
import json
import os
from pathlib import Path
import asyncio
from typing import Any, Dict
from fastapi.encoders import jsonable_encoder


class JsonKVStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = asyncio.Lock()
        if not self.path.exists():
            self._atomic_write({})

    # Internal sync read to avoid nested awaits with the same lock
    def _read_sync(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}

    async def load(self) -> Dict[str, Any]:
        # Optional: no lock, small chance of reading mid-write but atomic replace keeps file valid
        return self._read_sync()

    async def save(self, data: Dict[str, Any]) -> None:
        async with self._lock:
            self._atomic_write(data)

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    async def upsert(self, key: str, value: Any) -> None:
        async with self._lock:
            data = self._read_sync()  # read under the same lock, no awaits
            data[key] = jsonable_encoder(value)
            self._atomic_write(data)

    async def delete(self, key: str) -> None:
        async with self._lock:
            data = self._read_sync()  # read under the same lock, no awaits
            if key in data:
                del data[key]
                self._atomic_write(data)
