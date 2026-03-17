"""
routers/demo.py
Endpoint para criar dados de demonstração via navegador.
Acesse: https://barberflow-api-0o7n.onrender.com/demo/seed
"""

from fastapi import APIRouter
from app.database.connection import SessionLocal, Base, engine
from app.models.models import (
    Barbershop, User, Barber, Service, Client,
    Appointment, AppointmentStatus, PlanType
)
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext

router = APIRouter(prefix="/demo", tags=["Demonstração"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@router.post("/seed")
def seed_demo_data():
    """
    Cria barbearia de demonstração completa.
    Login: demo@barberflow.com / demo123
    """
    db = SessionLocal()
    try:
        # Remove demo anterior se existir
        demo_shop = db.query(Barbershop).filter(Barbershop.slug == "barbearia-demo").first()
        if demo_shop:
            db.query(Appointment).filter(Appointment.barbershop_id == demo_shop.id).delete()
            db.query(Client).filter(Client.barbershop_id == demo_shop.id).delete()
            db.query(Service).filter(Service.barbershop_id == demo_shop.id).delete()
            db.query(Barber).filter(Barber.barbershop_id == demo_shop.id).delete()
            db.query(User).filter(User.barbershop_id == demo_shop.id).delete()
            db.delete(demo_shop)
            db.commit()

        # Barbearia
        barbershop = Barbershop(
            name="Barbearia Estilo & Navalha",
            slug="barbearia-demo",
            phone="(21) 99999-1234",
            address="Rua das Flores, 123 — Centro, Rio de Janeiro/RJ",
            plan=PlanType.free,
            is_active=True,
        )
        db.add(barbershop)
        db.flush()

        # Usuário demo
        user = User(
            name="Carlos Dono",
            email="demo@barberflow.com",
            password_hash=pwd_context.hash("demo123"),
            barbershop_id=barbershop.id,
            is_active=True,
        )
        db.add(user)
        db.flush()

        # Profissionais
        barbers_data = [
            {"name": "Rafael Oliveira",  "phone": "(21) 98888-1111", "specialty": "Corte masculino, Degradê"},
            {"name": "Lucas Mendes",     "phone": "(21) 98888-2222", "specialty": "Barba, Bigode, Sobrancelha"},
            {"name": "Bruno Costa",      "phone": "(21) 98888-3333", "specialty": "Corte infantil, Platinado"},
            {"name": "Thiago Ferreira",  "phone": "(21) 98888-4444", "specialty": "Corte feminino, Coloração"},
        ]
        barbers = []
        for b in barbers_data:
            barber = Barber(barbershop_id=barbershop.id, **b)
            db.add(barber)
            barbers.append(barber)
        db.flush()

        # Serviços
        services_data = [
            {"name": "Corte Masculino",       "description": "Corte completo com acabamento",          "duration": 30,  "price": 35.0},
            {"name": "Corte + Barba",         "description": "Corte masculino com barba completa",      "duration": 60,  "price": 60.0},
            {"name": "Barba Completa",        "description": "Barba com toalha quente e navalha",       "duration": 30,  "price": 30.0},
            {"name": "Degradê",               "description": "Degradê com máquina e tesoura",           "duration": 45,  "price": 45.0},
            {"name": "Corte Infantil",        "description": "Corte para crianças até 10 anos",         "duration": 25,  "price": 25.0},
            {"name": "Platinado",             "description": "Descoloração com produtos profissionais", "duration": 90,  "price": 120.0},
            {"name": "Sobrancelha",           "description": "Design de sobrancelha masculina",         "duration": 15,  "price": 15.0},
            {"name": "Hidratação",            "description": "Hidratação capilar com máscara",          "duration": 30,  "price": 40.0},
        ]
        services = []
        for s in services_data:
            service = Service(barbershop_id=barbershop.id, **s)
            db.add(service)
            services.append(service)
        db.flush()

        # Clientes
        clients_data = [
            {"name": "João Silva",       "phone": "(21) 97777-0001", "email": "joao@email.com",    "notes": "Prefere corte curto nas laterais"},
            {"name": "Pedro Alves",      "phone": "(21) 97777-0002", "email": "pedro@email.com",   "notes": "Cliente VIP - sempre pontual"},
            {"name": "Marcos Souza",     "phone": "(21) 97777-0003", "email": None,                "notes": None},
            {"name": "André Lima",       "phone": "(21) 97777-0004", "email": "andre@email.com",   "notes": "Alérgico a alguns produtos"},
            {"name": "Felipe Rocha",     "phone": "(21) 97777-0005", "email": None,                "notes": "Gosta de degradê baixo"},
            {"name": "Gabriel Martins",  "phone": "(21) 97777-0006", "email": "gabriel@email.com", "notes": None},
            {"name": "Ricardo Nunes",    "phone": "(21) 97777-0007", "email": None,                "notes": "Corte toda semana"},
            {"name": "Diego Carvalho",   "phone": "(21) 97777-0008", "email": "diego@email.com",   "notes": None},
            {"name": "Lucas Barbosa",    "phone": "(21) 97777-0009", "email": None,                "notes": "Traz o filho junto"},
            {"name": "Mateus Gomes",     "phone": "(21) 97777-0010", "email": "mateus@email.com",  "notes": None},
            {"name": "Henrique Castro",  "phone": "(21) 97777-0011", "email": None,                "notes": "Prefere o Rafael"},
            {"name": "Bruno Teixeira",   "phone": "(21) 97777-0012", "email": "bteixeira@email.com","notes": None},
        ]
        clients = []
        for c in clients_data:
            client = Client(barbershop_id=barbershop.id, **c)
            db.add(client)
            clients.append(client)
        db.flush()

        # Agendamentos — UTC-3 Brasília
        now_utc   = datetime.now(timezone.utc).replace(tzinfo=None)
        today_utc = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        offset    = timedelta(hours=3)

        def dt(day_delta, hour, minute):
            local = today_utc + timedelta(days=day_delta, hours=hour, minutes=minute)
            return local + offset

        appts = [
            # Ontem — concluídos
            (0, 0,  -1,  9,  0, AppointmentStatus.completed),
            (1, 1,  -1,  9, 30, AppointmentStatus.completed),
            (2, 2,  -1, 10,  0, AppointmentStatus.completed),
            (3, 3,  -1, 10, 30, AppointmentStatus.completed),
            (4, 0,  -1, 11,  0, AppointmentStatus.completed),
            (5, 1,  -1, 14,  0, AppointmentStatus.completed),
            (6, 2,  -1, 14, 30, AppointmentStatus.completed),
            (7, 3,  -1, 15,  0, AppointmentStatus.completed),
            (8, 0,  -1, 15, 30, AppointmentStatus.cancelled),
            (9, 1,  -1, 16,  0, AppointmentStatus.completed),
            # Hoje
            (0,  0,  0,  9,  0, AppointmentStatus.confirmed),
            (1,  1,  0,  9, 30, AppointmentStatus.confirmed),
            (2,  2,  0, 10,  0, AppointmentStatus.confirmed),
            (3,  3,  0, 10, 30, AppointmentStatus.confirmed),
            (4,  0,  0, 11,  0, AppointmentStatus.confirmed),
            (5,  1,  0, 11, 30, AppointmentStatus.pending),
            (6,  2,  0, 14,  0, AppointmentStatus.confirmed),
            (7,  3,  0, 14, 30, AppointmentStatus.confirmed),
            (8,  0,  0, 15,  0, AppointmentStatus.pending),
            (9,  1,  0, 15, 30, AppointmentStatus.confirmed),
            (10, 2,  0, 16,  0, AppointmentStatus.confirmed),
            (11, 3,  0, 17,  0, AppointmentStatus.confirmed),
            # Amanhã
            (3,  0,  1,  9,  0, AppointmentStatus.confirmed),
            (4,  1,  1,  9, 30, AppointmentStatus.confirmed),
            (5,  2,  1, 10,  0, AppointmentStatus.confirmed),
            (6,  3,  1, 10, 30, AppointmentStatus.confirmed),
            (7,  0,  1, 11,  0, AppointmentStatus.confirmed),
            (8,  1,  1, 14,  0, AppointmentStatus.confirmed),
            (9,  2,  1, 15,  0, AppointmentStatus.pending),
            (10, 3,  1, 16,  0, AppointmentStatus.confirmed),
            # Próxima semana
            (0,  0,  3, 10,  0, AppointmentStatus.confirmed),
            (2,  1,  3, 11,  0, AppointmentStatus.confirmed),
            (4,  2,  5,  9,  0, AppointmentStatus.confirmed),
            (6,  3,  5, 14,  0, AppointmentStatus.confirmed),
            (1,  0,  7, 10,  0, AppointmentStatus.confirmed),
        ]

        # (client_idx, barber_idx, day, hour, min, status)
        service_cycle = [0, 1, 2, 3, 4, 5, 6, 7]
        for i, (ci, bi, day, hour, minute, status) in enumerate(appts):
            appointment = Appointment(
                client_id=clients[ci % len(clients)].id,
                barber_id=barbers[bi % len(barbers)].id,
                service_id=services[i % len(services)].id,
                barbershop_id=barbershop.id,
                datetime=dt(day, hour, minute),
                status=status,
            )
            db.add(appointment)

        db.commit()

        return {
            "success": True,
            "message": "Dados de demonstração criados com sucesso!",
            "login": {
                "email": "demo@barberflow.com",
                "senha": "demo123",
                "url": "https://barberflow-app.pages.dev"
            },
            "resumo": {
                "barbearia": barbershop.name,
                "slug": barbershop.slug,
                "profissionais": len(barbers),
                "servicos": len(services),
                "clientes": len(clients),
                "agendamentos": len(appts),
            }
        }

    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()
