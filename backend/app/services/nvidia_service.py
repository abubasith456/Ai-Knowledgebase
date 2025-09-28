import aiohttp
import asyncio
from typing import List
from app.config import settings
from app.utils.logging import log_print


class NVIDIAService:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.base_url = settings.NVIDIA_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        log_print("✅ Async NVIDIA service initialized")

    async def get_embeddings(self, texts: List[str], model: str) -> List[List[float]]:
        """Get embeddings from NVIDIA API - ASYNC VERSION"""
        url = f"{self.base_url}/embeddings"

        data = {
            "input": texts,
            "model": model,
            "input_type": "query",
            "encoding_format": "float",
            "truncate": "NONE",
        }

        log_print(f"🤖 Making ASYNC NVIDIA API request with {len(texts)} texts")

        timeout = aiohttp.ClientTimeout(total=60)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url, headers=self.headers, json=data
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        log_print(f"❌ NVIDIA API error: {response.status}")
                        log_print(f"📋 Response: {error_text}")
                        raise Exception(f"NVIDIA API error: {response.status}")

                    result = await response.json()

                    if "data" not in result:
                        raise Exception(f"Unexpected response format: {result}")

                    embeddings = [item["embedding"] for item in result["data"]]
                    log_print(
                        f"✅ ASYNC NVIDIA API success: {len(embeddings)} embeddings, dimension: {len(embeddings[0])}"
                    )
                    return embeddings

        except asyncio.TimeoutError:
            log_print(f"❌ NVIDIA API timeout after 60 seconds")
            raise Exception("NVIDIA API request timed out")
        except Exception as e:
            log_print(f"❌ ASYNC NVIDIA API failed: {str(e)}")
            raise Exception(f"NVIDIA API failed: {str(e)}")


nvidia_service = NVIDIAService()
