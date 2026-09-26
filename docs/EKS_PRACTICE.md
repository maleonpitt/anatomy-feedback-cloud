# EKS practice — code setup only (no AWS apply)

This repo models a **cloud-friendly** path for the anatomy-feedback API:

```text
GitHub Actions (later)
  → build image
  → push to ECR
  → (hypothetical) roll Deployment on EKS

Browser
  → CloudFront → private S3 → React
  → ALB Ingress → Service → Pod (Uvicorn/FastAPI) → category S3
```

**Practice AWS account (documented only):** `423687459077`  
**We do not create EKS/ECR resources in AWS from this exercise unless you later authorize apply.**

## What “EKS practice” means here

| Artifact | Location | Purpose |
|----------|----------|---------|
| Dockerfile | `backend/Dockerfile` | Image you would push to ECR |
| K8s manifests | `k8s/` | Namespace, SA/IRSA, Deployment, Service, Ingress sketch |
| Terraform ECR | `infra/ecr.tf` | Registry definition |
| Terraform EKS | `infra/eks.tf`, `infra/eks_iam.tf` | Cluster + node group + IAM |
| GitHub OIDC | `infra/github_oidc.tf` | CD deploy role |
| API IRSA | `infra/irsa_api.tf` + `category_s3.tf` | Pod access to category bucket |
| Frontend CDN | `infra/frontend.tf` | S3 + CloudFront (UI, not in the cluster) |
| CD workflow | `.github/workflows/cd.yml` | Dry-run builds; live ECR/S3/EKS when authorized |
| Legacy EC2/ALB model | `infra/main.tf` | Older learning path; EKS is primary |

## Safe commands

```bash
# Terraform — validate HCL only
cd infra
terraform fmt -recursive
terraform init -backend=false
terraform validate

# Kubernetes — optional local cluster only (kind/minikube)
# kubectl apply -f k8s/...   # only against local practice clusters unless authorized
```

## Forbidden (this practice repo default)

- `terraform apply` / `terraform destroy`
- `aws eks create-cluster` / any live cluster mutation
- Pushing secrets to GitHub
- Setting `SKIP_AUTH=true` on cluster ConfigMaps

## ECR + EKS relationship

1. Build: `docker build -t anatomy-feedback-api ./backend`  
2. Tag/push to **ECR** (when authorized)  
3. EKS nodes pull that image  
4. Deployment runs pods; Ingress exposes HTTPS via ALB controller  

You need **both** ECR (store) and EKS (run). ECS is optional and not required for K8s practice.

CD ship path (dry-run by default): [`CD_PRACTICE.md`](CD_PRACTICE.md).
