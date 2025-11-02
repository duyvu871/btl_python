from typing import Generic, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.db import Base

# Define a generic type variable for models
ModelType = TypeVar("ModelType", bound=Base)

# Base repository class
class BaseRepository(Generic[ModelType]):
    """
    Generic repository for CRUD operations.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    # Retrieve a single record by ID
    async def get(self, model_id: str) -> ModelType | None:
        result = await self.session.get(self.model, model_id)
        return result

    # Create a new record
    async def create(self, data: dict) -> ModelType:
        db_obj = self.model(**data)
        self.session.add(db_obj)
        await self.session.flush()  # Flush to get the ID without committing
        return db_obj

    # Update an existing record
    async def update(self, model_id: str, data: dict) -> ModelType | None:
        db_obj = await self.get(model_id)
        if db_obj:
            for key, value in data.items():
                setattr(db_obj, key, value)
        return db_obj

    # Delete a record by ID
    async def delete(self, model_id: str) -> bool:
        db_obj = await self.get(model_id)
        if db_obj:
            await self.session.delete(db_obj)
            return True
        return False