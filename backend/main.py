import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import agents, orders, products

app = FastAPI(title="Cloud Multi-Agent E-Commerce Intelligence System")

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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
