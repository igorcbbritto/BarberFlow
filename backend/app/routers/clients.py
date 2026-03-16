"""
routers/clients.py
CRUD de clientes da barbearia.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import Client, User
from app.schemas.schemas import ClientCreate, ClientUpdate, ClientResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/clients", tags=["Clientes"])


@router.get("/", response_model=List[ClientResponse])
def list_clients(
    search: Optional[str] = Query(None, description="Busca por nome ou telefone"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista clientes da barbearia.
    Aceita parâmetro de busca: GET /clients?search=João
    """
    query = db.query(Client).filter(
        Client.barbershop_id == current_user.barbershop_id
    )
    
    # Filtro de busca opcional
    if search:
        query = query.filter(
            Client.name.ilike(f"%{search}%") |  # ilike = case-insensitive
            Client.phone.ilike(f"%{search}%")
        )
    
    return query.order_by(Client.name).all()


@router.post("/", response_model=ClientResponse, status_code=201)
def create_client(
    data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cadastra novo cliente"""
    client = Client(
        **data.model_dump(),
        barbershop_id=current_user.barbershop_id
    )
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.get("/{client_id}", response_model=ClientResponse)
def get_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.barbershop_id == current_user.barbershop_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return client


@router.put("/{client_id}", response_model=ClientResponse)
def update_client(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.barbershop_id == current_user.barbershop_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(client, field, value)
    
    db.commit()
    db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=204)
def delete_client(
    client_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.barbershop_id == current_user.barbershop_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    db.delete(client)
    db.commit()
