"""
Seed admin user from environment variables.
Reads FIRST_SUPERUSER, FIRST_SUPERUSER_PASSWORD, FIRST_SUPERUSER_USERNAME
Usage: python backend/scripts/seed_admin.py
"""

import asyncio
import os
import sys
from pathlib import Path

from src.core.database.db import get_db
from src.core.database.models import User
from src.core.database.models.user import Role
from src.core.security.password import hash_password

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select

async def seed_admin():
    """Create or update admin user from environment variables."""
    email = os.getenv("FIRST_SUPERUSER")
    password = os.getenv("FIRST_SUPERUSER_PASSWORD")
    username = os.getenv("FIRST_SUPERUSER_USERNAME")

    if not email or not password:
        print("⚠️  Skipping admin seed: FIRST_SUPERUSER and FIRST_SUPERUSER_PASSWORD must be set.")
        return None

    if not username:
        username = email.split("@")[0]

    async for db in get_db():
        # Check if user exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            updated = False
            if existing_user.role != Role.ADMIN:
                existing_user.role = Role.ADMIN
                updated = True
            if not existing_user.verified:
                existing_user.verified = True
                updated = True

            if updated:
                await db.commit()
                print(f"✅ Updated user {email} to admin role and verified.")
            else:
                print(f"ℹ️  User {email} already exists as admin.")
            return None

        # Create new admin user
        hashed_password = hash_password(password)
        admin_user = User(
            user_name=username, email=email, password=hashed_password, role=Role.ADMIN, verified=True, preferences=[]
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.user_name}")
        print(f"   Role: {admin_user.role.value}")

        return admin_user
    return None


if __name__ == "__main__":
    asyncio.run(seed_admin())
