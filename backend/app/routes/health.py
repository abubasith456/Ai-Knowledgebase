from fastapi import APIRouter
from app.models.response import StandardResponse
from app.services.nvidia_service import nvidia_service
from app.utils.logging import log_print

router = APIRouter()


@router.get("/", response_model=StandardResponse)
async def health_check():
    return StandardResponse.success(
        data={"service": "knowledge-base-api", "version": "2.0.0", "status": "healthy"}
    )


@router.post("/test/nvidia", response_model=StandardResponse)
async def test_nvidia_api(text: str = "Hello world"):
    """Test NVIDIA API directly"""
    try:
        log_print(f"🧪 Testing NVIDIA API with text: '{text}'")
        embeddings = await nvidia_service.get_embeddings(
            [text], "nvidia/llama-3.2-nv-embedqa-1b-v2"
        )

        return StandardResponse.success(
            data={
                "text": text,
                "embedding_dimension": len(embeddings[0]),
                "embedding_sample": embeddings[0][:5],
            }
        )

    except Exception as e:
        log_print(f"❌ NVIDIA API test failed: {str(e)}")
        return StandardResponse.failed(error=str(e))
