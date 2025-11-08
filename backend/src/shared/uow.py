from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.db import get_db


class UnitOfWork:
    """
    Unit of Work pattern implementation for managing repositories and transactions.

    this class inspired by https://docs.sqlalchemy.org/en/20/orm/session_basics.html
    """
    def __init__(self, session: AsyncSession):
        from src.modules.user.repository import UserRepository
        from src.modules.subscription.repository import PlanRepository, SubscriptionRepository
        from src.modules.record.repository import RecordingRepository, SegmentRepository

        self.session = session

        self.user_repo = UserRepository(session)
        self.plan_repo = PlanRepository(session)
        self.subscription_repo = SubscriptionRepository(session)
        self.recording_repo = RecordingRepository(session)
        self.segment_repo = SegmentRepository(session)

    async def commit(self):
        """Commit transaction."""
        await self.session.commit()

    async def rollback(self):
        """Rollback transaction."""
        await self.session.rollback()


async def get_uow(
    session: AsyncSession = Depends(get_db),
) -> AsyncGenerator[UnitOfWork, None]:
    """
    Dependency injector for UnitOfWork.
    """
    uow = UnitOfWork(session)
    try:
        yield uow

        await uow.commit()
    except Exception:
        await uow.rollback()
        raise
