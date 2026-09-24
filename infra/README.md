# Infrastructure learning model (Phases 6–7)

**This directory is for design, reading, and local validation only.**  
It does **not** deploy infrastructure and must **not** be applied against the live AWS account without explicit authorization.

## Target architecture

```text
                     Internet
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ↓                           ↓
     CloudFront                      ALB :443
          ↓                           ↓
     Private S3                 Target Group
     (React build)                    ↓
                                   EC2 → Uvicorn → FastAPI
                                        ↓
                              Category S3 (backend)
```

**Nginx is retired** from this model. Legacy config: [`../legacy/`](../legacy/).

## Files

| File | Role |
|------|------|
| `versions.tf` | Provider pin; skip credential checks for local validate |
| `variables.tf` | Placeholder inputs (VPC, subnets, certs, buckets, domains) |
| `main.tf` | Phase 6: ALB, listener, target group, SGs, EC2 |
| `frontend.tf` | Phase 7: private S3, OAC, CloudFront, SPA fallback |
| `outputs.tf` | Key outputs for learning |

## Two S3 buckets

| Variable | Purpose |
|----------|---------|
| `frontend_bucket_name` | React static assets (CloudFront only) |
| `category_data_bucket_name` | Documented placeholder for `CATEGORY_BUCKET_NAME` (backend) |

## Safe local commands

```bash
cd infra
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

## Forbidden

- `terraform apply` / `terraform destroy` / `terraform plan` against a real account
- Any AWS CLI that creates, modifies, or queries production resources

## Documentation

- [`../docs/PHASE_6_ALB.md`](../docs/PHASE_6_ALB.md) — API path
- [`../docs/PHASE_7_CLOUDFRONT.md`](../docs/PHASE_7_CLOUDFRONT.md) — frontend path
- [`../docs/LOCAL_DEVELOPMENT.md`](../docs/LOCAL_DEVELOPMENT.md) — run locally without AWS
