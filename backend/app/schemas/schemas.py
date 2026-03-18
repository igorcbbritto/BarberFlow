"""
schemas/schemas.py
Schemas Pydantic para validação de dados de entrada e saída da API.

- "Create" = dados para criar um novo registro (vem do usuário)
- "Update" = dados para atualizar (campos opcionais)  
- "Response" = dados retornados pela API (inclui id, created_at, etc.)
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, field_validator
from app.models.models import AppointmentStatus, PlanType


# ═══════════════════════════════════════════
# AUTH SCHEMAS
# ═══════════════════════════════════════════

class RegisterRequest(BaseModel):
    """Dados para criar nova barbearia + usuário admin"""
    barbershop_name: str
    barbershop_slug: str          # URL: meusistema.com/barbearia/joaobarber
    user_name: str
    email: EmailStr
    password: str

    @field_validator("barbershop_slug")
    @classmethod
    def slug_lowercase(cls, v):
        # Slug deve ser minúsculo e sem espaços
        return v.lower().replace(" ", "-")

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v):
        if len(v) < 6:
            raise ValueError("Senha deve ter pelo menos 6 caracteres")
        return v


class LoginRequest(BaseModel):
    """Dados para fazer login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Resposta do login com o token JWT"""
    access_token: str
    token_type: str = "bearer"
    barbershop_id: int
    barbershop_name: str
    barbershop_slug: str
    user_name: str
    is_admin: bool = False
    must_change_password: bool = False


# ═══════════════════════════════════════════
# BARBERSHOP SCHEMAS
# ═══════════════════════════════════════════

class BarbershopResponse(BaseModel):
    """Dados públicos de uma barbearia"""
    id: int
    name: str
    slug: str
    phone: Optional[str]
    address: Optional[str]
    plan: PlanType

    class Config:
        from_attributes = True  # Permite converter objeto SQLAlchemy para schema


# ═══════════════════════════════════════════
# BARBER SCHEMAS (Profissionais)
# ═══════════════════════════════════════════

class BarberCreate(BaseModel):
    """Dados para cadastrar novo barbeiro"""
    name: str
    phone: Optional[str] = None
    specialty: Optional[str] = None


class BarberUpdate(BaseModel):
    """Dados para atualizar barbeiro (todos opcionais)"""
    name: Optional[str] = None
    phone: Optional[str] = None
    specialty: Optional[str] = None
    is_active: Optional[bool] = None


class BarberResponse(BaseModel):
    """Retorno de dados do barbeiro"""
    id: int
    name: str
    phone: Optional[str]
    specialty: Optional[str]
    is_active: bool
    barbershop_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# SERVICE SCHEMAS (Serviços)
# ═══════════════════════════════════════════

class ServiceCreate(BaseModel):
    """Dados para cadastrar novo serviço"""
    name: str
    description: Optional[str] = None
    duration: int      # em minutos
    price: float       # em reais

    @field_validator("price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("Preço deve ser maior que zero")
        return v

    @field_validator("duration")
    @classmethod
    def duration_positive(cls, v):
        if v <= 0:
            raise ValueError("Duração deve ser maior que zero")
        return v


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    is_active: Optional[bool] = None


class ServiceResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    duration: int
    price: float
    is_active: bool
    barbershop_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# CLIENT SCHEMAS (Clientes)
# ═══════════════════════════════════════════

class ClientCreate(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    notes: Optional[str] = None


class ClientResponse(BaseModel):
    id: int
    name: str
    phone: Optional[str]
    email: Optional[str]
    notes: Optional[str]
    barbershop_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# APPOINTMENT SCHEMAS (Agendamentos)
# ═══════════════════════════════════════════

class AppointmentCreate(BaseModel):
    """Dados para criar agendamento"""
    client_id: int
    barber_id: int
    service_id: int
    datetime: datetime
    notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    """Dados para atualizar agendamento"""
    client_id: Optional[int] = None
    barber_id: Optional[int] = None
    service_id: Optional[int] = None
    appointment_datetime: Optional[datetime] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

    model_config = {"populate_by_name": True}


class AppointmentResponse(BaseModel):
    """Retorno completo do agendamento (com dados relacionados)"""
    id: int
    datetime: datetime
    status: AppointmentStatus
    notes: Optional[str]
    barbershop_id: int
    created_at: datetime

    # Dados do cliente, barbeiro e serviço (join automático)
    client: ClientResponse
    barber: BarberResponse
    service: ServiceResponse

    class Config:
        from_attributes = True


# Versão simplificada para listagens
class AppointmentSimple(BaseModel):
    id: int
    datetime: datetime
    status: AppointmentStatus
    client_name: str
    barber_name: str
    service_name: str
    service_price: float
    notes: Optional[str]

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# DASHBOARD SCHEMA
# ═══════════════════════════════════════════

class DashboardResponse(BaseModel):
    """Dados do dashboard principal"""
    today_appointments_count: int     # Agendamentos do dia
    today_revenue: float              # Faturamento do dia
    total_clients: int                # Total de clientes cadastrados
    today_appointments: List[dict]    # Lista dos agendamentos de hoje


# ═══════════════════════════════════════════
# AGENDAMENTO PÚBLICO (para clientes)
# ═══════════════════════════════════════════

class PublicAppointmentCreate(BaseModel):
    """
    Agendamento feito pelo cliente pelo link público.
    Não precisa de autenticação.
    """
    client_name: str
    client_phone: str
    client_email: Optional[str] = None
    barber_id: int
    service_id: int
    datetime: datetime


# ═══════════════════════════════════════════
# BARBER SCHEDULE SCHEMAS (Horários de trabalho)
# ═══════════════════════════════════════════

class BarberScheduleCreate(BaseModel):
    """Define horário de trabalho de um profissional em um dia da semana"""
    barber_id:   int
    day_of_week: int    # 0=Segunda ... 6=Domingo
    start_time:  str    # "08:00"
    end_time:    str    # "18:00"

    @field_validator("day_of_week")
    @classmethod
    def valid_day(cls, v):
        if not 0 <= v <= 6:
            raise ValueError("Dia deve ser entre 0 (Segunda) e 6 (Domingo)")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_time(cls, v):
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Hora deve estar no formato HH:MM")
        return v


class BarberScheduleResponse(BaseModel):
    id:           int
    barber_id:    int
    day_of_week:  int
    start_time:   str
    end_time:     str
    is_active:    bool

    class Config:
        from_attributes = True


class AvailableSlot(BaseModel):
    """Horário disponível para agendamento"""
    time:     str   # "09:00"
    datetime: str   # ISO string para enviar ao backend


# ═══════════════════════════════════════════
# BARBER SCHEDULE SCHEMAS
# ═══════════════════════════════════════════

class BarberScheduleCreate(BaseModel):
    """Cria ou atualiza horário de um dia da semana"""
    day_of_week: int   # 0=Segunda ... 6=Domingo
    start_time: str    # "08:00"
    end_time: str      # "18:00"
    is_active: bool = True

class BarberScheduleResponse(BaseModel):
    id: int
    barber_id: int
    day_of_week: int
    start_time: str
    end_time: str
    is_active: bool

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# BARBER SCHEDULE SCHEMAS (Horários de trabalho)
# ═══════════════════════════════════════════

class ScheduleCreate(BaseModel):
    """Horário de trabalho de um dia da semana"""
    weekday:    int    # 0=Seg, 1=Ter... 6=Dom
    start_time: str    # "08:00"
    end_time:   str    # "18:00"

    @field_validator("weekday")
    @classmethod
    def valid_weekday(cls, v):
        if not 0 <= v <= 6:
            raise ValueError("Dia da semana deve ser entre 0 (Seg) e 6 (Dom)")
        return v


class ScheduleResponse(BaseModel):
    id:         int
    barber_id:  int
    weekday:    int
    start_time: str
    end_time:   str
    is_active:  bool

    class Config:
        from_attributes = True


# ═══════════════════════════════════════════
# BARBER SCHEDULE SCHEMAS (Agenda dos profissionais)
# ═══════════════════════════════════════════

class BarberScheduleCreate(BaseModel):
    """Horário de trabalho para um dia da semana"""
    day_of_week: int   # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom
    start_time: str    # "08:00"
    end_time: str      # "18:00"

    @field_validator("day_of_week")
    @classmethod
    def valid_day(cls, v):
        if v not in range(7):
            raise ValueError("Dia da semana deve ser entre 0 (Segunda) e 6 (Domingo)")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def valid_time(cls, v):
        import re
        if not re.match(r"^\d{2}:\d{2}$", v):
            raise ValueError("Horário deve estar no formato HH:MM")
        return v


class BarberScheduleResponse(BaseModel):
    id: int
    barber_id: int
    day_of_week: int
    start_time: str
    end_time: str
    is_active: bool

    class Config:
        from_attributes = True
