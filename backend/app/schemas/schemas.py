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
