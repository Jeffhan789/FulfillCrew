"""Health check endpoint for Kubernetes/Docker orchestration.

This module implements the health check pattern required by cloud-native
deployment platforms (Docker Compose, Kubernetes, AWS ECS, etc.).

Health Check Levels:
    - Liveness: Is the process running? (FastAPI handles this implicitly)
    - Readiness: Is the app ready to accept traffic? (this endpoint)
    - Startup: Has the app finished initialisation? (init_db in lifespan)

Checks Performed:
    1. database: Can we connect to PostgreSQL?
    2. redis: Is the event bus backed by Redis?
    3. demand_model: Does the PyTorch MLP file exist?
    4. fraud_model: Does the XGBoost model file exist?

Status Logic:
    - "healthy": ALL checks pass → load balancer routes traffic here
    - "degraded": ONE or more checks fail → trigger alert, but keep serving
      (fallback to JSON products and heuristic models still works)

Interview Note:
    Q: What's the difference between /health and /ready in Kubernetes?
    A: /health (liveness) tells K8s whether to restart the container.
       /ready (readiness) tells K8s whether to route traffic to the pod.
       We combine both here for simplicity.
       
    Q: Why check for file existence instead of loading the model?
    A: Loading large models into memory on every health check would be
       expensive and slow. File existence is a cheap proxy. In production
       you'd also verify model checksums or version metadata.
"""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.engine import check_db_connection, get_db
from backend.infrastructure.config import settings
from backend.infrastructure.event_bus import get_event_bus
from backend.schemas import HealthCheck

router = APIRouter(tags=["health"])


async def check_redis_connection() -> bool:
    """Return ``True`` if the configured event bus is backed by Redis and reachable."""
    try:
        bus = await get_event_bus(settings.REDIS_URL)
        #  The event-bus factory returns InMemoryEventBus when Redis is unavailable,
        #  so we check the class name as a lightweight proxy.
        return bus.__class__.__name__ == "RedisEventBus"
    except Exception:
        return False


async def check_demand_model() -> bool:
    """Return ``True`` if the demand-prediction model file exists on disk."""
    model_path = (
        Path(__file__).parents[2] / "ml_models" / "demand_prediction" / "models" / "demand_mlp.pt"
    )
    return model_path.exists()


async def check_fraud_model() -> bool:
    """Return ``True`` if the fraud-detection model file exists on disk."""
    model_path = (
        Path(__file__).parents[2] / "ml_models" / "fraud_detection" / "models" / "fraud_xgb.json"
    )
    return model_path.exists()


@router.get("/health", response_model=HealthCheck)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthCheck:
    db_ok = await check_db_connection()
    redis_ok = await check_redis_connection()
    demand_model_ok = await check_demand_model()
    fraud_model_ok = await check_fraud_model()

    checks = {
        "database": db_ok,
        "redis": redis_ok,
        "demand_model": demand_model_ok,
        "fraud_model": fraud_model_ok,
    }
    status = "healthy" if all(checks.values()) else "degraded"
    return HealthCheck(status=status, checks=checks)
