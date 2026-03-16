"""
main.py
Ponto de entrada da aplicação FastAPI.

Para rodar em desenvolvimento:
    uvicorn app.main:app --reload

Para rodar em produção:
    uvicorn app.main:app --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.connection import engine, Base
from app.models import models  # Importa para criar as tabelas

# Importa todos os roteadores
from app.routers import auth, barbers, services, clients, appointments, dashboard

# ─────────────────────────────────────────────
# Cria as tabelas no banco (se não existirem)
# Em produção, use Alembic para migrations!
# ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

# ─────────────────────────────────────────────
# Cria a aplicação FastAPI
# ─────────────────────────────────────────────
app = FastAPI(
    title="BarberFlow API",
    description="SaaS para gerenciamento de barbearias e salões de beleza",
    version="1.0.0",
    docs_url="/docs",      # Swagger UI: http://localhost:8000/docs
    redoc_url="/redoc",    # ReDoc: http://localhost:8000/redoc
)

# ─────────────────────────────────────────────
# CORS - Permite que o frontend acesse a API
# Em produção, troque "*" pelo domínio do seu frontend
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Produção: ["https://seusite.vercel.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Registra as rotas
# ─────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(barbers.router)
app.include_router(services.router)
app.include_router(clients.router)
app.include_router(appointments.router)
app.include_router(dashboard.router)


@app.get("/", tags=["Health Check"])
def root():
    """Health check - verifica se a API está online"""
    return {
        "status": "online",
        "app": "BarberFlow API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health Check"])
def health():
    """Endpoint de saúde para monitoramento (Render, Railway, etc.)"""
    return {"status": "healthy"}
