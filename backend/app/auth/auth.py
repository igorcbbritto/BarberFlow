"""
auth/auth.py
Funções de autenticação: hash de senha, criação e verificação de JWT.

bcrypt  = transforma senha em hash seguro (sem volta)
JWT     = token que prova que o usuário está logado
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import User

# Lê configurações do .env
SECRET_KEY  = os.getenv("SECRET_KEY", "chave-secreta-desenvolvimento-trocar-em-producao")
ALGORITHM   = os.getenv("ALGORITHM", "HS256")
EXPIRE_MINS = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))  # 7 dias

# Contexto para hash de senhas com bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Esquema de autenticação: lê o token do header "Authorization: Bearer <token>"
bearer_scheme = HTTPBearer()


# ─────────────────────────────────────────────
# FUNÇÕES DE SENHA
# ─────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Transforma a senha em hash bcrypt (não tem como reverter)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha digitada corresponde ao hash salvo"""
    return pwd_context.verify(plain_password, hashed_password)


# ─────────────────────────────────────────────
# FUNÇÕES DE TOKEN JWT
# ─────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token JWT com os dados do usuário.
    O token expira após EXPIRE_MINS minutos.
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINS)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decodifica e valida um token JWT.
    Lança HTTPException se o token for inválido ou expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado. Faça login novamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# ─────────────────────────────────────────────
# DEPENDENCY: Usuário atual autenticado
# ─────────────────────────────────────────────

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Dependency FastAPI: verifica o token JWT e retorna o usuário logado.
    
    Uso nas rotas protegidas:
        current_user: User = Depends(get_current_user)
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token sem identificação de usuário"
        )
    
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado ou inativo"
        )
    
    return user
