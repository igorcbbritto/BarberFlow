"""
models/models.py
Tabelas do banco de dados.

Novidades:
- Barbershop: logo_url
- User: must_change_password, reset_code, reset_code_expires
- BarberSchedule: break1_start, break1_end, break2_start, break2_end
- PasswordResetCode: tabela de códigos temporários
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
import enum

from app.database.connection import Base


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AppointmentStatus(str, enum.Enum):
    pending   = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"


class PlanType(str, enum.Enum):
    free    = "free"
    basic   = "basic"
    premium = "premium"


class Barbershop(Base):
    __tablename__ = "barbershops"
    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)
    slug       = Column(String(50), unique=True, index=True)
    phone      = Column(String(20), nullable=True)
    address    = Column(String(200), nullable=True)
    logo_url   = Column(String(500), nullable=True)   # URL da logomarca
    plan       = Column(Enum(PlanType), default=PlanType.free)
    is_active  = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    users        = relationship("User", back_populates="barbershop")
    barbers      = relationship("Barber", back_populates="barbershop")
    services     = relationship("Service", back_populates="barbershop")
    clients      = relationship("Client", back_populates="barbershop")
    appointments = relationship("Appointment", back_populates="barbershop")


class User(Base):
    __tablename__ = "users"
    id                   = Column(Integer, primary_key=True, index=True)
    name                 = Column(String(100), nullable=False)
    email                = Column(String(150), unique=True, index=True, nullable=False)
    password_hash        = Column(String(200), nullable=False)
    barbershop_id        = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    is_active            = Column(Boolean, default=True)
    must_change_password = Column(Boolean, default=False)  # True = pede troca no próximo login
    created_at           = Column(DateTime, default=utcnow)

    barbershop    = relationship("Barbershop", back_populates="users")
    reset_codes   = relationship("PasswordResetCode", back_populates="user", cascade="all, delete-orphan")


class PasswordResetCode(Base):
    """
    Código temporário de 6 dígitos para resetar senha.
    Admin gera, usuário digita no login para criar nova senha.
    Expira em 1 hora.
    """
    __tablename__ = "password_reset_codes"
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    code       = Column(String(6), nullable=False)
    used       = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    user = relationship("User", back_populates="reset_codes")


class Barber(Base):
    __tablename__ = "barbers"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=True)
    specialty     = Column(String(100), nullable=True)
    is_active     = Column(Boolean, default=True)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=utcnow)

    barbershop   = relationship("Barbershop", back_populates="barbers")
    appointments = relationship("Appointment", back_populates="barber")
    schedules    = relationship("BarberSchedule", back_populates="barber")


class Service(Base):
    __tablename__ = "services"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    description   = Column(Text, nullable=True)
    duration      = Column(Integer, nullable=False)
    price         = Column(Float, nullable=False)
    is_active     = Column(Boolean, default=True)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=utcnow)

    barbershop   = relationship("Barbershop", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


class Client(Base):
    __tablename__ = "clients"
    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=True)
    email         = Column(String(150), nullable=True)
    notes         = Column(Text, nullable=True)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=utcnow)

    barbershop   = relationship("Barbershop", back_populates="clients")
    appointments = relationship("Appointment", back_populates="client")


class Appointment(Base):
    __tablename__ = "appointments"
    id            = Column(Integer, primary_key=True, index=True)
    client_id     = Column(Integer, ForeignKey("clients.id"), nullable=False)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    service_id    = Column(Integer, ForeignKey("services.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    datetime      = Column(DateTime, nullable=False)
    status        = Column(Enum(AppointmentStatus), default=AppointmentStatus.confirmed)
    notes         = Column(Text, nullable=True)
    created_at    = Column(DateTime, default=utcnow)

    barbershop = relationship("Barbershop", back_populates="appointments")
    client     = relationship("Client", back_populates="appointments")
    barber     = relationship("Barber", back_populates="appointments")
    service    = relationship("Service", back_populates="appointments")


class BarberSchedule(Base):
    """
    Horários de trabalho por dia da semana com suporte a intervalos.
    day_of_week: 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom
    Intervalos opcionais: break1 (almoço) e break2 (café da tarde)
    """
    __tablename__ = "barber_schedules"
    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)
    start_time    = Column(String(5), nullable=False)   # "08:00"
    end_time      = Column(String(5), nullable=False)   # "18:00"
    # Intervalo 1 (almoço) — opcional
    break1_start  = Column(String(5), nullable=True)    # "12:00"
    break1_end    = Column(String(5), nullable=True)    # "13:00"
    # Intervalo 2 (café da tarde) — opcional
    break2_start  = Column(String(5), nullable=True)    # "15:30"
    break2_end    = Column(String(5), nullable=True)    # "15:50"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", back_populates="schedules")
    barbershop = relationship("Barbershop", foreign_keys=[barbershop_id])
