from datetime import datetime
from fastapi import Form
from pydantic import BaseModel
from typing import Optional, Annotated
from sqlmodel import Field, SQLModel

# SQLModel Table for Users
class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    hashed_password: str

# Pydantic schema for registering a new user (request)
class RegisterUser(BaseModel):
    username: Annotated[str, Form()]
    email: Annotated[str, Form()]
    password: Annotated[str, Form()]

# Token models for JWT handling
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Schema for updating user details
class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None

# Model for Refresh Token
class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.user_id")
    token: str
    expires_at: datetime

# Model for Refresh Token Request
class RefreshTokenRequest(BaseModel):
    refresh_token: str

# Response after login (contains refresh token)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str

class RefreshTokenData(BaseModel):
    email: str

class UserAll(BaseModel):
    username: str
    email: str
    user_id: int
    
    class Config:
        orm_mode = True  # Allows Pydantic to work with SQLModel objects

class UserResponse(BaseModel):
    username: str
    email: str
    user_id: int
    # message:str

