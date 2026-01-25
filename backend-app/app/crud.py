from sqlalchemy.orm import Session
from sqlalchemy import desc
from passlib.context import CryptContext
from app import models, schemas

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    # ИЗМЕНЕНО: Добавлена поддержка поля is_staff при создании пользователя
    db_user = models.User(
        username=user.username, 
        password_hash=hashed_password, 
        is_admin=user.is_admin,
        is_staff=user.is_staff  # <-- Теперь сохраняем статус сотрудника
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_ticket(db: Session, ticket: schemas.TicketCreate):
    db_ticket = models.Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

# ИЗМЕНЕНО: Логика получения заявок теперь учитывает is_staff
def get_tickets(db: Session, user_id: int = None, is_admin: bool = False, is_staff: bool = False):
    query = db.query(models.Ticket)
    # Если не админ и не сотрудник — показываем только свои заявки
    if not (is_admin or is_staff):
        query = query.filter((models.Ticket.creator_id == user_id) | (models.Ticket.assignee_id == user_id))
    return query.order_by(desc(models.Ticket.created_at)).all()

# НОВАЯ ФУНКЦИЯ: Получить все заявки (для совместимости с роутером)
def get_all_tickets(db: Session):
    return db.query(models.Ticket).order_by(desc(models.Ticket.created_at)).all()

def get_ticket(db: Session, ticket_id: int):
    return db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()

# НОВАЯ ФУНКЦИЯ: Редактирование (заменяет логику удаления)
def update_ticket(db: Session, ticket_id: int, ticket_update: schemas.TicketUpdate, user_id: int, is_staff: bool, is_admin: bool):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if not db_ticket:
        return None

    # Фиксируем, кто последний редактировал заявку
    db_ticket.last_editor_id = user_id

    # Логика для сотрудников и админов
    if is_staff or is_admin:
        if ticket_update.status:
            db_ticket.status = ticket_update.status
            # Если сотрудник меняет статус на "in_progress", назначаем его исполнителем автоматически
            if ticket_update.status == "in_progress" and db_ticket.assignee_id is None:
                db_ticket.assignee_id = user_id
    
    # Логика для автора (может править текст, пока не закрыто)
    elif db_ticket.creator_id == user_id:
        if db_ticket.status != "closed":
            if ticket_update.title:
                db_ticket.title = ticket_update.title
            if ticket_update.description:
                db_ticket.description = ticket_update.description

    db.commit()
    db.refresh(db_ticket)
    return db_ticket

# ИЗМЕНЕНО: Простое удаление для админа (без проверки на "последнюю заявку")
def delete_ticket_force(db: Session, ticket_id: int):
    db_ticket = db.query(models.Ticket).filter(models.Ticket.id == ticket_id).first()
    if db_ticket:
        db.delete(db_ticket)
        db.commit()
        return True
    return False

def create_report(db: Session, ticket_id: int, comment: str, file_path: str = None):
    db_report = models.Report(ticket_id=ticket_id, comment=comment, file_path=file_path)
    db.add(db_report)
    db.commit()
    return db_report

def get_reports(db: Session, ticket_id: int):
    return db.query(models.Report).filter(models.Report.ticket_id == ticket_id).all()