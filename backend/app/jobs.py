import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from threading import Lock


@dataclass
class Job:
	id: str
	type: str
	status: str
	message: Optional[str]
	file_id: Optional[str]
	document_name: Optional[str]
	num_chunks: Optional[int]
	started_at: str
	finished_at: Optional[str]


_jobs: Dict[str, Job] = {}
_lock = Lock()


def _now() -> str:
	return datetime.now(timezone.utc).isoformat()


def create_job(job_type: str, file_id: Optional[str] = None, document_name: Optional[str] = None) -> str:
	job_id = str(uuid.uuid4())
	job = Job(
		id=job_id,
		type=job_type,
		status="processing",
		message=None,
		file_id=file_id,
		document_name=document_name,
		num_chunks=None,
		started_at=_now(),
		finished_at=None,
	)
	with _lock:
		_jobs[job_id] = job
	return job_id


def complete_job(job_id: str, message: Optional[str] = None, num_chunks: Optional[int] = None):
	with _lock:
		job = _jobs.get(job_id)
		if not job:
			return
		job.status = "completed"
		job.message = message
		job.num_chunks = num_chunks
		job.finished_at = _now()


def fail_job(job_id: str, message: str):
	with _lock:
		job = _jobs.get(job_id)
		if not job:
			return
		job.status = "failed"
		job.message = message
		job.finished_at = _now()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
	with _lock:
		job = _jobs.get(job_id)
		return asdict(job) if job else None

