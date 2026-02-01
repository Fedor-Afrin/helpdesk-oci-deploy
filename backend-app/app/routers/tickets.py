from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import boto3
from app.database import get_db
from app import crud, schemas

router = APIRouter(prefix="/tickets", tags=["tickets"])

# Конфигурация OCI Object Storage (Берем из переменных окружения)
OCI_ACCESS_KEY = os.getenv('OCI_ACCESS_KEY')
OCI_SECRET_KEY = os.getenv('OCI_SECRET_KEY')
OCI_REGION = os.getenv('OCI_REGION', 'il-jerusalem-1')
OCI_NAMESPACE = os.getenv('OCI_NAMESPACE')
OCI_BUCKET_NAME = os.getenv('OCI_BUCKET_NAME')

# Инициализация клиента S3 для Oracle Cloud
s3_client = boto3.client(
    's3',
    aws_access_key_id=OCI_ACCESS_KEY,
    aws_secret_access_key=OCI_SECRET_KEY,
    region_name=OCI_REGION,
    endpoint_url=f"https://{OCI_NAMESPACE}.compat.objectstorage.{OCI_REGION}.oraclecloud.com"
)

@router.post("/", response_model=schemas.TicketResponse)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    return crud.create_ticket(db, ticket)

@router.get("/", response_model=List[schemas.TicketResponse])
def read_tickets(
    user_id: int, 
    is_admin: bool = False, 
    is_staff: bool = False,
    db: Session = Depends(get_db)
):
    if is_admin or is_staff:
        return crud.get_all_tickets(db)
    return crud.get_tickets(db, user_id=user_id, is_admin=False)

@router.get("/{ticket_id}", response_model=schemas.TicketResponse)
def read_ticket(ticket_id: int, db: Session = Depends(get_db)):
    return crud.get_ticket(db, ticket_id)

@router.put("/{ticket_id}", response_model=schemas.TicketResponse)
def update_ticket(
    ticket_id: int, 
    ticket_update: schemas.TicketUpdate,
    user_id: int,
    is_admin: bool = False,
    is_staff: bool = False,
    db: Session = Depends(get_db)
):
    db_ticket = crud.get_ticket(db, ticket_id)
    if not db_ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    updated_ticket = crud.update_ticket(
        db, 
        ticket_id=ticket_id, 
        ticket_update=ticket_update,
        user_id=user_id,
        is_staff=is_staff,
        is_admin=is_admin
    )
    return updated_ticket

@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, is_admin: bool = False, db: Session = Depends(get_db)):
    if not is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete tickets")
    
    success = crud.delete_ticket_force(db, ticket_id)
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
        file_path = f"tickets/{ticket_id}/{file.filename}"
        try:
            # Загружаем файл напрямую в бакет Oracle Object Storage
            s3_client.upload_fileobj(
                file.file,
                OCI_BUCKET_NAME,
                file_path
            )
        except Exception as e:
            print(f"Error uploading to OCI: {e}")
            raise HTTPException(status_code=500, detail="Could not upload file to cloud storage")
            
    crud.create_report(db, ticket_id, comment, file_path)
    return {"status": "ok"}

@router.get("/", response_model=List[schemas.TicketResponse])
def read_tickets(
    user_id: int, 
    is_admin: bool = False, 
    is_staff: bool = False,
    db: Session = Depends(get_db)
):
    # Просто передаем всё в crud.get_tickets. 
    # Твой crud.py сам решит: если admin/staff — даст всё, если нет — отфильтрует по user_id.
    return crud.get_tickets(
        db, 
        user_id=user_id, 
        is_admin=is_admin, 
        is_staff=is_staff
    )