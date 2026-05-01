#!/usr/bin/env python3
"""
Initialize database tables for EduRisk AI
This script creates all tables defined in the SQLAlchemy models
"""
import asyncio
import sys
import os

from sqlalchemy.ext.asyncio import create_async_engine
from backend.db.session import Base
from backend.models.student import Student
from backend.models.prediction import Prediction
from backend.models.audit_log import AuditLog

async def init_db():
    """Create all database tables"""
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://edurisk:edurisk_password@postgres:5432/edurisk_db")
    
    print("🔧 Connecting to database...")
    print(f"   URL: {database_url.replace(database_url.split('@')[0].split('//')[1], '***')}")
    
    engine = create_async_engine(database_url, echo=True)
    
    print("\n📦 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("\n✅ Database tables created successfully!")

if __name__ == "__main__":
    asyncio.run(init_db())
