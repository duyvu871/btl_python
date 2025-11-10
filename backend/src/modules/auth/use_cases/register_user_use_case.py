import logging

from fastapi import Depends

from src.core.config.env import env, global_logger_name
from src.core.database.models.user import User
from src.core.security.password import hash_password
from src.modules.auth.schema import UserCreate
from src.modules.subscription.use_cases import CreateSubscriptionUseCase
from src.modules.verification.use_cases import VerificationUseCase, get_verification_usecase
from src.shared.uow import UnitOfWork, get_uow

logger = logging.getLogger(global_logger_name)

class RegisterUserUseCase:
    """
    Use case for registering a new user in the auth module.
    """

    def __init__(
        self,
        uow: UnitOfWork,
        verification_use_case: VerificationUseCase,
    ):
        self.uow = uow
        self.verification_use_case = verification_use_case
        self.create_subscription_use_case = CreateSubscriptionUseCase(uow)

    async def execute(self, user_data: UserCreate) -> User:
        """
        Execute the use case to register a user.
        :param user_data: UserCreate schema instance
        :return: Created User instance
        :raises ValueError: If user with email already exists
        """
        # Check if user already exists
        existing = await self.uow.user_repo.get_by_email(str(user_data.email))
        if existing:
            raise ValueError("User with this email already exists")

        # Hash the password
        hashed = hash_password(user_data.password)
        # get username from email if not provided

        # Prepare data for creation
        data = user_data.model_dump()
        if not user_data.user_name:
            data["user_name"] = str(user_data.email).split("@")[0]
        data["password"] = hashed

        try:
            # Create the user
            user = await self.uow.user_repo.create(data)

            # Create subscription with FREE plan
            try:
                await self.create_subscription_use_case.execute(user.id)
            except Exception as e:
                # Log error but don't fail registration
                logger.warning(f"Failed to create subscription for user {user.id}: {e}")

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
            raise ValueError("Failed to register user") from e


def get_register_user_usecase(
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
) -> RegisterUserUseCase:
    return RegisterUserUseCase(uow, verification_use_case)
