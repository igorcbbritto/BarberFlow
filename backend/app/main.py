"""main.py — BarberFlow API"""

import os, sys, logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", stream=sys.stdout)
log = logging.getLogger(__name__)

log.info("=== Iniciando BarberFlow API ===")
log.info(f"Python: {sys.version}")
log.info(f"DATABASE_URL: {'SIM' if os.getenv('DATABASE_URL') else 'NAO'}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.connection import engine, Base
from app.models import models
from app.routers import auth, barbers, services, clients, appointments, dashboard, demo, schedules, password, admin

log.info("Criando tabelas...")
try:
    Base.metadata.create_all(bind=engine)
    log.info("Tabelas OK!")
except Exception as e:
    log.error(f"ERRO: {e}"); raise

app = FastAPI(
    title="BarberFlow API",
    description="SaaS para barbearias",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(auth.router)
app.include_router(barbers.router)
app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)
app.include_router(demo.router)
app.include_router(schedules.router)
app.include_router(password.router)
app.include_router(admin.router)

log.info("=== API pronta! ===")

@app.get("/", tags=["Health Check"])
def root(): return {"status": "online", "app": "BarberFlow API", "version": "1.0.0"}

@app.get("/health", tags=["Health Check"])
def health(): return {"status": "healthy"}

@app.post("/setup-admin", tags=["Setup"], include_in_schema=False)
def setup_admin():
    """Cria o usuário superadmin uma única vez. Idempotente e seguro."""
    import os
    from passlib.context import CryptContext
    from app.database.connection import SessionLocal
    from app.models.models import Barbershop, User, PlanType

    db = SessionLocal()
    pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "igor.c.b.britto@gmail.com")
    ADMIN_PASS  = os.getenv("ADMIN_PASSWORD", "")

    try:
        if db.query(User).filter(User.email == ADMIN_EMAIL).first():
            return {"status": "already_exists", "message": "Admin já cadastrado."}

        shop = Barbershop(
            name="BarberFlow Admin",
            slug="barberflow-admin",
            plan=PlanType.free,
            is_active=True,
        )
        db.add(shop)
        db.flush()

        user = User(
            name="Igor Admin",
            email=ADMIN_EMAIL,
            password_hash=pwd.hash(ADMIN_PASS),
            barbershop_id=shop.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        return {"status": "created", "message": f"Admin criado: {ADMIN_EMAIL}"}
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
