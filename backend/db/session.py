"""
Database session management with async SQLAlchemy.

This module provides async database engine configuration, connection pooling,
and session management for FastAPI dependency injection.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/edurisk_ai"
)

# Create async engine with connection pooling
# pool_size=20: Maximum number of connections to keep in the pool
# max_overflow=10: Additional connections beyond pool_size when needed
# pool_pre_ping=True: Verify connections before use to handle stale connections
# pool_recycle=3600: Recycle connections after 1 hour to prevent stale connections
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging during development
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

# Create async session factory
# expire_on_commit=False: Prevent lazy-loading issues after commit
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base for ORM models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Provides an async database session with automatic transaction management:
    - Commits on successful completion
    - Rolls back on exceptions
    - Always closes the session
    
    Yields:
        AsyncSession: Database session for use in route handlers
        
    Example:
        @app.get("/students")
        async def get_students(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Student))
            return result.scalars().all()
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize database by creating all tables.
    
    This should only be used for development/testing.
    In production, use Alembic migrations instead.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """
    Close database engine and dispose of connection pool.
    
    Should be called on application shutdown.
    """
    await engine.dispose()
