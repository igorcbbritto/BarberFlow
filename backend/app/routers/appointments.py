"""
routers/appointments.py
CRUD de agendamentos + endpoint público para clientes agendarem online.
"""

from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app.database.connection import get_db
from app.models.models import Appointment, AppointmentStatus, PaymentStatus, Client, Barber, Service, Barbershop, User
from app.schemas.schemas import AppointmentCreate, AppointmentUpdate, AppointmentResponse, PublicAppointmentCreate
from app.auth.auth import get_current_user

router = APIRouter(prefix="/appointments", tags=["Agendamentos"])


@router.get("/", response_model=List[dict])
def list_appointments(
    date_filter: Optional[str] = Query(None, description="Filtrar por data: YYYY-MM-DD"),
    tz_offset: Optional[int] = Query(None, description="Offset do fuso em minutos"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from datetime import timedelta
    query = db.query(Appointment).options(
        joinedload(Appointment.client),
        joinedload(Appointment.barber),
        joinedload(Appointment.service),
    ).filter(
        Appointment.barbershop_id == current_user.barbershop_id
    )

    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, "%Y-%m-%d").date()
            # tz_offset é positivo quando atrás de UTC (ex: Brasília = 180 min)
            # Somamos ao UTC para achar o início/fim do dia local no banco
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
    
    # Remove timezone info para salvar em UTC puro no banco
    from datetime import timezone as tz
    dt = data.datetime
    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        dt = dt.astimezone(tz.utc).replace(tzinfo=None)

    # Valida conflito de horário para o mesmo profissional
    from datetime import timedelta
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
        status=AppointmentStatus.scheduled
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
    
    update_data = data.model_dump(exclude_unset=True)

    # Trata o campo de data/hora (renomeado para evitar conflito com módulo datetime)
    from datetime import timezone as tz
    if 'appointment_datetime' in update_data and update_data['appointment_datetime'] is not None:
        dt = update_data.pop('appointment_datetime')
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            dt = dt.astimezone(tz.utc).replace(tzinfo=None)
        update_data['datetime'] = dt

    for field, value in update_data.items():
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
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancela (se ativo) ou exclui definitivamente (se já cancelado)"""
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.barbershop_id == current_user.barbershop_id
    ).first()

    if not appointment:
        raise HTTPException(status_code=404, detail="Agendamento não encontrado")

    if appointment.status == AppointmentStatus.cancelled:
        db.delete(appointment)
    else:
        appointment.status = AppointmentStatus.cancelled
    db.commit()


@router.patch("/{appointment_id}/payment", response_model=dict)
def toggle_payment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Alterna status de pagamento entre pago e não pago"""
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

    appointment.payment_status = (
        PaymentStatus.unpaid if appointment.payment_status == PaymentStatus.paid
        else PaymentStatus.paid
    )
    db.commit()
    return _format_appointment(appointment)


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
    
    # Remove timezone info para salvar UTC puro
    from datetime import timezone as tz, timedelta
    dt_public = data.datetime
    if hasattr(dt_public, 'tzinfo') and dt_public.tzinfo is not None:
        dt_public = dt_public.astimezone(tz.utc).replace(tzinfo=None)

    # Valida conflito de horário — mesmo profissional no mesmo horário
    conflito_pub = db.query(Appointment).filter(
        Appointment.barber_id == data.barber_id,
        Appointment.barbershop_id == barbershop.id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime >= dt_public - timedelta(minutes=59),
        Appointment.datetime <= dt_public + timedelta(minutes=59),
    ).first()

    if conflito_pub:
        # Converte UTC para Brasília para mostrar na mensagem
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
        status=AppointmentStatus.scheduled
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




@router.get("/public/{slug}/slots")
def get_available_slots(
    slug: str,
    barber_id: int,
    service_id: int,
    date: str,  # YYYY-MM-DD no fuso local do cliente
    db: Session = Depends(get_db)
):
    """
    Retorna horários vagos de um profissional em uma data.
    Considera: horário de trabalho, duração do serviço e agendamentos existentes.
    """
    from datetime import timedelta, time
    from app.models.models import BarberSchedule

    barbershop = db.query(Barbershop).filter(
        Barbershop.slug == slug,
        Barbershop.is_active == True
    ).first()
    if not barbershop:
        raise HTTPException(status_code=404, detail="Barbearia não encontrada")

    # Valida serviço
    service = db.query(Service).filter(
        Service.id == service_id,
        Service.barbershop_id == barbershop.id,
        Service.is_active == True
    ).first()
    if not service:
        raise HTTPException(status_code=404, detail="Serviço não encontrado")

    # Parse da data enviada pelo cliente (já no fuso local dele)
    try:
        filter_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Data inválida. Use YYYY-MM-DD")

    # Dia da semana: 0=Segunda...6=Domingo (Python: Monday=0)
    dia_semana = filter_date.weekday()

    # Busca horário de trabalho do profissional nesse dia
    schedule = db.query(BarberSchedule).filter(
        BarberSchedule.barber_id == barber_id,
        BarberSchedule.barbershop_id == barbershop.id,
        BarberSchedule.dia_semana == dia_semana,
        BarberSchedule.ativo == True
    ).first()

    # Se não tem horário configurado, usa padrão 08:00-18:00
    if schedule:
        h_inicio = int(schedule.hora_inicio.split(":")[0])
        m_inicio = int(schedule.hora_inicio.split(":")[1])
        h_fim    = int(schedule.hora_fim.split(":")[0])
        m_fim    = int(schedule.hora_fim.split(":")[1])
    else:
        h_inicio, m_inicio = 8,  0
        h_fim,    m_fim    = 18, 0

    # Busca agendamentos do dia para este barbeiro (o banco está em UTC, offset=0 por default)
    # O cliente envia a data local, o banco guarda UTC — assumimos UTC=local para simplicidade
    # (o offset já é tratado na exibição pelo frontend)
    day_start = datetime.combine(filter_date, datetime.min.time())
    day_end   = datetime.combine(filter_date, datetime.max.time())

    existing = db.query(Appointment).filter(
        Appointment.barber_id == barber_id,
        Appointment.barbershop_id == barbershop.id,
        Appointment.status.notin_([AppointmentStatus.cancelled]),
        Appointment.datetime >= day_start,
        Appointment.datetime <= day_end,
    ).all()

    # Horários já ocupados (início e fim de cada agendamento existente)
    occupied = []
    for a in existing:
        a_service = db.query(Service).filter(Service.id == a.service_id).first()
        dur = a_service.duration if a_service else 30
        occupied.append((a.datetime, a.datetime + timedelta(minutes=dur)))

    # Gera slots de acordo com a duração do serviço escolhido
    duration = service.duration
    slots = []
    current = datetime.combine(filter_date, time(h_inicio, m_inicio))
    end_of_day = datetime.combine(filter_date, time(h_fim, m_fim))

    now_utc = datetime.now()  # Para não mostrar slots no passado
    today = now_utc.date()

    while current + timedelta(minutes=duration) <= end_of_day:
        slot_end = current + timedelta(minutes=duration)

        # Não mostrar slots no passado (só para hoje)
        if filter_date == today and current <= now_utc:
            current += timedelta(minutes=30)
            continue

        # Verifica conflito com agendamentos existentes
        conflict = False
        for occ_start, occ_end in occupied:
            if current < occ_end and slot_end > occ_start:
                conflict = True
                break

        if not conflict:
            slots.append({
                "time": current.strftime("%H:%M"),
                "datetime_local": current.isoformat(),
            })

        current += timedelta(minutes=30)

    return {
        "date": date,
        "barber_id": barber_id,
        "service_duration": duration,
        "slots": slots,
        "working": True if schedule else False,
        "schedule": {
            "inicio": schedule.hora_inicio if schedule else "08:00",
            "fim": schedule.hora_fim if schedule else "18:00",
        }
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
        "payment_status": a.payment_status.value if a.payment_status else "unpaid",
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
