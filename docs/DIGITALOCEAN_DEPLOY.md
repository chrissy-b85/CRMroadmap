# DigitalOcean Deployment Guide

This guide walks through deploying the NDIS CRM application to DigitalOcean, targeting the **`syd1` (Sydney)** region as a full alternative to the existing GCP infrastructure.

---

## Prerequisites

- [doctl](https://docs.digitalocean.com/reference/doctl/how-to/install/) — DigitalOcean CLI
- [Terraform](https://developer.hashicorp.com/terraform/install) ≥ 1.5
- [Docker](https://docs.docker.com/get-docker/) (for building images)
- A DigitalOcean account with API access
- A GCP project — still required for **Document AI** (invoice OCR). All other GCP services are replaced by DigitalOcean equivalents.

---

## Architecture overview

| Service | GCP | DigitalOcean |
|---------|-----|--------------|
| Container hosting | Cloud Run | App Platform |
| Container registry | Artifact Registry | Container Registry |
| PostgreSQL | Cloud SQL | Managed PostgreSQL |
| Redis / Celery broker | Memorystore | Managed Redis |
| File storage | Cloud Storage (GCS) | Spaces (S3-compatible) |
| Invoice OCR | **Document AI** | **Document AI (GCP — unchanged)** |

> **Note:** Google Cloud Document AI is the only GCP service still used after migrating to DigitalOcean. You must keep `GCP_PROJECT_ID`, `DOCUMENT_AI_PROCESSOR_ID`, and `GCP_SERVICE_ACCOUNT_KEY` configured.

---

## Step 1: Create infrastructure with Terraform

```bash
# Install Terraform if needed
brew install terraform  # macOS; see https://developer.hashicorp.com/terraform/install for other platforms

# Export your DigitalOcean API token
export TF_VAR_do_token="<your-digitalocean-api-token>"

# Provision all resources
cd infra/do
terraform init
terraform apply
```

Note the outputs after `terraform apply`:

| Output | Description |
|--------|-------------|
| `postgres_uri` | PostgreSQL connection string (sensitive) |
| `redis_uri` | Redis connection string (sensitive) |
| `registry_endpoint` | Container registry endpoint |
| `spaces_bucket_name` | Spaces bucket name (`ndis-crm-files`) |
| `spaces_endpoint` | `https://syd1.digitaloceanspaces.com` |

Retrieve sensitive outputs with:

```bash
terraform output -raw postgres_uri
terraform output -raw redis_uri
```

---

## Step 2: Create Container Registry

If the registry was not created by Terraform (or you prefer the CLI):

```bash
doctl registry create ndis-crm
```

---

## Step 3: Configure App Platform secrets

The app spec at `infra/do/app.yaml` defines all services. Before the first deploy, set the following secrets in the DigitalOcean dashboard under **Apps → <your app> → Settings → App-Level Environment Variables**, or pass them with `doctl`:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL URI from Terraform output |
| `REDIS_URL` | Redis URI from Terraform output |
| `AUTH0_DOMAIN` | Auth0 tenant domain (e.g. `your-tenant.au.auth0.com`) |
| `AUTH0_AUDIENCE` | Auth0 API audience |
| `AUTH0_CLIENT_SECRET` | Auth0 M2M client secret |
| `DO_SPACES_KEY` | Spaces access key ID |
| `DO_SPACES_SECRET` | Spaces secret access key |
| `GCP_PROJECT_ID` | GCP project for Document AI |
| `DOCUMENT_AI_PROCESSOR_ID` | Document AI processor ID |
| `GCP_SERVICE_ACCOUNT_KEY` | JSON key for the GCP service account (base64 or file mount) |
| `GRAPH_TENANT_ID` | Microsoft 365 tenant ID |
| `GRAPH_CLIENT_ID` | Microsoft Graph app client ID |
| `GRAPH_CLIENT_SECRET` | Microsoft Graph app client secret |
| `GRAPH_SHARED_MAILBOX` | Shared mailbox address for invoice ingestion |
| `GRAPH_FROM_MAILBOX` | From address for outbound notifications |
| `XERO_CLIENT_ID` | Xero app client ID |
| `XERO_CLIENT_SECRET` | Xero app client secret |
| `XERO_REDIRECT_URI` | Xero OAuth redirect URI |
| `XERO_WEBHOOK_KEY` | Xero webhook signing key |
| `VAPID_PUBLIC_KEY` | Web Push VAPID public key |
| `VAPID_PRIVATE_KEY` | Web Push VAPID private key |
| `CELERY_BROKER_URL` | Same as `REDIS_URL` |
| `NEXT_PUBLIC_API_URL` | Backend URL as seen by the browser |
| `AUTH0_SECRET` | Long random secret for Next.js Auth0 SDK |
| `AUTH0_BASE_URL` | Frontend base URL (e.g. `https://your-app.ondigitalocean.app`) |
| `AUTH0_ISSUER_BASE_URL` | Auth0 issuer URL (`https://<AUTH0_DOMAIN>`) |
| `AUTH0_CLIENT_ID` | Auth0 SPA client ID |
| `NEXT_PUBLIC_VAPID_PUBLIC_KEY` | Same as `VAPID_PUBLIC_KEY` |

### Create the app for the first time

```bash
doctl apps create --spec infra/do/app.yaml
```

Set secrets via the dashboard, then note the **App ID** shown in `doctl apps list` — you will need it for GitHub Actions.

---

## Step 4: Build and push images manually (first deploy)

```bash
# Authenticate with the registry
doctl registry login

REGISTRY="registry.digitalocean.com/<your-registry-name>"
SHA=$(git rev-parse --short HEAD)

# Backend
docker build -f backend/Dockerfile.prod -t $REGISTRY/ndis-crm-backend:$SHA backend
docker push $REGISTRY/ndis-crm-backend:$SHA
docker tag  $REGISTRY/ndis-crm-backend:$SHA $REGISTRY/ndis-crm-backend:latest
docker push $REGISTRY/ndis-crm-backend:latest

# Frontend
docker build -f frontend/Dockerfile.prod -t $REGISTRY/ndis-crm-frontend:$SHA frontend
docker push $REGISTRY/ndis-crm-frontend:$SHA
docker tag  $REGISTRY/ndis-crm-frontend:$SHA $REGISTRY/ndis-crm-frontend:latest
docker push $REGISTRY/ndis-crm-frontend:latest
```

---

## Step 5: Run database migrations

```bash
# Retrieve the connection URI
DB_URI=$(cd infra/do && terraform output -raw postgres_uri)

# Run Alembic migrations from the backend directory
DATABASE_URL="$DB_URI" alembic upgrade head
```

Alternatively, using `doctl`:

```bash
DB_URI=$(doctl databases connection ndis-crm-postgres --no-headers -o uri)
DATABASE_URL="$DB_URI" alembic upgrade head
```

---

## Step 6: Set up GitHub Actions

Add the following secrets to your GitHub repository (**Settings → Secrets and variables → Actions**):

| Secret | Value |
|--------|-------|
| `DIGITALOCEAN_ACCESS_TOKEN` | Your DigitalOcean API token |
| `DO_REGISTRY_NAME` | Container registry name (e.g. `ndis-crm`) |
| `DO_APP_ID` | App Platform app ID from `doctl apps list` |

Once set, every push to `main` will automatically build and deploy both images via `.github/workflows/deploy-do.yml`.

---

## Step 7: Configure Auth0 callback URLs

In the Auth0 dashboard, update the **Allowed Callback URLs** and **Allowed Logout URLs** for your application to include the App Platform URL:

```
https://<your-app-name>.ondigitalocean.app/api/auth/callback
https://<your-app-name>.ondigitalocean.app
```

---

## Step 8: Configure Xero redirect URI

In the [Xero developer portal](https://developer.xero.com/), update the OAuth 2.0 redirect URI for your app to:

```
https://<your-app-url>/xero/callback
```

---

## Cost estimate (approximate, AUD/month)

| Resource | Size | Est. cost |
|----------|------|-----------|
| App Platform — backend (professional-xs) | 1 instance | ~$18 |
| App Platform — celery-worker (professional-xs) | 1 instance | ~$18 |
| App Platform — celery-beat (professional-xs) | 1 instance | ~$18 |
| App Platform — frontend (professional-xs) | 1 instance | ~$18 |
| Managed PostgreSQL (`db-s-1vcpu-1gb`) | 1 node | ~$21 |
| Managed Redis (`db-s-1vcpu-1gb`) | 1 node | ~$21 |
| Container Registry (basic tier) | — | ~$7 |
| Spaces storage | First 250 GB + transfer | ~$7+ |
| **Total** | | **~$128+/month** |

Prices are indicative and may vary. See [DigitalOcean pricing](https://www.digitalocean.com/pricing) for current rates.

---

## GCP services still required

Even after migrating to DigitalOcean, you must retain the following GCP configuration:

| Variable | Purpose |
|----------|---------|
| `GCP_PROJECT_ID` | GCP project for Document AI |
| `DOCUMENT_AI_PROCESSOR_ID` | Invoice OCR processor |
| `GCP_SERVICE_ACCOUNT_KEY` | Service account credentials for Document AI API calls |

All other GCP services (Cloud Storage, Cloud Run, Artifact Registry, Memorystore) are replaced by their DigitalOcean equivalents described in this guide.
