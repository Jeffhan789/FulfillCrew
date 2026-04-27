from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import agents, orders, products

app = FastAPI(title="Cloud Multi-Agent E-Commerce Intelligence System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
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

