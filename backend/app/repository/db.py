# app/storage/db.py
from app.repository.json_store import JsonKVStore

projects_store = JsonKVStore("app/storage/db/projects.json")
documents_store = JsonKVStore("app/storage/db/documents.json")
project_docs_store = JsonKVStore(
    "app/storage/db/project_docs.json"
)  # maps project_id -> [doc_ids]
indexes_store = JsonKVStore("app/storage/db/indexes.json")
