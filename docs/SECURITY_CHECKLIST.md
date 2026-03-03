# Security Checklist — NDIS CRM

> **Sprint:** UAT / QA / Bugfix  
> **Reviewed by:** ___________________  
> **Date:** ___________________

Mark each item **Pass ✅ / Fail ❌ / N/A** and add notes where relevant.

---

## 1. Auth0 Configuration

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-01 | MFA enforced for all staff (Coordinator, Admin) roles | | Verify in Auth0 Dashboard → Security → MFA |
| SEC-02 | Token expiry set to ≤ 1 hour for access tokens | | Default is 86400 s; reduce for production |
| SEC-03 | Refresh token rotation enabled | | Prevents refresh token reuse attacks |
| SEC-04 | Allowed callback URLs restricted to production domain only | | Remove localhost entries before go-live |
| SEC-05 | Allowed logout URLs restricted to production domain | | |
| SEC-06 | Allowed web origins restricted to production domain | | |
| SEC-07 | Brute-force protection enabled | | Auth0 Attack Protection → Brute Force |
| SEC-08 | Anomalous IP / bot detection enabled | | Auth0 Attack Protection → Suspicious IPs |

---

## 2. API Authentication and Authorisation

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-09 | All API endpoints require a valid Bearer token (`get_current_user` or `require_role`) | | Verify no public routes exist unintentionally |
| SEC-10 | Role-based access enforced on all routes | | `require_role("Coordinator")` / `require_role("Admin")` checked |
| SEC-11 | Participant endpoints use `get_current_participant` (Auth0 sub bound to participant record) | | |
| SEC-12 | 401 returned for unauthenticated requests in production (AUTH0_DOMAIN set) | | |
| SEC-13 | 403 returned when role is insufficient | | |
| SEC-14 | UUID path parameters validated (FastAPI raises 422 on malformed UUIDs) | | |

---

## 3. SQL Injection Prevention

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-15 | All database queries use SQLAlchemy ORM or parameterised `select()` statements | | No raw `text()` with string formatting |
| SEC-16 | No f-string interpolation into SQL queries | | Grep codebase: `grep -rn "text(f" backend/` |
| SEC-17 | User-supplied filter values passed as bound parameters | | Verified in `participants.py`, `invoices.py`, `providers.py` |

---

## 4. Secrets Management

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-18 | No secrets committed to the repository | | Run `git log --all -S <secret>` and `truffleHog` scan |
| SEC-19 | All credentials loaded from environment variables | | `AUTH0_DOMAIN`, `AUTH0_AUDIENCE`, `DATABASE_URL`, `GCS_*`, `XERO_*` |
| SEC-20 | `.env` files listed in `.gitignore` | | Verified in `.gitignore` |
| SEC-21 | Production secrets stored in Google Secret Manager (not `.env` files) | | |
| SEC-22 | `backend/.env.example` contains only placeholder values | | No real credentials in example file |

---

## 5. Google Cloud Storage

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-23 | GCS bucket is private (no public access) | | Verify in GCP Console → Storage → Permissions |
| SEC-24 | All file access uses signed URLs with short expiry (≤ 15 minutes) | | |
| SEC-25 | Service account has minimal permissions (Storage Object Creator / Viewer only) | | Principle of least privilege |
| SEC-26 | Uploaded file types validated before storage (PDF only for invoices) | | Check MIME type and file extension |

---

## 6. Xero Integration

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-27 | Xero webhook signature validated via HMAC-SHA256 before processing payload | | `XeroClient.validate_webhook_signature` used in webhook router |
| SEC-28 | Xero OAuth2 tokens stored encrypted or in Secret Manager | | Not stored as plaintext in DB |
| SEC-29 | Xero connection scoped to minimum required permissions | | Accounting.Transactions only |

---

## 7. CORS Configuration

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-30 | CORS `allow_origins` set to production frontend domain only in production | | Must not be `["*"]` in production |
| SEC-31 | CORS `allow_credentials=True` only when required | | |
| SEC-32 | Preflight caching (`max_age`) configured appropriately | | |

---

## 8. Rate Limiting

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-33 | Rate limiting applied to authentication-adjacent endpoints | | Use Cloud Armor or a middleware like `slowapi` |
| SEC-34 | Invoice ingestion trigger endpoint rate-limited (Admin only, low volume expected) | | |
| SEC-35 | Push notification subscription endpoint rate-limited per participant | | |

---

## 9. Transport Security

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-36 | HTTPS enforced in production (HTTP → HTTPS redirect) | | Cloud Run defaults to HTTPS; verify no HTTP ingress |
| SEC-37 | HSTS header configured | | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| SEC-38 | Secure and HttpOnly flags set on session cookies (if any) | | Auth0 SDK handles this |
| SEC-39 | TLS 1.2+ enforced; TLS 1.0/1.1 disabled | | Verify in Cloud Load Balancer SSL policy |

---

## 10. General Hardening

| # | Check | Status | Notes |
|---|-------|--------|-------|
| SEC-40 | Dependency vulnerabilities scanned (`pip-audit` / Dependabot) | | Check GitHub Security tab |
| SEC-41 | Frontend dependencies scanned (`npm audit`) | | |
| SEC-42 | Docker base images use non-root user | | Check `Dockerfile` — `USER` instruction present |
| SEC-43 | Logging does not include PII or sensitive data | | Audit log writes before/after JSON blobs — ensure passwords/tokens excluded |
| SEC-44 | Error responses do not leak internal stack traces in production | | FastAPI exception handlers configured |
| SEC-45 | `X-Content-Type-Options: nosniff` header set | | |
| SEC-46 | `X-Frame-Options: DENY` or `Content-Security-Policy: frame-ancestors 'none'` | | Prevents clickjacking |

---

## Summary

| Category | Total Checks | Pass | Fail | N/A |
|----------|-------------|------|------|-----|
| Auth0 | 8 | | | |
| API Auth/Authz | 6 | | | |
| SQL Injection | 3 | | | |
| Secrets | 5 | | | |
| GCS | 4 | | | |
| Xero | 3 | | | |
| CORS | 3 | | | |
| Rate Limiting | 3 | | | |
| Transport | 4 | | | |
| General Hardening | 7 | | | |
| **Total** | **46** | | | |

**Sign-off:**

| Role | Name | Date |
|------|------|------|
| Security reviewer | | |
| Tech lead | | |
