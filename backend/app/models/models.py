"""
models/models.py
Definição de todas as tabelas do banco de dados usando SQLAlchemy ORM.
Cada classe = uma tabela. Cada atributo = uma coluna.

MULTI-TENANT: Todos os dados são isolados por barbershop_id (tenant_id).
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
import enum

from app.database.connection import Base


# ─────────────────────────────────────────────
# ENUMS (valores fixos permitidos)
# ─────────────────────────────────────────────

class AppointmentStatus(str, enum.Enum):
    """Status possíveis de um agendamento"""
    pending   = "pending"    # Aguardando confirmação
    confirmed = "confirmed"  # Confirmado
    completed = "completed"  # Atendido
    cancelled = "cancelled"  # Cancelado


class PlanType(str, enum.Enum):
    """Planos do SaaS (preparado para futuro)"""
    free    = "free"    # Gratuito - com limites
    basic   = "basic"   # Pago básico
    premium = "premium" # Pago premium


# ─────────────────────────────────────────────
# TABELA: Barbearias (Tenants)
# ─────────────────────────────────────────────

class Barbershop(Base):
    """
    Representa cada barbearia/salão cadastrado no sistema.
    É o 'tenant' - cada barbearia vê apenas seus próprios dados.
    """
    __tablename__ = "barbershops"

    id         = Column(Integer, primary_key=True, index=True)
    name       = Column(String(100), nullable=False)           # Nome da barbearia
    slug       = Column(String(50), unique=True, index=True)   # URL amigável: joaobarber
    phone      = Column(String(20), nullable=True)
    address    = Column(String(200), nullable=True)
    plan       = Column(Enum(PlanType), default=PlanType.free) # Plano atual
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos (1 barbearia -> muitos de cada)
    users        = relationship("User", back_populates="barbershop")
    barbers      = relationship("Barber", back_populates="barbershop")
    services     = relationship("Service", back_populates="barbershop")
    clients      = relationship("Client", back_populates="barbershop")
    appointments = relationship("Appointment", back_populates="barbershop")


# ─────────────────────────────────────────────
# TABELA: Usuários (donos/admins da barbearia)
# ─────────────────────────────────────────────

class User(Base):
    """
    Usuários que fazem login no sistema (donos e gerentes).
    Cada usuário pertence a UMA barbearia.
    """
    __tablename__ = "users"

    id             = Column(Integer, primary_key=True, index=True)
    name           = Column(String(100), nullable=False)
    email          = Column(String(150), unique=True, index=True, nullable=False)
    password_hash  = Column(String(200), nullable=False)      # Nunca salvar senha em texto!
    barbershop_id  = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    is_active      = Column(Boolean, default=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    # Relacionamento com a barbearia
    barbershop = relationship("Barbershop", back_populates="users")


# ─────────────────────────────────────────────
# TABELA: Barbeiros/Profissionais
# ─────────────────────────────────────────────

class Barber(Base):
    """
    Profissionais que realizam os serviços.
    Podem ser diferentes dos usuários do sistema.
    """
    __tablename__ = "barbers"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=True)
    specialty     = Column(String(100), nullable=True)   # Ex: "Corte masculino, Barba"
    is_active     = Column(Boolean, default=True)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    barbershop   = relationship("Barbershop", back_populates="barbers")
    appointments = relationship("Appointment", back_populates="barber")


# ─────────────────────────────────────────────
# TABELA: Serviços
# ─────────────────────────────────────────────

class Service(Base):
    """
    Serviços oferecidos pela barbearia.
    Ex: Corte R$35 - 30min, Barba R$25 - 20min
    """
    __tablename__ = "services"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    description   = Column(Text, nullable=True)
    duration      = Column(Integer, nullable=False)    # Duração em minutos
    price         = Column(Float, nullable=False)       # Preço em reais
    is_active     = Column(Boolean, default=True)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    barbershop   = relationship("Barbershop", back_populates="services")
    appointments = relationship("Appointment", back_populates="service")


# ─────────────────────────────────────────────
# TABELA: Clientes
# ─────────────────────────────────────────────

class Client(Base):
    """
    Clientes da barbearia.
    Isolados por barbershop_id - cada barbearia tem sua própria lista.
    """
    __tablename__ = "clients"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String(100), nullable=False)
    phone         = Column(String(20), nullable=True)
    email         = Column(String(150), nullable=True)
    notes         = Column(Text, nullable=True)          # Observações sobre o cliente
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos
    barbershop   = relationship("Barbershop", back_populates="clients")
    appointments = relationship("Appointment", back_populates="client")


# ─────────────────────────────────────────────
# TABELA: Agendamentos
# ─────────────────────────────────────────────

class Appointment(Base):
    """
    Agendamentos - coração do sistema.
    Liga cliente + barbeiro + serviço + horário.
    """
    __tablename__ = "appointments"

    id            = Column(Integer, primary_key=True, index=True)
    client_id     = Column(Integer, ForeignKey("clients.id"), nullable=False)
    barber_id     = Column(Integer, ForeignKey("barbers.id"), nullable=False)
    service_id    = Column(Integer, ForeignKey("services.id"), nullable=False)
    barbershop_id = Column(Integer, ForeignKey("barbershops.id"), nullable=False)
    datetime      = Column(DateTime, nullable=False)              # Data e hora do agendamento
    status        = Column(Enum(AppointmentStatus), default=AppointmentStatus.confirmed)
    notes         = Column(Text, nullable=True)                   # Observações
    created_at    = Column(DateTime, default=datetime.utcnow)

    # Relacionamentos (para fazer JOIN automático)
    barbershop = relationship("Barbershop", back_populates="appointments")
    client     = relationship("Client", back_populates="appointments")
    barber     = relationship("Barber", back_populates="appointments")
    service    = relationship("Service", back_populates="appointments")
