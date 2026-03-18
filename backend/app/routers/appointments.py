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
    date_filter: Optional[str] = Query(None),
    tz_offset: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import timedelta
    query = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(Appointment.barbershop_id == current_user.barbershop_id)

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            offset_delta = timedelta(minutes=tz_offset if tz_offset is not None else 0)
            day_start = datetime.combine(filter_date, datetime.min.time()) + offset_delta
            day_end   = datetime.combine(filter_date, datetime.max.time()) + offset_delta
            query = query.filter(
                Appointment.datetime >= day_start,
                Appointment.datetime <= day_end,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de data inválido. Use YYYY-MM-DD")

    appointments = query.order_by(Appointment.datetime).all()
    return [_format_appointment(a) for a in appointments]


@router.post("/", response_model=dict, status_code=201)
def create_appointment(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    client = db.query(Client).filter(
        Client.id == data.client_id,
        Client.barbershop_id == current_user.barbershop_id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    barber = db.query(Barber).filter(
        Barber.id == data.barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    service = db.query(Service).filter(
        Service.id == data.service_id,
        Service.barbershop_id == current_user.barbershop_id
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    from datetime import timezone as tz, timedelta
    dt = data.datetime
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        dt = dt.astimezone(tz.utc).replace(tzinfo=None)

    conflito = db.query(Appointment).filter(
        Appointment.barber_id == data.barber_id,
        Appointment.barbershop_id == current_user.barbershop_id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime >= dt - timedelta(minutes=59),
        Appointment.datetime <= dt + timedelta(minutes=59),
    ).first()

    if conflito:
        raise HTTPException(
            status_code=400,
            detail=f"Profissional já tem agendamento próximo a este horário ({conflito.datetime.strftime('%H:%M')}). Escolha outro horário."
        )

    appointment = Appointment(
        client_id=data.client_id,
        barber_id=data.barber_id,
        service_id=data.service_id,
        datetime=dt,
        notes=data.notes,
        barbershop_id=current_user.barbershop_id,
        status=AppointmentStatus.confirmed
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

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
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    update_data = data.model_dump(exclude_unset=True)

    from datetime import timezone as tz
    if 'appointment_datetime' in update_data and update_data['appointment_datetime'] is not None:
        dt = update_data.pop('appointment_datetime')
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt = dt.astimezone(tz.utc).replace(tzinfo=None)
        update_data['datetime'] = dt

    for field, value in update_data.items():
        setattr(appointment, field, value)

    db.commit()

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
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    appointment.status = AppointmentStatus.cancelled
    db.commit()


@router.get("/public/{slug}/info")
def get_public_barbershop_info(slug: str, db: Session = Depends(get_db)):
    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug,
        Barbershop.is_active == True
    ).first()

    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

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
            "id":       barbershop.id,
            "name":     barbershop.name,
            "slug":     barbershop.slug,
            "phone":    barbershop.phone,
            "address":  barbershop.address,
            "logo_url": barbershop.logo_url,
        },
        "barbers":  [{"id": b.id, "name": b.name, "specialty": b.specialty} for b in barbers],
        "services": [{"id": s.id, "name": s.name, "duration": s.duration, "price": s.price} for s in services],
    }


@router.post("/public/{slug}/book")
def public_book_appointment(
    slug: str,
    data: PublicAppointmentCreate,
    db: Session = Depends(get_db)
):
    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug,
        Barbershop.is_active == True
    ).first()

    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

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

    from datetime import timezone as tz, timedelta
    dt_public = data.datetime
    if hasattr(dt_public, 'tzinfo') and dt_public.tzinfo is not None:
        dt_public = dt_public.astimezone(tz.utc).replace(tzinfo=None)

    conflito_pub = db.query(Appointment).filter(
        Appointment.barber_id == data.barber_id,
        Appointment.barbershop_id == barbershop.id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime >= dt_public - timedelta(minutes=59),
        Appointment.datetime <= dt_public + timedelta(minutes=59),
    ).first()

    if conflito_pub:
        local_time = (conflito_pub.datetime - timedelta(hours=3)).strftime('%H:%M')
        raise HTTPException(
            status_code=400,
            detail=f"Este horário já está ocupado ({local_time}). Por favor escolha outro horário."
        )

    appointment = Appointment(
        client_id=client.id,
        barber_id=data.barber_id,
        service_id=data.service_id,
        datetime=dt_public,
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


def _format_appointment(a: Appointment) -> dict:
    return {
        "id":           a.id,
        "datetime":     a.datetime.isoformat(),
        "status":       a.status.value,
        "notes":        a.notes,
        "barbershop_id":a.barbershop_id,
        "created_at":   a.created_at.isoformat(),
        "client":  {"id": a.client.id,  "name": a.client.name,  "phone": a.client.phone},
        "barber":  {"id": a.barber.id,  "name": a.barber.name},
        "service": {"id": a.service.id, "name": a.service.name, "price": a.service.price, "duration": a.service.duration},
    }
