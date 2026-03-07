# DigitalOcean Terraform Module

This directory contains the Terraform configuration for provisioning all DigitalOcean
infrastructure required to run the NDIS CRM application in the **`syd1` (Sydney)** region.

## Resources provisioned

| File | Resources |
|------|-----------|
| `main.tf` | Provider configuration |
| `variables.tf` | Input variables |
| `database.tf` | Managed PostgreSQL 15 cluster, Managed Redis 7 cluster, `ndis_crm` database |
| `registry.tf` | Container Registry (basic tier) |
| `spaces.tf` | Spaces bucket `ndis-crm-files` with CORS for signed-URL access |
| `outputs.tf` | Connection URIs and endpoint values |

## Required variables

| Variable | Description | Default |
|----------|-------------|---------|
| `do_token` | DigitalOcean API token (sensitive) | — |
| `region` | Region slug | `syd1` |
| `app_name` | Base name for resources | `ndis-crm` |
| `db_size` | PostgreSQL node size | `db-s-1vcpu-1gb` |
| `redis_size` | Redis node size | `db-s-1vcpu-1gb` |

## Quick start

```bash
export TF_VAR_do_token="<your-digitalocean-token>"
cd infra/do
terraform init
terraform apply
```

## Full deployment guide

See [docs/DIGITALOCEAN_DEPLOY.md](../../docs/DIGITALOCEAN_DEPLOY.md) for the complete
step-by-step deployment guide including App Platform setup, image builds, database
migrations, and GitHub Actions configuration.
