"""
main.py
Ponto de entrada da aplicação FastAPI.
"""

import os
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout
)
log = logging.getLogger(__name__)

log.info("=== Iniciando BarberFlow API ===")
log.info(f"Python: {sys.version}")
log.info(f"DATABASE_URL configurada: {'SIM' if os.getenv('DATABASE_URL') else 'NAO'}")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

log.info("Importando modulos internos...")

from app.database.connection import engine, Base
from app.models import models
from app.routers import auth, barbers, services, clients, appointments, dashboard, demo, schedules

log.info("Criando tabelas no banco de dados...")
try:
    Base.metadata.create_all(bind=engine)
    log.info("Tabelas criadas com sucesso!")
except Exception as e:
    log.error(f"ERRO ao criar tabelas: {e}")
    raise

app = FastAPI(
    title="BarberFlow API",
    description="SaaS para gerenciamento de barbearias e salões de beleza",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(barbers.router)
app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)
app.include_router(demo.router)
app.include_router(schedules.router)

log.info("=== BarberFlow API pronta! ===")


@app.get("/", tags=["Health Check"])
def root():
    return {"status": "online", "app": "BarberFlow API", "version": "1.0.0", "docs": "/docs"}


@app.get("/health", tags=["Health Check"])
def health():
    return {"status": "healthy"}
