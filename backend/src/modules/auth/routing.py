import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.core.config.env import env as settings
from src.core.config.env import global_logger_name
from src.core.database.models.user import User
from src.core.security.user import get_verified_user
from src.modules.auth.schema import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    ResendVerificationRequest,
    ResponseMessage,
    Token,
    UserCreate,
    UserRead,
    VerifyEmailRequest,
)
from src.modules.auth.use_cases import AuthUseCase, get_auth_usecase
from src.modules.verification.use_cases.helpers import VerificationUseCase, get_verification_usecase
from src.shared.schemas.response import SuccessResponse
from src.shared.uow import UnitOfWork, get_uow

logger = logging.getLogger(global_logger_name)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/login", response_model=SuccessResponse[LoginResponse])
async def login(
    login_in: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
):
    try:
        result = await auth_use_case.login(str(login_in.email), login_in.password)
        auth_response = LoginResponse(
            access_token=result.access_token,
            user=UserRead.model_validate(result.user),
        )
        return SuccessResponse(data=auth_response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.debug(f"/login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.post("/register", response_model=SuccessResponse[UserRead])
async def register_user(
    user_in: RegisterRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
):
    try:
        result = await auth_use_case.register(UserCreate(**user_in.model_dump()))
        auth_response = UserRead.model_validate(result)
        return SuccessResponse(data=auth_response, message="User registered successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.debug(f"/register error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during registration"
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
):
    try:
        result = await auth_use_case.login(form_data.username, form_data.password)
        return Token(access_token=result.access_token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.debug(f"/token error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during login"
        )


@router.get("/me", response_model=SuccessResponse[UserRead])
async def read_users_me(current_user: User = Depends(get_verified_user)):
    try:
        return SuccessResponse(data=UserRead.model_validate(current_user))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/verify-email", response_model=SuccessResponse)
async def verify_email(
    request: VerifyEmailRequest,
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
):
    """
    Verify user's email with verification code.

    Args:
        request: Contains email and verification code
        uow: Unit of work
        verification_use_case: Verification use case for code validation

    Returns:
        SuccessResponse with success status and message

    Raises:
        HTTPException: If user not found or code is invalid
    """
    # Check if user exists
    user = await uow.user_repo.get_by_email(email=str(request.email))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already verified
    if user.verified:
        return SuccessResponse(message="Email is already verified")

    # Verify the code
    verification_result = await verification_use_case.verify_email(email=str(request.email), code=request.code)

    if not verification_result["valid"]:
        remaining = verification_result.get("remaining_attempts")

        if remaining is not None and remaining > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid verification code. {remaining} attempts remaining.",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification code. Please request a new one.",
            )

    # Update user's verified status
    await uow.user_repo.update(str(user.id), {"verified": True})
    user = await uow.user_repo.get(str(user.id))  # Refresh the user

    return SuccessResponse(message="Email verified successfully")


@router.post("/resend-verification", response_model=SuccessResponse)
async def resend_verification_email(
    request: ResendVerificationRequest,
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
):
    """
    Resend use_cases email to user.

    Args:
        request: Contains user email
        uow: Unit of work
        verification_use_case: Verification use case

    Returns:
        SuccessResponse with success status

    Raises:
        HTTPException: If user not found, already verified, or rate limited
    """
    # Check if user exists
    user = await uow.user_repo.get_by_email(email=str(request.email))

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Check if already verified
    if user.verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email is already verified")

    # Send use_cases email
    try:
        job_id = await verification_use_case.send_email_verification(
            email=user.email,
            user_name=user.user_name,
            user_email=user.email,
            expiry_hours=24,
            company_name=settings.EMAILS_FROM_NAME or "BTL_OOP_PTIT",
            custom_message="Please verify your email to unlock all features.",
        )
        logger.debug(f"Verification email queued with job ID: {job_id}")

        return SuccessResponse(message="Verification email sent successfully")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.debug(f"/resend-verification email error: {e}")
        error_msg = str(e)
        if "Too many requests" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=ResponseMessage.RATE_LIMIT_EXCEEDED
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send use_cases email: {error_msg}"
        )
