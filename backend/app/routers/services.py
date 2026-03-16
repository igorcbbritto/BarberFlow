"""
routers/services.py
CRUD de serviços oferecidos pela barbearia.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Service, User
from app.schemas.schemas import ServiceCreate, ServiceUpdate, ServiceResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/services", tags=["Serviços"])


@router.get("/", response_model=List[ServiceResponse])
def list_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista todos os serviços ativos da barbearia"""
    services = db.query(Service).filter(
        Service.barbershop_id == current_user.barbershop_id,
        Service.is_active == True
    ).all()
    return services


@router.post("/", response_model=ServiceResponse, status_code=201)
def create_service(
    data: ServiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cadastra novo serviço"""
    service = Service(
        **data.model_dump(),
        barbershop_id=current_user.barbershop_id
    )
    db.add(service)
    db.commit()
    db.refresh(service)
    return service


@router.get("/{service_id}", response_model=ServiceResponse)
def get_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.barbershop_id == current_user.barbershop_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    return service


@router.put("/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.barbershop_id == current_user.barbershop_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    return service


@router.delete("/{service_id}", status_code=204)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Desativa serviço (soft delete)"""
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.barbershop_id == current_user.barbershop_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    service.is_active = False
    db.commit()
