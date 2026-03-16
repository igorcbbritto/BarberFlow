# ✂️ BarberFlow — SaaS para Barbearias e Salões

> Sistema completo de gestão multi-tenant para barbearias e salões de beleza.  
> Backend em Python/FastAPI · Frontend em HTML/TailwindCSS · Deploy 100% gratuito

---

## 📋 Índice

- [Funcionalidades](#funcionalidades)
- [Arquitetura](#arquitetura)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Rodar Localmente](#como-rodar-localmente)
- [Deploy Gratuito](#deploy-gratuito)
- [Endpoints da API](#endpoints-da-api)
- [Multi-Tenant](#multi-tenant)
- [Próximos Passos](#próximos-passos)

---

## ✅ Funcionalidades

| Funcionalidade | Status |
|---|---|
| Cadastro de barbearia (com slug único) | ✅ |
| Login com JWT | ✅ |
| Dashboard com métricas do dia | ✅ |
| Agenda (criar, editar, cancelar) | ✅ |
| Filtro de agendamentos por data | ✅ |
| Cadastro de clientes com busca | ✅ |
| Cadastro de profissionais | ✅ |
| Cadastro de serviços com preços | ✅ |
| **Link de agendamento online para clientes** | ✅ |
| Sistema multi-tenant isolado por barbearia | ✅ |
| Hash de senha bcrypt | ✅ |
| Validação com Pydantic | ✅ |
| CI/CD com GitHub Actions | ✅ |

---

## 🏗️ Arquitetura

```
Cliente (Navegador)
        │
        ▼
  Frontend (HTML + TailwindCSS)
  Netlify / Vercel / Cloudflare Pages
        │
        │ HTTP REST (JSON)
        ▼
  Backend (FastAPI + Python)
  Render / Railway / Fly.io
        │
        │ SQLAlchemy ORM
        ▼
  Banco de Dados
  SQLite (dev) / Supabase PostgreSQL (prod)
```

### Multi-tenant
Cada barbearia é um **tenant** isolado. Todos os dados (clientes, agendamentos, profissionais, serviços) possuem `barbershop_id` que garante o isolamento completo entre barbearias.

---

## 🛠️ Tecnologias

**Backend**
- **Python 3.11** + **FastAPI** — API REST moderna e performática
- **SQLAlchemy** — ORM para mapear objetos Python ↔ banco de dados
- **Pydantic** — Validação automática de dados de entrada
- **bcrypt** — Hash seguro de senhas
- **JWT (python-jose)** — Autenticação stateless com tokens

**Frontend**
- **HTML5** + **JavaScript Vanilla** — Sem frameworks, fácil de entender
- **TailwindCSS (CDN)** — Estilização utilitária rápida
- **Google Fonts** — Tipografia: Bebas Neue + DM Sans

**Banco de Dados**
- **SQLite** — Desenvolvimento local (zero configuração)
- **Supabase PostgreSQL** — Produção gratuita (recomendado)

**Infraestrutura (tudo gratuito)**
- **Render** — Hospedagem do backend
- **Netlify** — Hospedagem do frontend
- **GitHub Actions** — CI/CD automático

---

## 📁 Estrutura do Projeto

```
barberflow/
├── .github/
│   └── workflows/
│       └── deploy.yml          ← CI/CD automático
│
├── backend/
│   ├── app/
│   │   ├── main.py             ← Entrada da aplicação FastAPI
│   │   ├── auth/
│   │   │   └── auth.py         ← JWT, bcrypt, dependências de auth
│   │   ├── database/
│   │   │   └── connection.py   ← Conexão SQLAlchemy + sessões
│   │   ├── models/
│   │   │   └── models.py       ← Tabelas do banco (ORM)
│   │   ├── routers/
│   │   │   ├── auth.py         ← POST /auth/login, /auth/register
│   │   │   ├── barbers.py      ← CRUD /barbers
│   │   │   ├── clients.py      ← CRUD /clients
│   │   │   ├── services.py     ← CRUD /services
│   │   │   ├── appointments.py ← CRUD /appointments + público
│   │   │   └── dashboard.py    ← GET /dashboard
│   │   └── schemas/
│   │       └── schemas.py      ← Validação Pydantic (entrada/saída)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
└── frontend/
    ├── index.html              ← Login / Cadastro
    ├── booking.html            ← Página pública de agendamento
    ├── js/
    │   ├── api.js              ← Funções de comunicação com a API
    │   └── layout.js           ← Sidebar + estilos compartilhados
    └── pages/
        ├── dashboard.html      ← Dashboard com métricas
        ├── agendamentos.html   ← Gerenciamento de agenda
        ├── clientes.html       ← Gerenciamento de clientes
        ├── profissionais.html  ← Gerenciamento de profissionais
        └── servicos.html       ← Gerenciamento de serviços
```

---

## 🚀 Como Rodar Localmente

### Pré-requisitos
- Python 3.11+
- Git

### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/barberflow.git
cd barberflow
```

### 2. Configure o Backend

```bash
cd backend

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env se necessário (SQLite já está configurado por padrão)
```

### 3. Inicie a API

```bash
uvicorn app.main:app --reload
```

A API estará disponível em: **http://localhost:8000**  
Documentação automática: **http://localhost:8000/docs**

### 4. Configure o Frontend

No arquivo `frontend/js/api.js`, verifique que a URL da API está correta:
```js
const API_BASE = window.API_URL || 'http://localhost:8000';
```

Abra `frontend/index.html` diretamente no navegador, ou use uma extensão como **Live Server** no VS Code.

---

## 🌐 Deploy Gratuito (Passo a Passo)

### Banco de Dados — Supabase (gratuito)

1. Crie conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em **Settings → Database**
4. Copie a **Connection String** (modo Transaction Pooler)
5. Cole no `.env` do backend:
```
DATABASE_URL=postgresql://postgres:[SENHA]@db.[PROJETO].supabase.co:5432/postgres
```

### Backend — Render (gratuito)

1. Crie conta em [render.com](https://render.com)
2. **New → Web Service**
3. Conecte seu repositório GitHub
4. Configure:
   - **Root Directory:** `backend`
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Em **Environment Variables**, adicione:
   - `DATABASE_URL` = sua URL do Supabase
   - `SECRET_KEY` = uma string aleatória longa (ex: `openssl rand -hex 32`)
6. Clique em **Create Web Service**

> ⚠️ O plano gratuito do Render "dorme" após 15 min de inatividade.  
> Para produção real, considere o plano pago ($7/mês) ou use Railway.

### Frontend — Netlify (gratuito)

1. Crie conta em [netlify.com](https://netlify.com)
2. **Add new site → Import an existing project**
3. Conecte seu GitHub
4. Configure:
   - **Base directory:** `frontend`
   - **Publish directory:** `frontend`
5. **Deploy site**

Após o deploy, atualize a URL da API no `frontend/js/api.js`:
```js
const API_BASE = 'https://seu-backend.onrender.com';
```

### CI/CD — GitHub Actions

Configure os seguintes **Secrets** no seu repositório GitHub  
(Settings → Secrets and variables → Actions):

| Secret | Descrição |
|--------|-----------|
| `RENDER_DEPLOY_HOOK_URL` | URL do webhook do Render |
| `NETLIFY_AUTH_TOKEN` | Token de acesso do Netlify |
| `NETLIFY_SITE_ID` | ID do site no Netlify |

---

## 📡 Endpoints da API

### Autenticação
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/auth/register` | Cria barbearia + usuário admin |
| POST | `/auth/login` | Login e retorna JWT |

### Profissionais
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/barbers/` | Lista profissionais |
| POST | `/barbers/` | Cadastra profissional |
| PUT | `/barbers/{id}` | Atualiza profissional |
| DELETE | `/barbers/{id}` | Desativa profissional |

### Serviços, Clientes — mesma estrutura de `/barbers/`

### Agendamentos
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/appointments/?date_filter=YYYY-MM-DD` | Lista agendamentos |
| POST | `/appointments/` | Cria agendamento |
| PUT | `/appointments/{id}` | Atualiza / muda status |
| DELETE | `/appointments/{id}` | Cancela agendamento |
| GET | `/appointments/public/{slug}/info` | Info pública da barbearia |
| POST | `/appointments/public/{slug}/book` | Cliente agenda online |

### Dashboard
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/dashboard/` | Métricas do dia |

> 💡 Acesse `/docs` no backend para a documentação interativa Swagger!

---

## 🔒 Multi-Tenant

O isolamento de dados funciona assim:

1. Cada barbearia tem um `id` único (o `tenant_id`)
2. Todo registro no banco tem `barbershop_id`
3. Cada usuário logado carrega seu `barbershop_id` no JWT
4. **Toda query filtra por `barbershop_id`** — um tenant nunca vê dados de outro

```python
# Exemplo de query multi-tenant segura:
clients = db.query(Client).filter(
    Client.barbershop_id == current_user.barbershop_id  # <- isolamento
).all()
```

---

## 🗺️ Próximos Passos

### Curto prazo (MVP+)
- [ ] Notificações por WhatsApp (API Evolution ou Twilio)
- [ ] Bloqueio de horários já ocupados no agendamento online
- [ ] Horário de funcionamento por dia da semana
- [ ] Upload de foto dos profissionais (Cloudinary)

### Médio prazo (SaaS completo)
- [ ] Sistema de planos (Free / Pro / Premium) com Stripe
- [ ] Limite de agendamentos por plano
- [ ] Relatórios financeiros por período
- [ ] App mobile com React Native

### Longo prazo (escala)
- [ ] Migração para AWS (RDS + ECS + CloudFront)
- [ ] Cache com Redis
- [ ] Fila de tarefas com Celery (envio de lembretes)
- [ ] Webhook para integrações externas

---

## 🤝 Contribuindo

1. Fork o projeto
2. Crie sua branch: `git checkout -b feature/minha-feature`
3. Commit: `git commit -m 'feat: adiciona nova funcionalidade'`
4. Push: `git push origin feature/minha-feature`
5. Abra um Pull Request

---

## 📄 Licença

MIT License — use livremente para projetos pessoais e comerciais.

---

**Feito com ✂️ e ☕ para a comunidade dev brasileira**
