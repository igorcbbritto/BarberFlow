"""
routers/schedules.py
CRUD de horários de trabalho dos profissionais + slots disponíveis.
"""

from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.models import BarberSchedule, Barber, Appointment, AppointmentStatus, User
from app.schemas.schemas import BarberScheduleCreate, BarberScheduleResponse
from app.auth.auth import get_current_user

router = APIRouter(prefix="/schedules", tags=["Agenda dos Profissionais"])


@router.get("/{barber_id}", response_model=List[BarberScheduleResponse])
def get_barber_schedule(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna os horários de trabalho de um profissional"""
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    return db.query(BarberSchedule).filter(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.barbershop_id == current_user.barbershop_id,
        BarberSchedule.is_active == True
    ).order_by(BarberSchedule.day_of_week).all()


@router.post("/{barber_id}")
def save_barber_schedule(
    barber_id: int,
    schedules: List[BarberScheduleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Salva/substitui a agenda completa do profissional"""
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    db.query(BarberSchedule).filter(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.barbershop_id == current_user.barbershop_id
    ).delete()

    for s in schedules:
        db.add(BarberSchedule(
            barber_id=barber_id,
            barbershop_id=current_user.barbershop_id,
            day_of_week=s.day_of_week,
            start_time=s.start_time,
            end_time=s.end_time,
            is_active=True
        ))

    db.commit()
    return {"message": f"Agenda de {barber.name} salva com sucesso!"}


@router.get("/public/slots")
def get_available_slots(
    barber_id: int = Query(...),
    service_id: int = Query(...),
    date: str = Query(..., description="YYYY-MM-DD"),
    slug: str = Query(...),
    tz_offset: int = Query(180, description="Offset em minutos (padrão 180 = Brasília UTC-3)"),
    db: Session = Depends(get_db)
):
    """
    Retorna horários VAGOS de um profissional em uma data.
    Endpoint público — sem autenticação.
    """
    from app.models.models import Barbershop, Service

    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug, Barbershop.is_active == True
    ).first()
    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == barbershop.id,
        Barber.is_active == True
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    service = db.query(Service).filter(
        Service.id == service_id,
        Service.barbershop_id == barbershop.id,
        Service.is_active == True
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    try:
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Use YYYY-MM-DD")

    # Dia da semana: Python weekday() → 0=Seg, igual ao nosso modelo
    day_of_week = filter_date.weekday()

    schedule = db.query(BarberSchedule).filter(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.barbershop_id == barbershop.id,
        BarberSchedule.day_of_week == day_of_week,
        BarberSchedule.is_active == True
    ).first()

    if not schedule:
        return {"slots": [], "message": "Profissional não trabalha neste dia"}

    # Gera todos os slots com base na duração do serviço
    start_h, start_m = map(int, schedule.start_time.split(":"))
    end_h,   end_m   = map(int, schedule.end_time.split(":"))
    slot_duration    = service.duration

    current = datetime.combine(filter_date, datetime.min.time()).replace(
        hour=start_h, minute=start_m
    )
    end_dt = datetime.combine(filter_date, datetime.min.time()).replace(
        hour=end_h, minute=end_m
    )

    all_slots = []
    while current + timedelta(minutes=slot_duration) <= end_dt:
        all_slots.append(current)
        current += timedelta(minutes=slot_duration)

    # Busca ocupados — banco em UTC, converte usando offset enviado pelo browser
    offset = timedelta(minutes=tz_offset)
    day_start_utc = datetime.combine(filter_date, datetime.min.time()) + offset
    day_end_utc   = datetime.combine(filter_date, datetime.max.time()) + offset

    existing = db.query(Appointment).filter(
        Appointment.barber_id == barber_id,
        Appointment.barbershop_id == barbershop.id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime >= day_start_utc,
        Appointment.datetime <= day_end_utc,
    ).all()

    occupied = set()
    for appt in existing:
        local_dt = appt.datetime - offset
        occupied.add(local_dt.strftime("%H:%M"))

    # Horário atual no fuso do usuário
    now_brasilia = datetime.utcnow() - timedelta(minutes=tz_offset)

    available = []
    for slot in all_slots:
        time_str = slot.strftime("%H:%M")
        if time_str in occupied:
            continue
        if filter_date == datetime.utcnow().date():
            if slot <= now_brasilia + timedelta(minutes=30):
                continue
        available.append({
            "time": time_str,
            "datetime_local": slot.strftime("%Y-%m-%dT%H:%M"),
        })

    return {
        "slots": available,
        "date": date,
        "barber_name": barber.name,
        "service_name": service.name,
        "service_duration": service.duration,
        "work_hours": f"{schedule.start_time} — {schedule.end_time}",
    }
