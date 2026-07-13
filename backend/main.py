"""FulfillCrew FastAPI Application Entry Point.

Architecture Overview (COMP315 Cloud Computing):
    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
    │   Nginx      │────▶│  FastAPI     │────▶│  PostgreSQL  │
    │  (reverse    │     │  (Python)    │     │  (asyncpg)   │
    │   proxy)     │     │              │     │              │
    └──────────────┘     └──────┬───────┘     └──────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
              ┌─────▼─────┐ ┌───▼────┐ ┌───▼────┐
              │  Redis    │ │ ML     │ │structlog│
              │  (pub/sub)│ │ Models │ │metrics │
              └───────────┘ └────────┘ └────────┘

FastAPI Lifecycle:
    1. lifespan(startup): Initialise DB tables (init_db)
    2. lifespan(shutdown): Clean up connections
    3. Request: Pydantic validation → Service → Repository → DB
    4. Response: Serialised via jsonable_encoder

Interview Note:
    Q: Why FastAPI instead of Flask or Django?
    A: FastAPI provides native async/await, automatic OpenAPI docs, and
       Pydantic validation out of the box. It's designed for high-performance
       APIs, which aligns with the real-time WebSocket requirements.
       
    Q: How does CORS work here?
    A: CORS_ORIGINS env var controls allowed origins. In development the
       frontend (Vite on :5173) and backend (:8000) run on different ports,
       so CORS is essential. In production, Nginx proxies both to the same
       domain, making CORS unnecessary.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import agents, health, metrics, orders, products
from backend.api import websocket as websocket_router
from backend.database.engine import init_db
from backend.infrastructure.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.
    
    Handles startup/shutdown events for the FastAPI app.
    This replaces the deprecated @app.on_event("startup") pattern.
    """
    logger.info("application_startup", event="startup")
    await init_db()
    yield
    logger.info("application_shutdown", event="shutdown")


app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,
)

# CORS origins from environment, falling back to sensible defaults for local dev
# In production behind Nginx, CORS is typically unnecessary since both
# frontend and backend are served from the same origin.
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080",
]

raw_cors = os.getenv("CORS_ORIGINS", "")
if raw_cors:
    allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router registration — each module owns a distinct API domain
app.include_router(products.router)    # /products
app.include_router(orders.router)      # /orders
app.include_router(agents.router)      # /agents
app.include_router(health.router)      # /health
app.include_router(metrics.router)     # /metrics
app.include_router(websocket_router.router)  # /ws/orders/{order_id}
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import agents, health, metrics, orders, products
from backend.api import websocket as websocket_router
from backend.database.engine import init_db
from backend.infrastructure.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", event="startup")
    await init_db()
    yield
    logger.info("application_shutdown", event="shutdown")


app = FastAPI(
    title="Cloud Multi-Agent E-Commerce Intelligence System",
    lifespan=lifespan,
)

# CORS origins from environment, falling back to sensible defaults for local dev
default_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:8080",
]

raw_cors = os.getenv("CORS_ORIGINS", "")
if raw_cors:
    allowed_origins = [o.strip() for o in raw_cors.split(",") if o.strip()]
else:
    allowed_origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products.router)
app.include_router(orders.router)
app.include_router(agents.router)
app.include_router(health.router)
app.include_router(metrics.router)
app.include_router(websocket_router.router)
