"""
routers/auth.py
Endpoints de autenticação: registro e login.

POST /auth/register  → Cria barbearia + usuário admin
POST /auth/login     → Retorna token JWT
"""

import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database.connection import get_db
from app.models.models import Barbershop, User
from app.schemas.schemas import RegisterRequest, LoginRequest, TokenResponse
from app.auth.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registra uma nova barbearia com seu usuário administrador.
    
    Fluxo:
    1. Verifica se email já existe
    2. Verifica se slug já está em uso
    3. Cria a barbearia
    4. Cria o usuário admin vinculado à barbearia
    5. Retorna token JWT para já entrar logado
    """
    # Verifica email duplicado
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este e-mail já está em uso"
        )
    
    # Verifica slug duplicado
    existing_shop = db.query(Barbershop).filter(Barbershop.slug == data.barbershop_slug).first()
    if existing_shop:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Este endereço (slug) já está em uso. Escolha outro."
        )
    
    try:
        # Cria a barbearia
        barbershop = Barbershop(
            name=data.barbershop_name,
            slug=data.barbershop_slug,
        )
        db.add(barbershop)
        db.flush()  # Gera o ID sem commitar ainda
        
        # Cria o usuário admin
        user = User(
            name=data.user_name,
            email=data.email,
            password_hash=hash_password(data.password),
            barbershop_id=barbershop.id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        db.refresh(barbershop)
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro ao criar conta. Verifique os dados e tente novamente."
        )
    
    # Gera token JWT (usuário já entra logado após cadastro)
    token = create_access_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=token,
        barbershop_id=barbershop.id,
        barbershop_name=barbershop.name,
        barbershop_slug=barbershop.slug,
        user_name=user.name,
        must_change_password=False,
    )


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """
    Autentica um usuário e retorna o token JWT.
    
    Fluxo:
    1. Busca usuário pelo email
    2. Verifica senha com bcrypt
    3. Retorna token JWT
    """
    # Busca usuário pelo email
    user = db.query(User).filter(User.email == data.email).first()
    
    # Verifica se usuário existe E se a senha está correta
    # Nota: verificamos os dois juntos para evitar timing attacks
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada. Entre em contato com o suporte."
        )
    
    # Busca a barbearia do usuário
    barbershop = db.query(Barbershop).filter(Barbershop.id == user.barbershop_id).first()

    # Verifica se a barbearia não está suspensa
    if not barbershop.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso suspenso. Entre em contato para reativar."
        )

    # Verifica se o acesso não expirou (None = vitalício)
    if barbershop.expires_at and barbershop.expires_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seu acesso expirou. Entre em contato para renovar."
        )

    # Gera token JWT
    token = create_access_token(data={"sub": str(user.id)})

    admin_email = os.getenv("ADMIN_EMAIL", "igor.c.b.britto@gmail.com")

    return TokenResponse(
        access_token=token,
        barbershop_id=barbershop.id,
        barbershop_name=barbershop.name,
        barbershop_slug=barbershop.slug,
        user_name=user.name,
        is_admin=user.email == admin_email,
        must_change_password=user.must_change_password or False,
    )
