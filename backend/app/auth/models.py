from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class UserPublic(BaseModel):
    id: int
    username: str
    full_name: str
    designation: Optional[str] = None
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    must_change_password: bool
    user: UserPublic


class UserCreate(BaseModel):
    username: str
    password: str
    full_name: str
    designation: Optional[str] = None
    role: str  # 'admin' or 'operator'


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class AuditLogEntry(BaseModel):
    id: int
    username: str
    action: str
    fiscal_code: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    details: Optional[dict] = None
