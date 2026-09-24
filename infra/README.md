# Infrastructure learning model (EKS-first)

**Code-only / apply-ready sketches.**  
Do **not** run `terraform apply` or `destroy` against AWS account `423687459077` (or any account) unless you explicitly authorize it.

## Target architecture

```text
                     Internet
                        │
          ┌─────────────┴─────────────┐
          │                           │
          ↓                           ↓
     CloudFront                   ALB Ingress
          ↓                           ↓
     Private S3                    EKS Service
     (React)                          ↓
                                   Pods (ECR image)
                                      ↓
                                   FastAPI
                                      ↓
                              Category S3
```

## Files

| File | Role |
|------|------|
| `ecr.tf` | ECR repository for API images |
| `eks.tf` / `eks_iam.tf` | EKS cluster, node group, IAM |
| `frontend.tf` | CloudFront + private frontend S3 |
| `main.tf` | Alternate EC2+ALB model (legacy learning) |
| `variables.tf` / `outputs.tf` | Placeholders only |

## Safe local commands

```bash
cd infra
terraform fmt -recursive
terraform init -backend=false
terraform validate
```

## Forbidden

- `terraform apply` / `terraform destroy` / `terraform plan` against a real account  
- Creating real EKS/ECR/CloudFront resources  

See [`../docs/EKS_PRACTICE.md`](../docs/EKS_PRACTICE.md) and [`../k8s/README.md`](../k8s/README.md).
