"""
routers/admin.py
Painel administrativo do BarberFlow.
Acesso restrito ao superadmin (email configurado em variável de ambiente).
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.models import Barbershop, User, Appointment, Client, PlanType
from app.auth.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Email do superadmin — configure no Render como variável de ambiente ADMIN_EMAIL
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@barberflow.com")


def require_admin(current_user: User = Depends(get_current_user)):
    """Garante que só o superadmin acessa estas rotas"""
    if current_user.email != ADMIN_EMAIL:
        raise HTTPException(status_code=403, detail="Acesso restrito ao administrador")
    return current_user


# ── Schemas ──

class BarbershopCreateAdmin(BaseModel):
    name: str
    slug: str
    phone: Optional[str] = None
    address: Optional[str] = None
    owner_name: str
    owner_email: str
    owner_password: str
    access_days: int = 30   # dias de acesso a partir de hoje


class BarbershopUpdateAdmin(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    access_days: Optional[int] = None   # adiciona N dias a partir de hoje


# ── Helpers ──

def _format_shop(shop: Barbershop, db: Session) -> dict:
    owner = db.query(User).filter(User.barbershop_id == shop.id).first()
    appt_count = db.query(func.count(Appointment.id)).filter(
        Appointment.barbershop_id == shop.id
    ).scalar()
    client_count = db.query(func.count(Client.id)).filter(
        Client.barbershop_id == shop.id
    ).scalar()

    expires_at = shop.expires_at
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    days_left = None
    if expires_at:
        delta = expires_at - now
        days_left = max(0, delta.days)

    return {
        "id": shop.id,
        "name": shop.name,
        "slug": shop.slug,
        "phone": shop.phone,
        "is_active": shop.is_active,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "days_left": days_left,
        "owner_name": owner.name if owner else None,
        "owner_email": owner.email if owner else None,
        "appointments_count": appt_count,
        "clients_count": client_count,
        "created_at": shop.created_at.isoformat(),
    }


# ── Endpoints ──

@router.get("/barbershops", response_model=List[dict])
def list_barbershops(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Lista todas as barbearias cadastradas"""
    shops = db.query(Barbershop).order_by(Barbershop.created_at.desc()).all()
    return [_format_shop(s, db) for s in shops]


@router.post("/barbershops", response_model=dict, status_code=201)
def create_barbershop(
    data: BarbershopCreateAdmin,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Cria nova barbearia com usuário admin e prazo de acesso"""
    # Verifica slug único
    if db.query(Barbershop).filter(Barbershop.slug == data.slug).first():
        raise HTTPException(status_code=400, detail="Este slug já está em uso")

    # Verifica email único
    if db.query(User).filter(User.email == data.owner_email).first():
        raise HTTPException(status_code=400, detail="Este e-mail já está cadastrado")

    expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=data.access_days)

    shop = Barbershop(
        name=data.name,
        slug=data.slug,
        phone=data.phone,
        address=data.address,
        plan=PlanType.free,
        is_active=True,
        expires_at=expires_at,
    )
    db.add(shop)
    db.flush()

    user = User(
        name=data.owner_name,
        email=data.owner_email,
        password_hash=pwd_context.hash(data.owner_password),
        barbershop_id=shop.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(shop)

    return _format_shop(shop, db)


@router.patch("/barbershops/{shop_id}", response_model=dict)
def update_barbershop(
    shop_id: int,
    data: BarbershopUpdateAdmin,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Atualiza barbearia: suspender, reativar, adicionar dias"""
    shop = db.query(Barbershop).filter(Barbershop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

    if data.name is not None:
        shop.name = data.name
    if data.phone is not None:
        shop.phone = data.phone
    if data.is_active is not None:
        shop.is_active = data.is_active
    if data.access_days is not None:
        # Adiciona dias a partir de hoje (ou da expiração atual se ainda válida)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        base = max(shop.expires_at or now, now)
        shop.expires_at = base + timedelta(days=data.access_days)

    db.commit()
    return _format_shop(shop, db)


@router.delete("/barbershops/{shop_id}", status_code=204)
def delete_barbershop(
    shop_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    """Remove barbearia e todos os dados relacionados"""
    shop = db.query(Barbershop).filter(Barbershop.id == shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

    from app.models.models import BarberSchedule, Barber, Service, Client, Appointment
    db.query(Appointment).filter(Appointment.barbershop_id == shop_id).delete()
    db.query(BarberSchedule).filter(BarberSchedule.barbershop_id == shop_id).delete()
    db.query(Client).filter(Client.barbershop_id == shop_id).delete()
    db.query(Service).filter(Service.barbershop_id == shop_id).delete()
    db.query(Barber).filter(Barber.barbershop_id == shop_id).delete()
    db.query(User).filter(User.barbershop_id == shop_id).delete()
    db.delete(shop)
    db.commit()
