from sqlalchemy.ext.asyncio.engine import create_async_engine
from sqlalchemy.ext.asyncio.session import async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from src.core.config.env import env

# Create engine to connect to Postgres
engine = create_async_engine(
    env.DATABASE_URL,
    pool_pre_ping=True,  # Check connection before using
    echo=False,  # Display SQL commands in log (for debugging purposes)
)

# Create async session for each request
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)

# Base class for models
Base = declarative_base()

# Dependency to get DB session in FastAPI
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
