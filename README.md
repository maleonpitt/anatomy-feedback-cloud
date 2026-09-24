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

Runtime (practice path — ECS first):
  Browser → CloudFront → private S3 → React
  Browser → ALB → ECS Fargate → Uvicorn/FastAPI
                              └─ category S3 + external APIs via secrets
```

| Piece | Practice choice |
|-------|-----------------|
| **Image registry** | **ECR** (stores images) |
| **Run containers** | **ECS Fargate** first (simpler) |
| **Kubernetes** | **EKS** later (optional) — also pulls from **ECR** |
| **Frontend** | S3 + CloudFront |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |

### ECR vs ECS vs EKS

- **ECR** = where container images live (push/pull).  
- **ECS** = runs those images as tasks/services (start here).  
- **EKS** = runs those same images on Kubernetes (advanced track later).

You need **ECR + (ECS or EKS)**. Not “ECR instead of ECS.”

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

Terraform under `infra/` is a **learning model** until you explicitly authorize `apply` against account `423687459077`.
