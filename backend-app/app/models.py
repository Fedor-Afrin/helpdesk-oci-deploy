from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password_hash = Column(String)
    is_admin = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)

    # Связи: чтобы знать, какие тикеты связаны с этим пользователем
    created_tickets = relationship("Ticket", back_populates="creator", foreign_keys="[Ticket.creator_id]")
    assigned_tickets = relationship("Ticket", back_populates="assignee", foreign_keys="[Ticket.assignee_id]")

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="new") # Доступные статусы: new, in_progress, resolved, closed
    
    # Внешние ключи (ID пользователей)
    creator_id = Column(Integer, ForeignKey("users.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    last_editor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Даты (создание и автоматическое обновление при правке)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 

    # Объекты связей (для обращения через .creator, .assignee и т.д.)
    creator = relationship("User", foreign_keys=[creator_id], back_populates="created_tickets")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tickets")
    last_editor = relationship("User", foreign_keys=[last_editor_id])

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"))
    comment = Column(Text)
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())