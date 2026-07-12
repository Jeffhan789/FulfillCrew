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
