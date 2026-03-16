"""
routers/barbers.py
CRUD de profissionais/barbeiros.

Todas as rotas são protegidas por JWT.
Multi-tenant: usuário só vê os barbeiros da sua barbearia.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Barber, User
from app.schemas.schemas import BarberCreate, BarberUpdate, BarberResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/barbers", tags=["Profissionais"])


@router.get("/", response_model=List[BarberResponse])
def list_barbers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os profissionais da barbearia do usuário logado"""
    barbers = db.query(Barber).filter(
        Barber.barbershop_id == current_user.barbershop_id,
        Barber.is_active == True
    ).all()
    return barbers


@router.post("/", response_model=BarberResponse, status_code=201)
def create_barber(
    data: BarberCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cadastra novo profissional na barbearia"""
    barber = Barber(
        **data.model_dump(),
        barbershop_id=current_user.barbershop_id  # Vincula ao tenant automaticamente
    )
    db.add(barber)
    db.commit()
    db.refresh(barber)
    return barber


@router.get("/{barber_id}", response_model=BarberResponse)
def get_barber(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Busca um profissional pelo ID"""
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id  # Segurança: só da sua barbearia
    ).first()
    
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    return barber


@router.put("/{barber_id}", response_model=BarberResponse)
def update_barber(
    barber_id: int,
    data: BarberUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza dados de um profissional"""
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    # Atualiza apenas os campos enviados (exclude_unset=True ignora campos não enviados)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(barber, field, value)
    
    db.commit()
    db.refresh(barber)
    return barber


@router.delete("/{barber_id}", status_code=204)
def delete_barber(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Desativa um profissional (soft delete - não apaga do banco)"""
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    # Soft delete: marca como inativo em vez de apagar
    barber.is_active = False
    db.commit()
