"""
Use case: List users with pagination and filters.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database.models.user import Role, User


class ListUsersUseCase:
    """
    Use case for listing users with pagination and filters.

    Responsibilities:
    - Build query with filters
    - Apply pagination
    - Return paginated results
    """

    async def execute(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = 10,
        search: str | None = None,
        role: str | None = None,
        verified: bool | None = None,
    ) -> dict:
        """
        Execute the use case.

        Args:
            db: Database session
            page: Page number
            page_size: Items per page
            search: Search term for email or username
            role: Filter by role
            verified: Filter by verification status

        Returns:
            Dict with total, page, page_size, users list

        Raises:
            ValueError: If invalid role
        """
        # Build query
        query = select(User)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.where((User.email.ilike(search_term)) | (User.user_name.ilike(search_term)))

        if role:
            try:
                role_enum = Role[role.upper()]
                query = query.where(User.role == role_enum)
            except KeyError:
                raise ValueError(f"Invalid role: {role}. Must be 'user' or 'admin'")

        if verified is not None:
            query = query.where(User.verified == verified)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(User.created_at.desc())

        # Execute query
        result = await db.execute(query)
        users = result.scalars().all()

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "users": users,
        }
