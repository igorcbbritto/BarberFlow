"""
database/connection.py
Configuração da conexão com o banco de dados usando SQLAlchemy.
Suporta SQLite (desenvolvimento) e PostgreSQL (produção).
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Lê a URL do banco do arquivo .env
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./barberflow.db")

# Configuração especial para SQLite (não precisa de thread pool)
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Necessário para SQLite
    )
else:
    # PostgreSQL (Supabase, etc.)
    engine = create_engine(DATABASE_URL)

# Fábrica de sessões - cada requisição HTTP abre e fecha uma sessão
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para todos os models (tabelas) do sistema
Base = declarative_base()


def get_db():
    """
    Dependency do FastAPI: abre uma sessão de banco por requisição
    e garante que ela seja fechada ao final (mesmo com erros).
    
    Uso nas rotas:
        db: Session = Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
