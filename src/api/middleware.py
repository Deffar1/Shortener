import time

from fastapi import Request, Response

from src.core.logger import logger

async def log_middleware(request: Request, call_next):
    start_time = time.time()

    try:
        response: Response = await call_next(request)
        process_time = time.time() - start_time

        logger.info(
            f"{request.method} {request.url.path} | Status: {response.status_code} Time: {process_time:.4f}s"
        )
        return response
    except Exception as e:
        logger.exception(f"Unhandled Server Error in {request.url.path}")
        raise e
