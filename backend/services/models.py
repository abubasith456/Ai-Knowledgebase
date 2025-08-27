from enum import Enum
from dataclasses import dataclass
from typing import List


class DocStatus(str, Enum):
    pending = "pending"
    parsing = "parsing"
    completed = "completed"


class IndexStatus(str, Enum):
    idle = "idle"
    indexing = "indexing"
    completed = "completed"


@dataclass
class Project:
    id: str
    name: str
    secret: str


@dataclass
class Document:
    id: str
    project_id: str
    filename: str
    status: DocStatus


@dataclass
class IndexDef:
    id: str
    project_id: str
    name: str
    status: IndexStatus
    document_ids: List[str]
