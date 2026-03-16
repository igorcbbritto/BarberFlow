"""
routers/dashboard.py
Endpoint do dashboard com métricas do dia.
"""

from datetime import datetime
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
    """
    Retorna dados do dashboard:
    - Agendamentos de hoje
    - Faturamento do dia
    - Total de clientes
    """
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_end   = datetime.combine(today, datetime.max.time())
    
    barbershop_id = current_user.barbershop_id
    
    # Agendamentos de hoje (exceto cancelados)
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
    
    # Faturamento do dia (apenas concluídos)
    completed_today = db.query(Appointment).options(
        joinedload(Appointment.service)
    ).filter(
        Appointment.barbershop_id == barbershop_id,
        Appointment.datetime >= today_start,
        Appointment.datetime <= today_end,
        Appointment.status == AppointmentStatus.completed
    ).all()
    
    today_revenue = sum(a.service.price for a in completed_today if a.service)
    
    # Total de clientes cadastrados
    total_clients = db.query(func.count(Client.id)).filter(
        Client.barbershop_id == barbershop_id
    ).scalar()
    
    # Formata lista de agendamentos de hoje
    appointments_list = []
    for a in today_appointments:
        appointments_list.append({
            "id": a.id,
            "time": a.datetime.strftime("%H:%M"),
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
        "current_date": today.strftime("%d/%m/%Y"),
    }
