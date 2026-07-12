from fastapi import APIRouter, Response

router = APIRouter(tags=["metrics"])

try:
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
except ImportError:
    @router.get("/metrics")
    async def metrics() -> Response:
        return Response(
            content="# prometheus_client not installed\n",
            media_type="text/plain",
        )
