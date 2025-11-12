"""
Script to truncate all data from the database.
WARNING: This will delete ALL data from all tables!

Usage:
    python -m scripts.truncate_data
"""

import asyncio
import logging
import sys
from pathlib import Path

from sqlalchemy import text

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database.db import get_db

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def truncate_all_tables():
    """Truncate all tables in the database."""
    logger.warning("⚠️  WARNING: This will delete ALL data from the database!")
    
    # Confirm action
    confirm = input("Are you sure you want to continue? Type 'YES' to confirm: ")
    if confirm != "YES":
        logger.info("Truncate operation cancelled.")
        return

    async for db in get_db():
        try:
            logger.info("Starting truncate operation...")
            
            # Disable foreign key checks temporarily (PostgreSQL)
            await db.execute(text("SET session_replication_role = 'replica';"))
            
            # List of tables to truncate in order (respect foreign key dependencies)
            tables = [
                "segment_words",
                "segments",
                "transcript_chunks",
                "recordings",
                "user_subscriptions",
                "user_profiles",
                "users",
                "plans",
            ]
            
            for table in tables:
                logger.info(f"Truncating table: {table}")
                await db.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;"))
            
            # Re-enable foreign key checks
            await db.execute(text("SET session_replication_role = 'origin';"))
            
            await db.commit()
            logger.info("✓ Successfully truncated all tables!")
            
        except Exception as e:
            logger.error(f"✗ Error truncating tables: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(truncate_all_tables())

