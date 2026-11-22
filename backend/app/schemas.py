
import string

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ConfigDict,
    field_validator
)


class UserRegister(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=30
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=30
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, password: str):

        if any(char.isspace() for char in password):
            raise ValueError("Password must not contain spaces")

        if not any('a' <= char <= 'z' for char in password):
            raise ValueError("Password must contain a lowercase letter")

        if not any('A' <= char <= 'Z' for char in password):
            raise ValueError("Password must contain an uppercase letter")

        if not any(char.isdigit() for char in password):
            raise ValueError("Password must contain a number")

        if not any(char in string.punctuation for char in password):
            raise ValueError("Password must contain a special character")

        return password


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)



class EmailVerificationRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)



class UserLogin(BaseModel):
    identifier: str
    password: str



from pydantic import BaseModel, EmailStr, Field


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerify(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)


class PasswordResetConfirm(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=30)