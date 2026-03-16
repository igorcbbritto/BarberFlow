"""
routers/appointments.py
CRUD de agendamentos + endpoint público para clientes agendarem online.
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.models import Appointment, AppointmentStatus, Client, Barber, Service, Barbershop, User
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse, PublicAppointmentCreate
from app.auth.auth import get_current_user

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])


@router.get("/", response_model=List[dict])
def list_appointments(
    date_filter: Optional[str] = Query(None, description="Filtrar por data: YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista agendamentos da barbearia.
    Aceita filtro por data: GET /appointments?date_filter=2024-01-15
    """
    query = db.query(Appointment).options(
        joinedload(Appointment.client),   # JOIN automático para pegar dados do cliente
        joinedload(Appointment.barber),   # JOIN do barbeiro
        joinedload(Appointment.service),  # JOIN do serviço
    ).filter(
        Appointment.barbershop_id == current_user.barbershop_id
    )
    
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            query = query.filter(
                Appointment.datetime >= datetime.combine(filter_date, datetime.min.time()),
                Appointment.datetime <  datetime.combine(filter_date, datetime.max.time()),
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")
    
    appointments = query.order_by(Appointment.datetime).all()
    
    # Monta resposta com dados relacionados
    return [_format_appointment(a) for a in appointments]


@router.post("/", response_model=dict, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cria novo agendamento.
    Valida que cliente, barbeiro e serviço pertencem à mesma barbearia.
    """
    # Valida que o cliente pertence à barbearia
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.barbershop_id == current_user.barbershop_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    
    # Valida barbeiro
    barber = db.query(Barber).filter(
        Barber.id == data.barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")
    
    # Valida serviço
    service = db.query(Service).filter(
        Service.id == data.service_id,
        Service.barbershop_id == current_user.barbershop_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")
    
    appointment = Appointment(
        client_id=data.client_id,
        barber_id=data.barber_id,
        service_id=data.service_id,
        datetime=data.datetime,
        notes=data.notes,
        barbershop_id=current_user.barbershop_id,
        status=AppointmentStatus.confirmed
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    # Recarrega com joins
    appointment = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(Appointment.id == appointment.id).first()
    
    return _format_appointment(appointment)


@router.get("/{appointment_id}", response_model=dict)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointment = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    return _format_appointment(appointment)


@router.put("/{appointment_id}", response_model=dict)
def update_appointment(
    appointment_id: int,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza agendamento (inclusive para cancelar: status='cancelled')"""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(appointment, field, value)
    
    db.commit()
    
    # Recarrega com joins para retornar dados completos
    appointment = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(Appointment.id == appointment_id).first()
    
    return _format_appointment(appointment)


@router.delete("/{appointment_id}", status_code=204)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancela um agendamento (muda status para cancelled)"""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")
    
    appointment.status = AppointmentStatus.cancelled
    db.commit()


# ─────────────────────────────────────────────
# ENDPOINT PÚBLICO (sem autenticação)
# Clientes agendam pelo link da barbearia
# ─────────────────────────────────────────────

@router.get("/public/{slug}/info")
def get_public_barbershop_info(slug: str, db: Session = Depends(get_db)):
    """
    Retorna dados públicos de uma barbearia para a página de agendamento.
    Acessível em: /appointments/public/joaobarber/info
    """
    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug,
        Barbershop.is_active == True
    ).first()
    
    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")
    
    # Busca profissionais e serviços ativos
    barbers = db.query(Barber).filter(
        Barber.barbershop_id == barbershop.id,
        Barber.is_active == True
    ).all()
    
    services = db.query(Service).filter(
        Service.barbershop_id == barbershop.id,
        Service.is_active == True
    ).all()
    
    return {
        "barbershop": {
            "id": barbershop.id,
            "name": barbershop.name,
            "slug": barbershop.slug,
            "phone": barbershop.phone,
            "address": barbershop.address,
        },
        "barbers": [{"id": b.id, "name": b.name, "specialty": b.specialty} for b in barbers],
        "services": [{"id": s.id, "name": s.name, "duration": s.duration, "price": s.price} for s in services],
    }


@router.post("/public/{slug}/book")
def public_book_appointment(
    slug: str,
    data: PublicAppointmentCreate,
    db: Session = Depends(get_db)
):
    """
    Cliente agenda online sem precisar de conta.
    Cria o cliente automaticamente se não existir.
    """
    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug,
        Barbershop.is_active == True
    ).first()
    
    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")
    
    # Busca ou cria cliente pelo telefone
    client = db.query(Client).filter(
        Client.phone == data.client_phone,
        Client.barbershop_id == barbershop.id
    ).first()
    
    if not client:
        client = Client(
            name=data.client_name,
            phone=data.client_phone,
            email=data.client_email,
            barbershop_id=barbershop.id
        )
        db.add(client)
        db.flush()
    
    # Valida barbeiro e serviço
    barber = db.query(Barber).filter(
        Barber.id == data.barber_id,
        Barber.barbershop_id == barbershop.id,
        Barber.is_active == True
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não disponível")
    
    service = db.query(Service).filter(
        Service.id == data.service_id,
        Service.barbershop_id == barbershop.id,
        Service.is_active == True
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não disponível")
    
    appointment = Appointment(
        client_id=client.id,
        barber_id=data.barber_id,
        service_id=data.service_id,
        datetime=data.datetime,
        barbershop_id=barbershop.id,
        status=AppointmentStatus.confirmed
    )
    db.add(appointment)
    db.commit()
    
    return {
        "message": "Agendamento realizado com sucesso!",
        "appointment_id": appointment.id,
        "datetime": appointment.datetime,
        "barber": barber.name,
        "service": service.name,
    }


# ─────────────────────────────────────────────
# Função auxiliar para formatar resposta
# ─────────────────────────────────────────────

def _format_appointment(a: Appointment) -> dict:
    """Converte objeto Appointment em dict com todos os dados"""
    return {
        "id": a.id,
        "datetime": a.datetime.isoformat(),
        "status": a.status.value,
        "notes": a.notes,
        "barbershop_id": a.barbershop_id,
        "created_at": a.created_at.isoformat(),
        "client": {
            "id": a.client.id,
            "name": a.client.name,
            "phone": a.client.phone,
        },
        "barber": {
            "id": a.barber.id,
            "name": a.barber.name,
        },
        "service": {
            "id": a.service.id,
            "name": a.service.name,
            "price": a.service.price,
            "duration": a.service.duration,
        },
    }
