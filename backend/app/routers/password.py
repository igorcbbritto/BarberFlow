"""
routers/password.py
Endpoints para reset e troca de senha.

Fluxo:
1. Admin acessa /password/reset-code/{user_email} → recebe código de 6 dígitos
2. Admin passa o código para o usuário (WhatsApp/telefone)
3. Usuário acessa /password/reset com email + código + nova senha
4. Usuário pode trocar a própria senha com /password/change (autenticado)
"""

import random
import string
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from app.database.connection import get_db
from app.models.models import User, PasswordResetCode, Barbershop, utcnow
from app.auth.auth import get_current_user, hash_password, verify_password

router = APIRouter(prefix="/password", tags=["Senha"])


# ── Schemas ──

class ResetWithCodeRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class UpdateProfileRequest(BaseModel):
    name: str | None = None
    logo_url: str | None = None
    phone: str | None = None
    address: str | None = None


# ── Gerar código de reset (admin ou sistema) ──

@router.post("/reset-code/{email}")
def generate_reset_code(
    email: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Gera um código de 6 dígitos para o usuário resetar a senha.
    Pode ser chamado pelo próprio usuário ou por um admin.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Só permite gerar código para usuários da mesma barbearia OU se for admin
    is_same_shop = user.barbershop_id == current_user.barbershop_id
    if not is_same_shop:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Invalida códigos anteriores
    db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.used == False
    ).delete()

    # Gera código de 6 dígitos
    code = ''.join(random.choices(string.digits, k=6))
    expires = utcnow() + timedelta(hours=1)

    reset = PasswordResetCode(
        user_id=user.id,
        code=code,
        expires_at=expires
    )
    db.add(reset)
    db.commit()

    return {
        "message": f"Código gerado para {user.name}",
        "code": code,
        "expires_in": "1 hora",
        "instruction": "Passe este código para o usuário pelo WhatsApp ou telefone"
    }


# ── Resetar senha com código (SEM autenticação) ──

@router.post("/reset")
def reset_password_with_code(
    data: ResetWithCodeRequest,
    db: Session = Depends(get_db)
):
    """
    Usuário reseta a senha informando o código recebido.
    Não precisa estar logado.
    """
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres")

    user = db.query(User).filter(User.email == data.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="E-mail não encontrado")

    # Busca código válido
    reset = db.query(PasswordResetCode).filter(
        PasswordResetCode.user_id == user.id,
        PasswordResetCode.code == data.code,
        PasswordResetCode.used == False,
        PasswordResetCode.expires_at > utcnow()
    ).first()

    if not reset:
        raise HTTPException(
            status_code=400,
            detail="Código inválido ou expirado. Solicite um novo código."
        )

    # Atualiza senha
    user.password_hash        = hash_password(data.new_password)
    user.must_change_password = False
    reset.used = True
    db.commit()

    return {"message": "Senha alterada com sucesso! Faça login com a nova senha."}


# ── Trocar própria senha (autenticado) ──

@router.post("/change")
def change_password(
    data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Usuário logado troca a própria senha."""
    if not verify_password(data.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Nova senha deve ter pelo menos 6 caracteres")

    current_user.password_hash        = hash_password(data.new_password)
    current_user.must_change_password = False
    db.commit()

    return {"message": "Senha alterada com sucesso!"}


# ── Atualizar perfil da barbearia (logo, telefone, endereço) ──

@router.put("/profile")
def update_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza dados da barbearia: nome, logo, telefone, endereço."""
    shop = db.query(Barbershop).filter(
        Barbershop.id == current_user.barbershop_id
    ).first()

    if data.logo_url   is not None: shop.logo_url = data.logo_url
    if data.phone      is not None: shop.phone    = data.phone
    if data.address    is not None: shop.address  = data.address
    if data.name       is not None: shop.name     = data.name

    db.commit()
    db.refresh(shop)

    return {
        "message": "Perfil atualizado!",
        "barbershop": {
            "name":     shop.name,
            "logo_url": shop.logo_url,
            "phone":    shop.phone,
            "address":  shop.address,
        }
    }


# ── Dados do perfil atual ──

@router.get("/profile")
def get_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna dados do perfil da barbearia e do usuário."""
    shop = db.query(Barbershop).filter(
        Barbershop.id == current_user.barbershop_id
    ).first()

    return {
        "user": {
            "name":                 current_user.name,
            "email":                current_user.email,
            "must_change_password": current_user.must_change_password,
        },
        "barbershop": {
            "name":     shop.name,
            "slug":     shop.slug,
            "logo_url": shop.logo_url,
            "phone":    shop.phone,
            "address":  shop.address,
        }
    }


# ── Admin define nova senha diretamente ──

class AdminResetRequest(BaseModel):
    email: EmailStr
    new_password: str

@router.post("/admin-reset")
def admin_reset_password(
    data: AdminResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Admin define uma nova senha para um usuário da barbearia.
    A senha deve ser enviada para o usuário por WhatsApp/telefone.
    No próximo login o usuário será obrigado a trocar a senha.
    """
    user = db.query(User).filter(
        User.email == data.email,
        User.barbershop_id == current_user.barbershop_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Senha deve ter pelo menos 6 caracteres")

    user.password_hash        = hash_password(data.new_password)
    user.must_change_password = True   # Força troca no próximo login
    db.commit()

    return {
        "message": f"Senha de {user.name} redefinida com sucesso!",
        "instruction": f"Envie a nova senha para {user.name} pelo WhatsApp. No próximo login será obrigado a criar uma nova senha.",
        "must_change": True
    }
