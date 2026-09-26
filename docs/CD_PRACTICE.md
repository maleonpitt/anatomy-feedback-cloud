# CD practice — full ship path (code-complete, apply not required to learn)

This repo models a production-shaped CD pipeline. **Default runs are dry-run** (build + artifacts only). Live AWS steps run only when you explicitly set `dry_run=false` **and** have authorized infra + OIDC.

## Pipeline shape

```text
workflow_dispatch
        │
        ├─ build-api          → Docker image (always)
        ├─ build-frontend     → npm run build (always)
        │
        │  if dry_run=true (default):
        │     upload GitHub artifacts / tarball — stop
        │
        └─ if dry_run=false (authorized live):
              ├─ publish-api       → ECR push (OIDC)
              ├─ publish-frontend  → S3 sync + CloudFront invalidation
              └─ deploy-eks        → kubectl set image + rollout status
```

Workflow file: [`.github/workflows/cd.yml`](../.github/workflows/cd.yml)

## Terraform pieces CD depends on

| Resource | File | Used by |
|----------|------|---------|
| ECR repo | `infra/ecr.tf` | publish-api |
| Frontend S3 + CloudFront | `infra/frontend.tf` | publish-frontend |
| EKS cluster | `infra/eks.tf` | deploy-eks |
| GitHub OIDC deploy role | `infra/github_oidc.tf` | all live jobs (`AWS_ROLE_ARN`) |
| Category S3 | `infra/category_s3.tf` | API runtime (not CD) |
| API IRSA role | `infra/irsa_api.tf` | API pods via `k8s/serviceaccount.yaml` |

After an **authorized** `terraform apply`, copy outputs into GitHub:

| Terraform output | GitHub |
|------------------|--------|
| `github_deploy_role_arn` | Secret **`AWS_ROLE_ARN`** |
| `ecr_repository_url` / name | Variable `ECR_REPOSITORY` |
| `frontend_bucket_name` | Variable `FRONTEND_BUCKET` |
| `cloudfront_distribution_id` | Variable `CLOUDFRONT_DISTRIBUTION_ID` |
| `eks_cluster_name` | Variable `EKS_CLUSTER_NAME` |
| (account id) | Variable `AWS_ACCOUNT_ID` |
| `api_irsa_role_arn` | Annotate `k8s/serviceaccount.yaml` |

Also map the deploy role into EKS access (access entry / `aws-auth`) so `kubectl` from Actions works.

## How to practice (no AWS)

1. Actions → **CD** → Run workflow  
2. Leave **dry_run = true**  
3. Confirm API image + frontend build artifacts appear  

Safe local Terraform checks (still no apply):

```bash
cd infra
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

## Live path (only when you authorize)

1. Authorize `terraform apply` for your account  
2. Set `AWS_ROLE_ARN` + variables above  
3. Ensure EKS manifests applied (`k8s/`) and IRSA annotation matches  
4. Re-run CD with **dry_run = false**

## Retired

`cd-artifacts.yml` was replaced by **CD dry_run** (same packaging, plus the real ship jobs behind a flag).
