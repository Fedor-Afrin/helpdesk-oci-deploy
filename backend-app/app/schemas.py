from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str
    is_admin: bool = False
    is_staff: bool = False

class UserResponse(UserBase):
    id: int
    is_admin: bool
    is_staff: bool
    class Config:
        from_attributes = True

class ReportResponse(BaseModel):
    id: int
    comment: Optional[str]
    file_path: Optional[str]
    created_at: datetime
    class Config:
        from_attributes = True

class TicketCreate(BaseModel):
    title: str
    description: str
    creator_id: int

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None

class TicketResponse(BaseModel):
    id: int
    title: str
    description: str
    status: str
    creator_id: int
    assignee_id: Optional[int] = None
    last_editor_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # --- МАГИЯ ЗДЕСЬ ---
    # Эти поля позволят фронтенду обращаться к именам: ticket.creator.username
    creator: Optional[UserResponse] = None
    assignee: Optional[UserResponse] = None
    last_editor: Optional[UserResponse] = None

    class Config:
        from_attributes = True