from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/tickets", tags=["tickets"])
MEDIA_DIR = "/app/media"

@router.post("/", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    # Здесь желательно добавить передачу user_id из токена в crud.create_ticket
    return crud.create_ticket(db, ticket)

@router.get("/", response_model=List[schemas.TicketResponse])
def read_tickets(
    user_id: int, 
    is_admin: bool = False, 
    is_staff: bool = False,  # <-- ДОБАВЛЕНО: параметр для сотрудника
    db: Session = Depends(get_db)
):
    # ЛОГИКА: Если Админ или Сотрудник — возвращаем все заявки
    if is_admin or is_staff:
        return crud.get_all_tickets(db) # Эту функцию нужно будет добавить в crud.py
    # Если просто юзер — только его заявки
    return crud.get_tickets(db, user_id=user_id, is_admin=False)

@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return crud.get_ticket(db, ticket_id)

# ЗАМЕНА DELETE НА UPDATE (Edit)
@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int, 
    ticket_update: schemas.TicketUpdate, # <-- Нужно создать эту схему в schemas.py
    user_id: int,
    is_admin: bool = False,
    is_staff: bool = False,
    db: Session = Depends(get_db)
):
    # ЛОГИКА РЕДАКТИРОВАНИЯ:
    # 1. Ищем заявку в базе
    db_ticket = crud.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # 2. Проверяем права:
    # Сотрудник/Админ может менять статус.
    # Автор может менять описание, если статус еще "new".
    updated_ticket = crud.update_ticket(
        db, 
        ticket_id=ticket_id, 
        ticket_update=ticket_update,
        user_id=user_id,
        is_staff=is_staff,
        is_admin=is_admin
    )
    return updated_ticket

# УДАЛЕНИЕ: Теперь доступно только админу (is_admin=True)
@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, is_admin: bool = False, db: Session = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete tickets")
    
    success = crud.delete_ticket_force(db, ticket_id) # Обычное удаление без проверок на "последнюю"
    if not success:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"status": "deleted"}

@router.post("/{ticket_id}/reports")
def add_report(
    ticket_id: int,
    comment: str = Form(...),
    file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    file_path = None
    if file:
        file_path = f"{ticket_id}_{file.filename}"
        full_path = os.path.join(MEDIA_DIR, file_path)
        with open(full_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
    crud.create_report(db, ticket_id, comment, file_path)
    return {"status": "ok"}

@router.get("/{ticket_id}/reports", response_model=List[schemas.ReportResponse])
def get_reports(ticket_id: int, db: Session = Depends(get_db)):
    return crud.get_reports(db, ticket_id)