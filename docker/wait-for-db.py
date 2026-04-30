#!/usr/bin/env python3
"""
Wait for database to be ready before starting the application.
This script ensures the backend doesn't start until PostgreSQL is accepting connections.
"""

import asyncio
import sys
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def wait_for_db(database_url: str, max_retries: int = 30, retry_interval: int = 2):
    """
    Wait for database to be ready.
    
    Args:
        database_url: Database connection URL
        max_retries: Maximum number of connection attempts
        retry_interval: Seconds to wait between retries
    
    Returns:
        True if database is ready, False otherwise
    """
    engine = create_async_engine(database_url, echo=False)
    
    for attempt in range(1, max_retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            print(f"✓ Database is ready after {attempt} attempt(s)")
            await engine.dispose()
            return True
        except Exception as e:
            if attempt < max_retries:
                print(f"⏳ Database not ready (attempt {attempt}/{max_retries}): {e}")
                await asyncio.sleep(retry_interval)
            else:
                print(f"✗ Database failed to become ready after {max_retries} attempts")
                await engine.dispose()
                return False
    
    return False

async def main():
    """Main entry point"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("✗ DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"⏳ Waiting for database at {database_url.split('@')[1] if '@' in database_url else 'unknown'}...")
    
    success = await wait_for_db(database_url)
    
    if success:
        print("✓ Database is ready - starting application")
        sys.exit(0)
    else:
        print("✗ Database connection failed - exiting")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
