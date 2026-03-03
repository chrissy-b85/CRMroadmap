# CI/CD Pipeline

## Pipeline Overview

```
Pull Request / Push to main
          │
          ▼
   ┌──────────────┐
   │   CI Workflow │  (ci.yml — runs on all PRs and pushes to main)
   │              │
   │  ┌─────────┐ │
   │  │ Backend │ │  • Ruff lint • Black format check • pytest --cov
   │  └─────────┘ │
   │  ┌──────────┐│
   │  │ Frontend ││  • ESLint • Prettier check • tsc --noEmit • Jest
   │  └──────────┘│
   └──────────────┘
          │
     (merge to main)
          │
          ▼
   ┌───────────────────┐
   │  Deploy Workflow  │  (deploy.yml — runs on push to main only)
   │                   │
   │  ┌─────────────┐  │
   │  │  Backend    │  │  Build → Push to Artifact Registry → Cloud Run
   │  └─────────────┘  │
   │  ┌─────────────┐  │
   │  │  Frontend   │  │  Build → Push to Artifact Registry → Cloud Run
   │  └─────────────┘  │
   └───────────────────┘
```

---

## CI Workflow (`.github/workflows/ci.yml`)

Triggered on every pull request and every push to `main`.

### Backend job

| Step | Tool | Command |
|------|------|---------|
| Set up Python | `actions/setup-python@v5` | Python 3.11 |
| Install deps | pip | `pip install -r requirements.txt ruff black pytest pytest-cov` |
| Lint | Ruff | `ruff check .` |
| Format check | Black | `black --check .` |
| Tests + coverage | pytest | `pytest --cov=. --cov-report=term-missing` |

### Frontend job

| Step | Tool | Command |
|------|------|---------|
| Set up Node.js | `actions/setup-node@v4` | Node.js 20 |
| Install deps | npm | `npm ci` |
| Lint | ESLint | `npx eslint .` |
| Format check | Prettier | `npx prettier --check .` |
| Type check | TypeScript | `npx tsc --noEmit` |
| Tests | Jest | `npx jest --passWithNoTests` |

---

## Deploy Workflow (`.github/workflows/deploy.yml`)

Triggered on push to `main` only.

### Authentication

Uses [Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation) via `google-github-actions/auth@v2` — no long-lived service account keys are stored as secrets.

### Backend deployment

1. Authenticate to GCP with Workload Identity Federation.
2. Build Docker image from `backend/Dockerfile`.
3. Push to `australia-southeast1-docker.pkg.dev/${GCP_PROJECT_ID}/ndis-crm/backend` (tagged with commit SHA and `latest`).
4. Deploy to Cloud Run service **`ndis-crm-backend`** in `australia-southeast1`.

### Frontend deployment

1. Authenticate to GCP with Workload Identity Federation.
2. Build Docker image from `frontend/Dockerfile`.
3. Push to `australia-southeast1-docker.pkg.dev/${GCP_PROJECT_ID}/ndis-crm/frontend` (tagged with commit SHA and `latest`).
4. Deploy to Cloud Run service **`ndis-crm-frontend`** in `australia-southeast1`.

---

## Required GitHub Secrets

Add the following secrets under **Settings → Secrets and variables → Actions** in the GitHub repository.

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | GCP project ID (e.g. `ndis-crm-prod`) |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Full resource name of the Workload Identity Provider, e.g. `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | Service account email used by GitHub Actions, e.g. `github-actions@ndis-crm-prod.iam.gserviceaccount.com` |
| `CLOUD_RUN_REGION` | GCP region for Cloud Run services (e.g. `australia-southeast1`) |

---

## Setting Up Workload Identity Federation on GCP

Run the following commands with the `gcloud` CLI (replace placeholder values as needed).

```bash
PROJECT_ID="ndis-crm-prod"
GITHUB_ORG="chrissy-b85"
GITHUB_REPO="CRMroadmap"
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SA_NAME="github-actions"

# 1. Create a Workload Identity Pool
gcloud iam workload-identity-pools create "$POOL_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# 2. Create a provider in the pool
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# 3. Create a Service Account
gcloud iam service-accounts create "$SA_NAME" \
  --project="$PROJECT_ID" \
  --display-name="GitHub Actions CI/CD"

# 4. Grant the SA permission to deploy to Cloud Run and push to Artifact Registry
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 5. Allow the GitHub repo to impersonate the SA via the pool
gcloud iam service-accounts add-iam-policy-binding \
  "${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="$PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/${POOL_ID}/attribute.repository/${GITHUB_ORG}/${GITHUB_REPO}"
```

After running the above commands, retrieve the provider resource name for the `GCP_WORKLOAD_IDENTITY_PROVIDER` secret:

```bash
gcloud iam workload-identity-pools providers describe "$PROVIDER_ID" \
  --project="$PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="$POOL_ID" \
  --format="value(name)"
```

---

## Adding Secrets to GitHub Repository Settings

1. Go to your repository on GitHub.
2. Click **Settings** → **Secrets and variables** → **Actions**.
3. Click **New repository secret** for each secret listed in the table above.
4. Paste the value and click **Add secret**.

---

## Deployment Rollback Instructions

Each deployment tags the Docker image with the Git commit SHA. To roll back to a previous revision:

### Option 1 — Redeploy a previous Cloud Run revision

```bash
# List revisions
gcloud run revisions list --service ndis-crm-backend --region australia-southeast1
gcloud run revisions list --service ndis-crm-frontend --region australia-southeast1

# Route 100% traffic to a specific revision
gcloud run services update-traffic ndis-crm-backend \
  --region australia-southeast1 \
  --to-revisions <REVISION_NAME>=100

gcloud run services update-traffic ndis-crm-frontend \
  --region australia-southeast1 \
  --to-revisions <REVISION_NAME>=100
```

### Option 2 — Redeploy a previous image by commit SHA

```bash
COMMIT_SHA="<previous-sha>"

gcloud run deploy ndis-crm-backend \
  --region australia-southeast1 \
  --image australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/backend:${COMMIT_SHA}

gcloud run deploy ndis-crm-frontend \
  --region australia-southeast1 \
  --image australia-southeast1-docker.pkg.dev/ndis-crm-prod/ndis-crm/frontend:${COMMIT_SHA}
```
