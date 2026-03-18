"""
routers/schedules.py
Agenda dos profissionais com suporte a intervalos (almoço, café).
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.models import BarberSchedule, Barber, Appointment, AppointmentStatus, User
from app.auth.auth import get_current_user

router = APIRouter(prefix="/schedules", tags=["Agenda dos Profissionais"])


# ── Schemas ──

class ScheduleCreate(BaseModel):
    day_of_week:  int
    start_time:   str          # "08:00"
    end_time:     str          # "18:00"
    break1_start: Optional[str] = None   # "12:00" almoço
    break1_end:   Optional[str] = None   # "13:00"
    break2_start: Optional[str] = None   # "15:30" café
    break2_end:   Optional[str] = None   # "15:50"


class ScheduleResponse(BaseModel):
    id:           int
    barber_id:    int
    day_of_week:  int
    start_time:   str
    end_time:     str
    break1_start: Optional[str]
    break1_end:   Optional[str]
    break2_start: Optional[str]
    break2_end:   Optional[str]
    is_active:    bool

    class Config:
        from_attributes = True


# ── GET agenda de um profissional ──

@router.get("/{barber_id}", response_model=List[ScheduleResponse])
def get_barber_schedule(
    barber_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
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


# ── POST salva agenda completa ──

@router.post("/{barber_id}")
def save_barber_schedule(
    barber_id: int,
    schedules: List[ScheduleCreate],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    barber = db.query(Barber).filter(
        Barber.id == barber_id,
        Barber.barbershop_id == current_user.barbershop_id
    ).first()
    if not barber:
        raise HTTPException(status_code=404, detail="Profissional não encontrado")

    # Apaga agenda atual e recria
    db.query(BarberSchedule).filter(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.barbershop_id == current_user.barbershop_id
    ).delete()

    for s in schedules:
        db.add(BarberSchedule(
            barber_id    = barber_id,
            barbershop_id= current_user.barbershop_id,
            day_of_week  = s.day_of_week,
            start_time   = s.start_time,
            end_time     = s.end_time,
            break1_start = s.break1_start,
            break1_end   = s.break1_end,
            break2_start = s.break2_start,
            break2_end   = s.break2_end,
            is_active    = True
        ))

    db.commit()
    return {"message": f"Agenda de {barber.name} salva com sucesso!"}


# ── GET slots disponíveis (público) ──

@router.get("/public/slots")
def get_available_slots(
    barber_id:  int = Query(...),
    service_id: int = Query(...),
    date:       str = Query(...),
    slug:       str = Query(...),
    tz_offset:  int = Query(180),
    db: Session = Depends(get_db)
):
    """Retorna horários vagos respeitando intervalos de almoço/café."""
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

    day_of_week = filter_date.weekday()

    schedule = db.query(BarberSchedule).filter(
        BarberSchedule.barber_id    == barber_id,
        BarberSchedule.barbershop_id== barbershop.id,
        BarberSchedule.day_of_week  == day_of_week,
        BarberSchedule.is_active    == True
    ).first()

    if not schedule:
        return {"slots": [], "message": "Profissional não trabalha neste dia"}

    # Constrói lista de períodos de intervalo
    def time_range(start_str, end_str):
        """Converte 'HH:MM'–'HH:MM' para (datetime, datetime) do dia filtrado"""
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        base = datetime.combine(filter_date, datetime.min.time())
        return (
            base.replace(hour=sh, minute=sm),
            base.replace(hour=eh, minute=em)
        )

    breaks = []
    if schedule.break1_start and schedule.break1_end:
        breaks.append(time_range(schedule.break1_start, schedule.break1_end))
    if schedule.break2_start and schedule.break2_end:
        breaks.append(time_range(schedule.break2_start, schedule.break2_end))

    def in_break(slot_dt):
        """Verifica se o slot cai dentro de algum intervalo"""
        slot_end = slot_dt + timedelta(minutes=service.duration)
        for b_start, b_end in breaks:
            # Slot conflita com intervalo se sobrepõe
            if slot_dt < b_end and slot_end > b_start:
                return True
        return False

    # Gera todos os slots do dia
    start_h, start_m = map(int, schedule.start_time.split(":"))
    end_h,   end_m   = map(int, schedule.end_time.split(":"))

    current = datetime.combine(filter_date, datetime.min.time()).replace(
        hour=start_h, minute=start_m
    )
    end_dt = datetime.combine(filter_date, datetime.min.time()).replace(
        hour=end_h, minute=end_m
    )

    all_slots = []
    while current + timedelta(minutes=service.duration) <= end_dt:
        all_slots.append(current)
        current += timedelta(minutes=service.duration)

    # Busca ocupados no banco (UTC)
    offset = timedelta(minutes=tz_offset)
    day_start_utc = datetime.combine(filter_date, datetime.min.time()) + offset
    day_end_utc   = datetime.combine(filter_date, datetime.max.time()) + offset

    existing = db.query(Appointment).filter(
        Appointment.barber_id    == barber_id,
        Appointment.barbershop_id== barbershop.id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime     >= day_start_utc,
        Appointment.datetime     <= day_end_utc,
    ).all()

    occupied = set()
    for appt in existing:
        local_dt = appt.datetime - offset
        occupied.add(local_dt.strftime("%H:%M"))

    # Horário atual no fuso do usuário
    now_local = datetime.utcnow() - timedelta(minutes=tz_offset)

    available = []
    for slot in all_slots:
        time_str = slot.strftime("%H:%M")
        if time_str in occupied:
            continue
        if in_break(slot):
            continue
        if filter_date == datetime.utcnow().date():
            if slot <= now_local + timedelta(minutes=30):
                continue
        available.append({
            "time": time_str,
            "datetime_local": slot.strftime("%Y-%m-%dT%H:%M"),
        })

    # Monta info dos intervalos para exibir
    breaks_info = []
    if schedule.break1_start:
        breaks_info.append(f"Almoço {schedule.break1_start}–{schedule.break1_end}")
    if schedule.break2_start:
        breaks_info.append(f"Intervalo {schedule.break2_start}–{schedule.break2_end}")

    return {
        "slots":            available,
        "date":             date,
        "barber_name":      barber.name,
        "service_name":     service.name,
        "service_duration": service.duration,
        "work_hours":       f"{schedule.start_time}–{schedule.end_time}",
        "breaks":           breaks_info,
    }
