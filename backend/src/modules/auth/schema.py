from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class UserCreate(BaseModel):
    """
    Schema for user registration request.
    """
    user_name: str | None = None
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(v) > 128:
            raise ValueError("Password cannot be longer than 128 characters")
        return v


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_name: str
    email: str
    verified: bool
    role: str
    created_at: datetime


class RegisterResponse(BaseModel):
    """
    Schema for register response.
    """
    user: UserRead


class TokenResponse(BaseModel):
    """
    Schema for token response.
    """
    access_token: str
    token_type: str = "bearer"

class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    user_name: str | None = None

class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class LoginResponse(BaseModel):
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
