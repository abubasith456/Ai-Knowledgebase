import requests
from typing import List
from app.config import settings
from app.utils.logging import log_print


class NVIDIAService:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        log_print("✅ NVIDIA service initialized")

    def get_embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        """Get embeddings from NVIDIA API"""
        url = f"{self.base_url}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        data = {
            "input": texts,
            "model": model,
            "input_type": "query",
            "encoding_format": "float",
            "truncate": "NONE",
        }

        log_print(f"🤖 Making NVIDIA API request with {len(texts)} texts")

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)

            if response.status_code != 200:
                log_print(f"❌ NVIDIA API error: {response.status_code}")
                log_print(f"📋 Response: {response.text}")
                response.raise_for_status()

            result = response.json()

            if "data" not in result:
                raise Exception(f"Unexpected response format: {result}")

            embeddings = [item["embedding"] for item in result["data"]]
            log_print(
                f"✅ NVIDIA API success: {len(embeddings)} embeddings, dimension: {len(embeddings[0])}"
            )
            return embeddings

        except Exception as e:
            log_print(f"❌ NVIDIA API failed: {str(e)}")
            raise Exception(f"NVIDIA API failed: {str(e)}")


nvidia_service = NVIDIAService()
