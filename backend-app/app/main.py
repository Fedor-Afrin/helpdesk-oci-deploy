from fastapi import FastAPI
from app.database import engine, Base, SessionLocal
from app.routers import auth, tickets
from app import crud, schemas, models  # <--- Добавь импорт models здесь!

# Теперь SQLAlchemy "увидит" классы Ticket и User внутри models
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Service Desk API")

app.include_router(auth.router)
app.include_router(tickets.router)

@app.on_event("startup")
def create_default_admin():
    db = SessionLocal()
    if not crud.get_user_by_username(db, "admin"):
        # Добавляем is_staff=True, чтобы админ тоже считался сотрудником
        admin_user = schemas.UserCreate(
            username="admin", 
            password="adminpassword", 
            is_admin=True,
            is_staff=True  
        )
        crud.create_user(db, admin_user)
        print("--- ADMIN / STAFF CREATED ---")
    db.close()

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Service Desk API is running"}
