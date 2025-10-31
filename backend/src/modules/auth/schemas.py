from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """
    Schema for user registration request.
    """
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
