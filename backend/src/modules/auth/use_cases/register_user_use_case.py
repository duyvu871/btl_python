import logging
from dataclasses import dataclass

from fastapi import Depends

from src.core.config.env import env, global_logger_name
from src.core.database.models.user import User
from src.core.security.password import hash_password
from src.modules.auth.schema import UserCreate
from src.modules.user.repository import UserRepository, get_user_repository
from src.modules.verification.use_cases import VerificationUseCase

logger = logging.getLogger(global_logger_name)

class RegisterUserUseCase:
    """
    Use case for registering a new user in the auth module.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        verification_use_case: VerificationUseCase,
    ):
        self.user_repo = user_repo
        self.verification_use_case = verification_use_case

    async def execute(self, user_data: UserCreate) -> User:
        """
        Execute the use case to register a user.
        :param user_data: UserCreate schema instance
        :return: Created User instance
        :raises ValueError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.user_repo.get_by_email(str(user_data.email))
        if existing:
            raise ValueError("User with this email already exists")

        # Hash the password
        hashed = hash_password(user_data.password)

        # Prepare data for creation
        data = user_data.model_dump()
        data['password'] = hashed

        try:
            # Create the user
            user = await self.user_repo.create(data)

            # Send verification email with user information
            try:
                job_id = await self.verification_use_case.send_email_verification(
                    email=user.email,
                    user_name=user.user_name,
                    user_email=user.email,
                    expiry_hours=24,
                    company_name=env.EMAILS_FROM_NAME or "BTL_PYTHON_PTIT",
                    custom_message="Welcome to our platform! Please verify your email to unlock all features.",
                )
                print(f"Verification email queued with job ID: {job_id}")
            except Exception as e:
                # Log error but don't fail registration
                print(f"Failed to send verification email: {e}")
                if "Too many requests" in str(e):
                    # Optionally inform user about rate limiting
                    pass

            return user
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            raise ValueError(f"Failed to register user") from e


def get_register_user_usecase(
    user_repo: UserRepository = Depends(get_user_repository),
    verification_use_case: VerificationUseCase = Depends(VerificationUseCase),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(user_repo, verification_use_case)