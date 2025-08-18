import os
import secrets
from typing import Optional
from fastapi import Header, HTTPException
from itsdangerous import URLSafeSerializer


_SERIALIZER_SECRET = os.environ.get("API_KEY_SECRET", secrets.token_urlsafe(32))
_serializer = URLSafeSerializer(_SERIALIZER_SECRET, salt="kb-api-key")


def generate_api_key_server() -> str:
	"""Generate a signed API key string the frontend can store locally."""
	raw = secrets.token_urlsafe(24)
	return _serializer.dumps({"k": raw})


_valid_keys_memory: set[str] = set()


def register_api_key(api_key: str) -> bool:
	try:
		data = _serializer.loads(api_key)
		_raw = data.get("k")
		if not _raw:
			return False
		_valid_keys_memory.add(api_key)
		return True
	except Exception:
		return False


def validate_api_key(api_key: str) -> bool:
	return api_key in _valid_keys_memory


def require_api_key(x_api_key: Optional[str] = Header(default=None, alias="x-api-key")) -> str:
	# Allow bypass in non-prod or local testing
	if os.environ.get("DISABLE_AUTH", "false").lower() in ("1", "true", "yes"):
		return x_api_key or "__disabled__"
	if not x_api_key or not validate_api_key(x_api_key):
		raise HTTPException(status_code=401, detail="Invalid or missing API key")
	return x_api_key