# anatomy-feedback-cloud

Public DevOps practice repo: take the student feedback app and make it **cloud-friendly**.

**AWS account for practice (when authorized):** `423687459077`  
**Do not commit secrets.** Use `.env.example` placeholders and GitHub Actions / AWS Secrets Manager later.

## Product

Instructors upload exam category mappings and student data, generate feedback, and (in production) email via Microsoft Graph. Local mode can write HTML previews.

Stack today (application):

- **Backend:** FastAPI + Uvicorn  
- **Frontend:** React (CRA)  
- **Tests:** pytest (backend)

## Cloud practice target

```text
GitHub Actions (CI/CD)
        │
        ├─► test / build
        ├─► push API image → Amazon ECR
        └─► (later) React build → S3 + CloudFront

Runtime (practice path — EKS / Kubernetes):
  Browser → CloudFront → private S3 → React
  Browser → ALB Ingress → EKS pods → Uvicorn/FastAPI
                              └─ category S3 + external APIs via secrets
```

| Piece | Practice choice |
|-------|-----------------|
| **Image registry** | **ECR** (build once, pull from EKS) |
| **Run containers** | **EKS** (Kubernetes) — primary DevOps practice track |
| **Optional alternate** | ECS Fargate — lighter path if you want a non-K8s comparison later |
| **Frontend** | S3 + CloudFront |
| **IaC** | Terraform (VPC, EKS, ECR, ALB/Ingress, IAM) |
| **CI/CD** | GitHub Actions → ECR → (later) deploy to EKS |

### ECR vs ECS vs EKS

- **ECR** = where container images live (push/pull). Required for either orchestrator.  
- **EKS** = managed Kubernetes — run the same image as Deployments/Services/Ingress (**this repo’s main practice goal**).  
- **ECS** = AWS-native tasks/services — optional later for comparison; not required to learn K8s.

## Local development

See [`docs/LOCAL_DEVELOPMENT.md`](docs/LOCAL_DEVELOPMENT.md) and [`CONFIG.md`](CONFIG.md).

```bash
# API
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill secrets locally; never commit .env
uvicorn main:app --host 0.0.0.0 --port 5001 --reload

# UI
cd frontend && cp .env.example .env && npm install && npm start
```

Optional local auth bypass (`SKIP_AUTH`) is documented in `docs/LOCAL_DEVELOPMENT.md`. Keep it **off** unless you need it; it must never be enabled in cloud/prod.

## Security

See [`SECURITY.md`](SECURITY.md).

## Related repos

- `anatomy-feedback-v2` — prior modernization / local architecture practice  
- This repo — cloud packaging, ECR/ECS, Terraform, CI/CD practice  

Terraform under `infra/` and manifests under `k8s/` are **apply-ready sketches for practice**.  
Do **not** `terraform apply` or create a real EKS cluster unless you explicitly authorize it.

See [`docs/EKS_PRACTICE.md`](docs/EKS_PRACTICE.md) and [`k8s/README.md`](k8s/README.md).
