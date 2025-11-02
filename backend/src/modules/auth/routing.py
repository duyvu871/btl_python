from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr

from src.core.database.models.user import User
from src.core.security.user import get_verified_user
from src.core.config.env import env as settings
from src.modules.auth.schema import UserCreate, UserRead
from src.modules.auth.use_cases import AuthUseCase, get_auth_usecase
from src.modules.verification.use_cases.helpers import VerificationUseCase, get_verification_usecase
from src.shared.uow import UnitOfWork, get_uow
from src.shared.schemas.response import SuccessResponse, ErrorResponse

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr



class AuthResponse(BaseModel):
    access_token: str | None = None
    refresh_token: str | None = None
    user: UserRead


# Error messages as simple strings
class ResponseMessage:
    EMAIL_ALREADY_REGISTERED = "Email already registered"
    INVALID_CREDENTIALS = "Invalid credentials"
    INVALID_TOKEN = "Invalid token"
    INVALID_PASSWORD_FORMAT = "Invalid password storage format"
    INCORRECT_EMAIL_OR_PASSWORD = "Incorrect email or password"
    VERIFICATION_EMAIL_SENT = "Verification email sent successfully"
    RATE_LIMIT_EXCEEDED = "Too many use_cases requests. Please try again later."


@router.post("/login", response_model=SuccessResponse[AuthResponse]) # type: ignore[valid-type]
async def login(
    login_in: LoginRequest,
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
):
    try:
        result = await auth_use_case.login(str(login_in.email), login_in.password)
        auth_response = AuthResponse(
            access_token=result.access_token,
            user=UserRead.model_validate(result.user),
        )
        return SuccessResponse(data=auth_response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=SuccessResponse[AuthResponse])
async def register_user(
    user_in: UserCreate,
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
):
    try:
        result = await auth_use_case.register(user_in)
        auth_response = AuthResponse(user=result.user)
        return SuccessResponse(data=auth_response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/token", response_model=None)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_use_case: AuthUseCase = Depends(get_auth_usecase),
) -> SuccessResponse[Token]:
    try:
        result = await auth_use_case.login(form_data.username, form_data.password)
        return SuccessResponse(data=result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=None)
async def read_users_me(current_user: User = Depends(get_verified_user)) -> SuccessResponse[UserRead]:
    return SuccessResponse(data=UserRead.model_validate(current_user))


@router.post("/verify-email", response_model=None)
async def verify_email(
    request: VerifyEmailRequest,
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
) -> SuccessResponse:
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


@router.post("/resend-verification", response_model=None)
async def resend_verification_email(
    request: ResendVerificationRequest,
    uow: UnitOfWork = Depends(get_uow),
    verification_use_case: VerificationUseCase = Depends(get_verification_usecase),
) -> SuccessResponse:
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
        print(f"Verification email queued with job ID: {job_id}")

        return SuccessResponse(message="Verification email sent successfully")
    except Exception as e:
        error_msg = str(e)
        if "Too many requests" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=ResponseMessage.RATE_LIMIT_EXCEEDED
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send use_cases email: {error_msg}"
        )
