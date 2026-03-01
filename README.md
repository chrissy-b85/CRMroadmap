# NDIS CRM

A custom-built **NDIS Plan Management CRM** for registered NDIS Plan Management providers. Manages the end-to-end lifecycle of participant plans, provider invoices, budget tracking, and compliance reporting.

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15 + shadcn/ui (TypeScript) |
| **Backend** | FastAPI (Python 3.11) |
| **Database** | PostgreSQL 15 |
| **Cache / Queue** | Redis 7 + Celery |
| **Auth** | Auth0 (MFA + RBAC) |
| **Cloud** | Google Cloud Platform (australia-southeast1) |
| **AI / OCR** | Google Document AI |
| **Accounting** | Xero API |
| **Email** | Microsoft Graph API (Outlook) |

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & Docker Compose
- See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for full setup instructions

### Run with Docker Compose

```bash
# 1. Copy environment files
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# 2. Edit the .env files with your values

# 3. Start all services
docker compose up --build
```

Services will be available at:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## Project Structure

```
CRMroadmap/
├── backend/       # FastAPI backend (Python)
├── frontend/      # Next.js + shadcn/ui (TypeScript)
├── docs/          # Project documentation
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Documentation

- [Getting Started](docs/GETTING_STARTED.md)
- [Project Roadmap](ROADMAP.md)
