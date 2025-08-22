from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
try:
	from .v1_router import router as v1_router
except ImportError:
	from v1_router import router as v1_router

app = FastAPI(title="Doc KB", version="1.0.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

@app.get("/health")
def health():
	return {"status": "ok"}

# Mount versioned API only
app.include_router(v1_router)