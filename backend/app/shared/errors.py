import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    # Never carries secrets/PII; `details` is safe to serialize verbatim to the client.
    def __init__(self, status_code: int, code: str, message: str, details: object | None = None):
        self.status_code = status_code
        self.code = code
        self.details = details
        super().__init__(message)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_request: Request, exc: AppError) -> JSONResponse:
        logger.warning("app_error", extra={"code": exc.code, "status_code": exc.status_code})
        body = {"error": exc.code}
        if exc.details is not None:
            body["details"] = exc.details
        return JSONResponse(status_code=exc.status_code, content=body)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("unhandled_error", exc_info=exc)
        return JSONResponse(status_code=500, content={"error": "internal_error"})
