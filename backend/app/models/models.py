"""
models/models.py
Definição de todas as tabelas do banco de dados usando SQLAlchemy ORM.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text, Time
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
    plan       = Column(Enum(PlanType), default=PlanType.free)
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)

    users        = relationship("User", back_populates="barbershop")
    barbers      = relationship("Barber", back_populates="barbershop")
    services     = relationship("Service", back_populates="barbershop")
    clients      = relationship("Client", back_populates="barbershop")
    appointments = relationship("Appointment", back_populates="barbershop")


class User(Base):
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100), nullable=False)
    email          = Column(String(150), unique=True, index=True, nullable=False)
    password_hash  = Column(String(200), nullable=False)
    barbershop_id  = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=utcnow)

    barbershop = relationship("Barbershop", back_populates="users")


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
    schedules    = relationship("BarberSchedule", back_populates="barber", cascade="all, delete-orphan")


class BarberSchedule(Base):
    """
    Horário de trabalho do profissional por dia da semana.
    weekday: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    weekday       = Column(Integer, nullable=False)   # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False) # "08:00"
    end_time      = Column(String(5), nullable=False) # "18:00"
    is_active     = Column(Boolean, default=True)

    barber = relationship("Barber", back_populates="schedules")


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


# ─────────────────────────────────────────────
# TABELA: Horários de trabalho dos profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Define os horários de trabalho de cada profissional por dia da semana.
    day_of_week: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)   # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False)  # "08:00"
    end_time      = Column(String(5), nullable=False)  # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Horários de trabalho dos profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Define os horários de trabalho de cada profissional por dia da semana.
    day_of_week: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)  # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False) # "08:00"
    end_time      = Column(String(5), nullable=False) # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Agenda dos Profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Horário de trabalho de cada profissional por dia da semana.
    day_of_week: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)   # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False)  # "08:00"
    end_time      = Column(String(5), nullable=False)  # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Agenda dos Profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Define o horário de trabalho de cada profissional por dia da semana.
    day_of_week: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)   # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False)  # "08:00"
    end_time      = Column(String(5), nullable=False)  # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Horários de trabalho dos profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Define os dias e horários de trabalho de cada profissional.
    Ex: Rafael trabalha Seg-Sex das 08:00 às 18:00
    weekday: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    weekday       = Column(Integer, nullable=False)   # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False) # "08:00"
    end_time      = Column(String(5), nullable=False) # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Horários de trabalho dos profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Define os horários de trabalho de cada profissional por dia da semana.
    weekday: 0=Segunda, 1=Terça, 2=Quarta, 3=Quinta, 4=Sexta, 5=Sábado, 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    weekday       = Column(Integer, nullable=False)  # 0=Seg ... 6=Dom
    start_time    = Column(String(5), nullable=False)  # "08:00"
    end_time      = Column(String(5), nullable=False)  # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")


# ─────────────────────────────────────────────
# TABELA: Agenda dos Profissionais
# ─────────────────────────────────────────────

class BarberSchedule(Base):
    """
    Horário de trabalho de cada profissional por dia da semana.
    day_of_week: 0=Segunda, 1=Terça, ..., 6=Domingo
    """
    __tablename__ = "barber_schedules"

    id            = Column(Integer, primary_key=True, index=True)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    day_of_week   = Column(Integer, nullable=False)   # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sab, 6=Dom
    start_time    = Column(String(5), nullable=False)  # "08:00"
    end_time      = Column(String(5), nullable=False)  # "18:00"
    is_active     = Column(Boolean, default=True)

    barber     = relationship("Barber", backref="schedules")
    barbershop = relationship("Barbershop")
