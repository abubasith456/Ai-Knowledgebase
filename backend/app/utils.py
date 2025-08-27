from fastapi.responses import JSONResponse
from app.models import CommonResponse


def success_response(message: str, data: dict | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content=CommonResponse(message=message, data=data or {}, error=None).dict(),
    )


def error_response(
    message: str, error: str, status_code: int = 400, data: dict | None = None
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=CommonResponse(message=message, data=data or {}, error=error).dict(),
    )
