# Auth0 Setup Guide

This document describes the full Auth0 configuration for the NDIS CRM, covering both the **Staff Portal** (Regular Web App) and the **Participant PWA** (Single Page App), RBAC, MFA, Terraform automation, and local development setup.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                       Auth0 Tenant                      │
│                                                         │
│  ┌──────────────────────┐  ┌────────────────────────┐  │
│  │  Staff Portal App    │  │  Participant PWA App   │  │
│  │  (Regular Web App)   │  │  (SPA)                 │  │
│  └──────────┬───────────┘  └───────────┬────────────┘  │
│             │                          │               │
│  ┌──────────▼──────────────────────────▼────────────┐  │
│  │              NDIS CRM API Resource Server        │  │
│  │         audience: https://api.ndis-crm.com       │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Roles: Admin | Coordinator | Viewer                    │
│  MFA:   Always enforced for Staff Portal                │
└─────────────────────────────────────────────────────────┘
```

### Staff Portal Login Flow

```
User → Staff Portal (Next.js)
     → GET /api/auth/login
     → Redirect to Auth0 Universal Login (+ MFA challenge)
     → Auth0 issues access token (RS256, audience: https://api.ndis-crm.com)
     → Callback to /api/auth/callback
     → Session stored server-side (Auth0 SDK)
     → Access token sent to FastAPI backend as Bearer token
     → Backend verifies token via JWKS endpoint
```

### Participant PWA Login Flow

```
User → Participant PWA (SPA / PWA)
     → Auth0 Universal Login (no MFA requirement)
     → Auth0 issues access token (RS256, audience: https://api.ndis-crm.com)
     → Token stored in memory (no localStorage for security)
     → API calls include Authorization: Bearer <token>
     → Backend verifies token via JWKS endpoint
```

---

## Prerequisites

- An [Auth0](https://auth0.com) account with a tenant created
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- Access to the Auth0 Management API (M2M application with `Management API` scopes)

---

## Step-by-Step Auth0 Tenant Setup

### 1. Create a Machine-to-Machine Application for Terraform

1. In the Auth0 Dashboard → **Applications** → **Create Application**
2. Choose **Machine to Machine Applications**
3. Select **Auth0 Management API** and grant all relevant scopes (at minimum: `read:clients`, `create:clients`, `update:clients`, `delete:clients`, `read:resource_servers`, `create:resource_servers`, `read:roles`, `create:roles`, `update:roles`)
4. Copy the **Client ID** and **Client Secret** — these are your Terraform credentials

### 2. Apply Terraform Configuration

```bash
cd infra/auth0
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your real values
terraform init
terraform plan
terraform apply
```

Note the outputs:
- `staff_portal_client_id`
- `participant_pwa_client_id`
- `api_audience`

### 3. Configure Auth0 Actions (Roles in Token)

To include RBAC roles in the access token, add an Auth0 Action:

1. Auth0 Dashboard → **Actions** → **Flows** → **Login**
2. Add a **Custom Action** with the following code:

```javascript
exports.onExecutePostLogin = async (event, api) => {
  const namespace = 'https://ndis-crm.com/';
  if (event.authorization) {
    api.accessToken.setCustomClaim(
      `${namespace}roles`,
      event.authorization.roles
    );
    api.idToken.setCustomClaim(
      `${namespace}roles`,
      event.authorization.roles
    );
  }
};
```

---

## RBAC Roles and Permissions

| Role        | Permissions                                                                                   |
|-------------|-----------------------------------------------------------------------------------------------|
| Admin       | `read:participants`, `write:participants`, `read:invoices`, `write:invoices`, `approve:invoices`, `read:reports`, `manage:users` |
| Coordinator | `read:participants`, `write:participants`, `read:invoices`, `write:invoices`, `approve:invoices`, `read:reports` |
| Viewer      | `read:participants`, `read:invoices`, `read:reports`                                         |

Roles are assigned to users in the Auth0 Dashboard → **User Management** → select user → **Roles**.

---

## MFA Setup for Staff

MFA is enforced for **all** users via the `always` policy configured in `infra/auth0/mfa.tf`.

Supported factors:
- **OTP** (authenticator app — Google Authenticator, Authy, etc.)

Staff members will be prompted to enrol in MFA on their first login. The supported enrolment flow is handled by Auth0 Universal Login.

---

## Backend Integration

### Environment Variables (`backend/.env`)

```
AUTH0_DOMAIN=your-tenant.auth0.com
AUTH0_AUDIENCE=https://api.ndis-crm.com
AUTH0_CLIENT_SECRET=
```

### Protecting FastAPI Endpoints

```python
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user, require_role

router = APIRouter()

# Any authenticated user
@router.get("/participants")
async def list_participants(user=Depends(get_current_user)):
    ...

# Admin role required
@router.delete("/users/{user_id}", dependencies=[Depends(require_role("Admin"))])
async def delete_user(user_id: str):
    ...
```

---

## Frontend Integration

### Environment Variables (`frontend/.env.local`)

```
AUTH0_SECRET=<run: openssl rand -hex 32>
AUTH0_BASE_URL=http://localhost:3000
AUTH0_ISSUER_BASE_URL=https://your-tenant.auth0.com
AUTH0_CLIENT_ID=<staff_portal_client_id from Terraform output>
AUTH0_CLIENT_SECRET=<staff portal client secret from Auth0 Dashboard>
NEXT_PUBLIC_AUTH0_AUDIENCE=https://api.ndis-crm.com
```

### Route Protection

`frontend/middleware.ts` automatically redirects unauthenticated users away from `/dashboard` and `/admin` routes to the Auth0 login page.

### Using the Session in Pages

```typescript
import { getSession } from "@auth0/nextjs-auth0";

export default async function DashboardPage() {
  const session = await getSession();
  return <div>Welcome, {session?.user.name}</div>;
}
```

---

## Local Development Setup

1. Copy example env files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

2. Fill in the Auth0 values from your tenant and Terraform outputs.

3. In Auth0 Dashboard, ensure `http://localhost:3000/api/auth/callback` and `http://localhost:3000` are listed under your Staff Portal application's **Allowed Callback URLs** and **Allowed Logout URLs**.

4. Start services:

```bash
docker-compose up
```

5. Navigate to `http://localhost:3000` — you will be redirected to Auth0 login on protected routes.
