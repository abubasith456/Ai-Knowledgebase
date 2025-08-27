import os
from typing import Optional

class EnvironmentConfig:
    """Simple environment configuration for the hybrid service"""
    
    @property
    def HYBRID_EMBEDDING_MODEL(self) -> str:
        return os.getenv("HYBRID_EMBEDDING_MODEL", "jinaai/jina-embeddings-v3")
    
    @property
    def HYBRID_MODEL_MAX_TOKENS(self) -> int:
        return int(os.getenv("HYBRID_MODEL_MAX_TOKENS", "2000"))
    
    @property
    def HYBRID_CHUNK_RATIO(self) -> float:
        return float(os.getenv("HYBRID_CHUNK_RATIO", "0.9"))
    
    @property
    def HYBRID_CHUNK_OVERLAP_RATIO(self) -> float:
        return float(os.getenv("HYBRID_CHUNK_OVERLAP_RATIO", "0.05"))

# Global instance
env = EnvironmentConfig()