# Getting Started

## Prerequisites

Ensure you have the following installed before setting up the project:

- [Docker](https://docs.docker.com/get-docker/) (v24+) & Docker Compose (v2+)
- [Node.js](https://nodejs.org/) v20 (for running the frontend locally without Docker)
- [Python](https://www.python.org/downloads/) 3.11 (for running the backend locally without Docker)
- [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (for GCP resource access)
- An [Auth0](https://auth0.com/) account with a configured tenant

---

## Local Development Setup (Docker Compose)

This is the recommended way to run all services together.

### 1. Clone the repository

```bash
git clone https://github.com/chrissy-b85/CRMroadmap.git
cd CRMroadmap
```

### 2. Configure environment variables

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit each file and fill in the required values (see [Environment Variables](#environment-variables) below).

### 3. Start all services

```bash
docker compose up --build
```

This starts:

| Service | URL |
|---|---|
| Frontend (Next.js) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Verify the backend health endpoint

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok"}
```

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `REDIS_URL` | Redis connection string |
| `AUTH0_DOMAIN` | Auth0 tenant domain |
| `AUTH0_AUDIENCE` | Auth0 API audience identifier |
| `GCP_PROJECT_ID` | Google Cloud project ID |
| `GCP_SERVICE_ACCOUNT_KEY` | Path to GCP service account JSON key file |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_API_URL` | Backend API base URL |
| `NEXT_PUBLIC_AUTH0_DOMAIN` | Auth0 tenant domain |
| `NEXT_PUBLIC_AUTH0_CLIENT_ID` | Auth0 SPA client ID |

---

## Running Services Individually

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # Edit .env with your values
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.example .env.local  # Edit .env.local with your values
npm run dev
```

---

## Auth0 Setup

1. Create an Auth0 account at https://auth0.com
2. Create a new **Regular Web Application** for the backend API
3. Create a new **Single Page Application** for the frontend
4. Set `AUTH0_DOMAIN` to your tenant domain (e.g. `your-tenant.au.auth0.com`)
5. Set `AUTH0_AUDIENCE` to the API identifier you define in Auth0
6. Set `NEXT_PUBLIC_AUTH0_CLIENT_ID` to your SPA client ID
7. Configure allowed callback URLs, logout URLs, and CORS origins in Auth0 dashboard

> **Note:** Auth0 configuration is a placeholder in Phase 1. MFA and RBAC roles (Admin, Coordinator, Viewer) will be fully configured during Sprint 1.

---

## GCP Setup

For full infrastructure setup, see [GCP Infrastructure](GCP_INFRASTRUCTURE.md).

Quick steps:

1. Install the [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
2. Authenticate: `gcloud auth login`
3. Set your project: `gcloud config set project ndis-crm-prod`
4. Run the bootstrap script: `./infra/scripts/bootstrap.sh`
5. Deploy infrastructure: `cd infra/terraform && terraform init && terraform apply`
6. Populate Secret Manager secrets (see [GCP Infrastructure — Secret Manager](GCP_INFRASTRUCTURE.md#5-secret-manager))

> **Note:** The local Docker Compose setup uses a local PostgreSQL container instead of Cloud SQL. Cloud infrastructure is used for production deployments only.
