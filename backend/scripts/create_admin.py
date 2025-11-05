"""
Script to create an admin user for testing.
Run this script to create an admin user in the database.
"""

import asyncio
import sys
from pathlib import Path

from src.core.database.db import get_db
from src.core.database.models import User
from src.core.database.models.user import Role
from src.core.security.password import hash_password

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import select


async def create_admin_user(email: str, password: str, user_name: str = None):
    """Create an admin user."""
    async for db in get_db():
        # Check if user already exists
        result = await db.execute(select(User).where(User.email == email))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User with email {email} already exists.")

            # Update to admin if not already
            if existing_user.role != Role.ADMIN:
                existing_user.role = Role.ADMIN
                existing_user.verified = True
                await db.commit()
                print(f"Updated {email} to admin role and verified.")
            else:
                print(f"{email} is already an admin.")
            return existing_user

        # Create new admin user
        if not user_name:
            user_name = email.split("@")[0]

        hashed_password = hash_password(password)

        admin_user = User(
            user_name=user_name,
            email=email,
            password=hashed_password,
            role=Role.ADMIN,
            verified=True,  # Auto-verify admin user
        )

        db.add(admin_user)
        await db.commit()
        await db.refresh(admin_user)

        print("✅ Admin user created successfully!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.user_name}")
        print(f"   Role: {admin_user.role.value}")
        print(f"   Verified: {admin_user.verified}")

        return admin_user
    return None


async def main():
    """Main function to create admin user."""
    print("=" * 50)
    print("Create Admin User")
    print("=" * 50)

    # You can modify these values or pass them as arguments
    admin_email = input("Enter admin email (default: admin@example.com): ").strip()
    if not admin_email:
        admin_email = "admin@example.com"

    admin_password = input("Enter admin password (default: admin123): ").strip()
    if not admin_password:
        admin_password = "admin123"

    admin_username = input(f"Enter username (default: {admin_email.split('@')[0]}): ").strip()
    if not admin_username:
        admin_username = admin_email.split("@")[0]

    await create_admin_user(admin_email, admin_password, admin_username)

    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
