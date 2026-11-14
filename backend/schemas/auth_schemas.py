from pydantic import BaseModel, Field, ConfigDict


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    phone: str = Field(min_length=5, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    phone: str = Field(min_length=5, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class UserProfile(BaseModel):
    id: int
    name: str
    phone: str | None
    role: str

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile
