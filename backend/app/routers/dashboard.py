"""
routers/dashboard.py
Endpoint do dashboard com métricas do dia.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database.connection import get_db
from app.models.models import Appointment, AppointmentStatus, Client, User
from app.auth.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Usa UTC para filtrar o dia — o frontend converte para horário local
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end   = now_utc.replace(hour=23, minute=59, second=59, microsecond=999999)

    barbershop_id = current_user.barbershop_id

    today_appointments = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(
        Appointment.barbershop_id == barbershop_id,
        Appointment.datetime >= today_start,
        Appointment.datetime <= today_end,
        Appointment.status != AppointmentStatus.cancelled
    ).order_by(Appointment.datetime).all()

    completed_today = db.query(Appointment).options(
        joinedload(Appointment.service)
    ).filter(
        Appointment.barbershop_id == barbershop_id,
        Appointment.datetime >= today_start,
        Appointment.datetime <= today_end,
        Appointment.status == AppointmentStatus.completed
    ).all()

    today_revenue = sum(a.service.price for a in completed_today if a.service)

    total_clients = db.query(func.count(Client.id)).filter(
        Client.barbershop_id == barbershop_id
    ).scalar()

    appointments_list = []
    for a in today_appointments:
        appointments_list.append({
            "id": a.id,
            "time": a.datetime.strftime("%H:%M"),
            "datetime_iso": a.datetime.isoformat(),
            "client_name": a.client.name if a.client else "—",
            "barber_name": a.barber.name if a.barber else "—",
            "service_name": a.service.name if a.service else "—",
            "service_price": a.service.price if a.service else 0,
            "status": a.status.value,
        })

    return {
        "today_appointments_count": len(today_appointments),
        "today_revenue": round(today_revenue, 2),
        "total_clients": total_clients,
        "today_appointments": appointments_list,
        "current_date": now_utc.strftime("%d/%m/%Y"),
        "server_utc_offset": 0,
    }
