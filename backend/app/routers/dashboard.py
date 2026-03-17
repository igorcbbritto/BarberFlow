"""
routers/dashboard.py
Endpoint do dashboard com métricas do dia.
Recebe tz_offset do frontend para filtrar pelo dia correto no fuso do usuário.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.database.connection import get_db
from app.models.models import Appointment, AppointmentStatus, Client, User
from app.auth.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/")
def get_dashboard(
    tz_offset: Optional[int] = Query(None, description="Offset do fuso em minutos (ex: 180 para Brasília)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # tz_offset vem do browser: getTimezoneOffset() — positivo = atrás de UTC
    # Brasília = 180, então somamos 180 min ao UTC para achar o "hoje" local
    offset_delta = timedelta(minutes=tz_offset if tz_offset is not None else 0)

    # "Agora" no horário local do usuário
    now_utc   = datetime.now(timezone.utc).replace(tzinfo=None)
    now_local = now_utc - offset_delta  # subtrai porque tz_offset é positivo quando atrás

    # Início e fim do dia local convertido para UTC (que é como está no banco)
    today_start = now_local.replace(hour=0,  minute=0,  second=0,  microsecond=0)    + offset_delta
    today_end   = now_local.replace(hour=23, minute=59, second=59, microsecond=999999) + offset_delta

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

    from app.models.models import PaymentStatus

    paid_today = db.query(Appointment).options(
        joinedload(Appointment.service)
    ).filter(
        Appointment.barbershop_id == barbershop_id,
        Appointment.datetime >= today_start,
        Appointment.datetime <= today_end,
        Appointment.payment_status == PaymentStatus.paid
    ).all()

    today_revenue = sum(a.service.price for a in paid_today if a.service)

    total_clients = db.query(func.count(Client.id)).filter(
        Client.barbershop_id == barbershop_id
    ).scalar()

    # Formata horário para exibição já convertido para o fuso local
    appointments_list = []
    for a in today_appointments:
        # Converte de UTC para horário local para exibir corretamente
        local_dt = a.datetime - offset_delta
        appointments_list.append({
            "id": a.id,
            "time": local_dt.strftime("%H:%M"),
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
        "current_date": now_local.strftime("%d/%m/%Y"),
    }
