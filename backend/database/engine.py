"""Database engine and session management for async PostgreSQL (SQLAlchemy 2.0).

Key Concepts (COMP315 Cloud Computing):
    1. Async Engine: create_async_engine with asyncpg driver
    2. AsyncSession: sessionmaker bound to async engine, expire_on_commit=False
    3. Dependency Injection: get_db() yields sessions for FastAPI Depends()
    4. Schema Migration: init_db() creates tables on startup (simplified for demo)

SQLAlchemy 2.0 vs 1.x Differences:
    - DeclarativeBase instead of declarative_base()
    - Mapped[] and mapped_column() for type-safe column definitions
    - select() instead of query()
    - AsyncSession with explicit await on all DB operations

Engineering Note:
    Q: Why asyncpg instead of psycopg2?
    A: asyncpg is a native async PostgreSQL driver that supports
       high-concurrency without blocking the event loop. psycopg2 is synchronous
       and would block all other requests while waiting for DB I/O.
       
    Q: What is expire_on_commit=False?
    A: By default, SQLAlchemy expires objects after commit, meaning the next
       attribute access triggers a lazy SELECT. In async code this is problematic
       because lazy loads occur outside the session context. Setting False
       keeps objects hydrated after commit, avoiding detached object errors.
       
    Q: How would you handle database migrations in production?
    A: Use Alembic (SQLAlchemy's migration tool) instead of create_all().
       init_db() is fine for development but dangerous in production because
       it doesn't handle schema evolution, rollbacks, or data migration.
"""

import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from backend.database.models import Base

# Connection string format: postgresql+asyncpg://user:pass@host:port/db
# The asyncpg driver is required for async SQLAlchemy 2.0
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/fulfillcrew"
)

engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    """FastAPI dependency that yields an async database session.
    
    Usage in routes:
        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables if they don't exist.
    
    WARNING: This is a simplified approach for development. In production,
    use Alembic migrations for schema evolution and version control.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db_connection() -> bool:
    """Health check: verify DB is reachable.
    
    Used by the /health endpoint to report database connectivity status.
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
